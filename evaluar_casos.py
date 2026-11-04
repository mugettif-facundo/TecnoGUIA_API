"""Evaluación con el modelo REAL de Ollama sobre casos fijos.

Sirve para comparar versiones del prompt o modelos con los mismos pedidos.
No necesita Uvicorn; usa la base en modo lectura y no guarda propuestas.
No generes desde el formulario mientras corre: ambos usarían Ollama a la vez.

Uso (CMD, en la carpeta del proyecto):
    .venv\\Scripts\\python.exe evaluar_casos.py
    .venv\\Scripts\\python.exe evaluar_casos.py --modelo qwen3:4b
    .venv\\Scripts\\python.exe evaluar_casos.py --casos energia_molinete mecanismos_poleas

Resultado: carpeta evaluaciones\\<fecha>_<modelo>\\ con un JSON por caso
(pedido, salida cruda, salida final, avisos, tiempos) y planilla_docente.csv
para que completes la evaluación pedagógica (abre en Excel).
"""
import argparse, csv, json, re, time
from datetime import datetime
from pathlib import Path

import ia_generadora as g
import ia_local

BASE = dict(duracion_minutos=80, cantidad_alumnos=25, alumnos_por_grupo=4, modalidad='grupos', dificultad='intermedia')


def mats(*nombres):
    return [{'nombre': n, 'cantidad': None, 'unidad': 'unidad'} for n in nombres]


CASOS = {
    'estructuras_sin_pegamento': dict(grado=5, contenido_nap_id='N57', tema='Comparar la resistencia de columnas de cartón con distintos plegados',
        conocimientos_previos='Usan tijeras escolares', materiales=mats('cartón corrugado', 'tijeras de papel')),
    'energia_carton_motores': dict(grado=6, contenido_nap_id='N61', tema='Construcción de energía renovable',
        conocimientos_previos='Identifican partes de un motor', materiales=mats('cartón corrugado', 'motor de corriente continua', 'tijeras de papel')),
    'energia_molinete': dict(grado=6, contenido_nap_id='N61', tema='Cómo se obtiene energía del viento',
        conocimientos_previos='Conocen molinos de viento del campo', materiales=mats('cartón corrugado', 'sorbetes plásticos', 'palitos de madera', 'tijeras de papel', 'cinta de papel')),
    'mecanismos_poleas': dict(grado=5, contenido_nap_id='N52', tema='Transmitir el giro de una manivela a otra rueda',
        conocimientos_previos='Reconocen ruedas y ejes', materiales=mats('tapitas de plástico', 'bandas elásticas', 'varillas de madera', 'cartón corrugado', 'tijeras de papel', 'cinta de papel')),
    'control_barrera': dict(grado=6, contenido_nap_id='N62', tema='Barrera manual y barrera automática',
        conocimientos_previos='Usaron palancas', materiales=mats('cartón corrugado', 'hilo piolín', 'palitos de helado de madera', 'cinta de papel', 'tijeras de papel')),
    'representacion_proceso': dict(grado=6, contenido_nap_id='N65', tema='Diagramar el proceso de reciclado de papel',
        conocimientos_previos='Leyeron recetas', materiales=mats('cartón corrugado', 'marcador permanente', 'tijeras de papel')),
    'estructuras_silicona_sin_pistola': dict(grado=5, contenido_nap_id='N57', tema='Estructuras con cartón y silicona',
        conocimientos_previos='', materiales=mats('cartón corrugado', 'silicona caliente', 'tijeras de papel')),
    'energia_san_luis': dict(grado=6, contenido_nap_id='N61', tema='Cómo se obtiene energía del viento',
        contexto_escuela='Escuela de La Punta; varios alumnos viajaron por la ruta y vieron aerogeneradores.',
        conocimientos_previos='Conocen molinos de viento del campo', materiales=mats('cartón corrugado', 'sorbetes plásticos', 'palitos de madera', 'tijeras de papel', 'cinta de papel')),
    'lista_mal_separada': dict(grado=6, contenido_nap_id='N61', tema='Construcción de energía renovable',
        conocimientos_previos='', materiales=mats('carton motores')),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--modelo', default=ia_local.MODELO)
    ap.add_argument('--casos', nargs='*', default=list(CASOS))
    args = ap.parse_args()
    carpeta = Path('evaluaciones') / (datetime.now().strftime('%Y%m%d_%H%M') + '_' + re.sub(r'[^A-Za-z0-9.]+', '-', args.modelo))
    carpeta.mkdir(parents=True, exist_ok=True)
    filas = []
    for nombre in args.casos:
        pedido = {**BASE, **CASOS[nombre]}
        print(f'\n== {nombre} ({pedido["contenido_nap_id"]}) con {args.modelo} ...', flush=True)
        inicio = time.time(); registro = {'caso': nombre, 'modelo': args.modelo, 'version_prompt': g.VERSION_PROMPT, 'pedido': pedido}
        try:
            r = g.generar(pedido, modelo=args.modelo)
            registro.update(estado='generada', resultado=r)
            cc = r['control_calidad']
            fila = dict(caso=nombre, estado='generada', titulo=r['titulo'], producto=r['plan_ia']['producto_o_proceso'],
                        prueba=r['prueba_final']['procedimiento'], revision_obligatoria=len(cc['revision_obligatoria']),
                        observaciones=len(cc['observaciones']), detalle_avisos=' | '.join(cc['revision_obligatoria'] + cc['observaciones']))
        except ia_local.ErrorIA as exc:
            registro.update(estado='error', codigo=exc.codigo, mensaje=exc.mensaje)
            fila = dict(caso=nombre, estado=f'error {exc.codigo}', titulo='', producto='', prueba='', revision_obligatoria='', observaciones='', detalle_avisos=exc.mensaje)
        segundos = round(time.time() - inicio, 1)
        registro['segundos'] = segundos; fila['segundos'] = segundos
        fila.update(pertinencia_1a3='', realizable_1a3='', cantidades_ok_si_no='', prueba_ok_si_no='', comentario_docente='')
        filas.append(fila)
        (carpeta / f'{nombre}.json').write_text(json.dumps(registro, ensure_ascii=False, indent=1), encoding='utf-8')
        print(f'   {fila["estado"]} en {segundos} s · revisión obligatoria: {fila["revision_obligatoria"]} · {fila["titulo"]}', flush=True)
    with open(carpeta / 'planilla_docente.csv', 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]), delimiter=';'); w.writeheader(); w.writerows(filas)
    print(f'\nListo. Resultados en {carpeta.resolve()}')
    print('Completá las columnas de evaluación docente en planilla_docente.csv.')


if __name__ == '__main__':
    main()
