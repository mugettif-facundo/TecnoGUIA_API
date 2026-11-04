"""Genera 3 actividades de ejemplo con la IA local y las guarda en ejemplos_video.json.
Se usa para filmar el video de demostración. No guarda propuestas en la base."""
import json, time
from pathlib import Path
import ia_generadora, ia_local

def m(*nombres):
    return [{'nombre': n, 'cantidad': None, 'unidad': 'unidad'} for n in nombres]

CASOS = [
    ('Energía del viento (6.º)', dict(grado=6, contenido_nap_id='N61', tema='Cómo se obtiene energía del viento: construir un molinete y relacionarlo con los aerogeneradores', duracion_minutos=80, cantidad_alumnos=25, alumnos_por_grupo=4, conocimientos_previos='Conocen molinos de viento del campo', modalidad='grupos', dificultad='intermedia', materiales=m('cartón corrugado', 'sorbetes plásticos', 'palitos de madera', 'tijeras de papel', 'cinta de papel'))),
    ('Mecanismos con poleas (5.º)', dict(grado=5, contenido_nap_id='N52', tema='Transmitir el giro de una manivela a otra rueda con poleas y elásticos', duracion_minutos=80, cantidad_alumnos=24, alumnos_por_grupo=4, conocimientos_previos='Reconocen ruedas y ejes', modalidad='grupos', dificultad='intermedia', materiales=m('tapitas de plástico', 'bandas elásticas', 'varillas de madera', 'cartón corrugado', 'tijeras de papel', 'cinta de papel'))),
    ('Producción en serie (5.º)', dict(grado=5, contenido_nap_id='N55', tema='Fabricar tarjetas iguales organizando una línea de producción con plantilla', duracion_minutos=80, cantidad_alumnos=24, alumnos_por_grupo=4, conocimientos_previos='Recortaron y plegaron papel', modalidad='grupos', dificultad='inicial', materiales=m('cartulina', 'tijeras de papel', 'lápices', 'regla'))),
]

salida = Path(__file__).resolve().parent / 'ejemplos_video.json'
resultados = []
for nombre, pedido in CASOS:
    print(f'Generando: {nombre} ... (puede tardar varios minutos)', flush=True)
    inicio = time.time()
    fila = {'nombre': nombre, 'pedido': pedido}
    try:
        fila['datos'] = ia_generadora.generar(pedido)
        fila['estado'] = 'ok'
    except ia_local.ErrorIA as exc:
        fila['estado'] = f'error {exc.codigo}'; fila['mensaje'] = exc.mensaje
    fila['segundos'] = round(time.time() - inicio)
    resultados.append(fila)
    salida.write_text(json.dumps(resultados, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'  -> {fila["estado"]} en {fila["segundos"]} s', flush=True)
print('Listo. Resultados en', salida)
