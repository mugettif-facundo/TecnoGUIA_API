"""Selecciona y adapta propuestas guardadas en SQLite. No utiliza IA."""
import json
import re
import sqlite3
import unicodedata
from pathlib import Path

BASE = Path(__file__).resolve().parent / 'tecnoguia.db'


class PedidoNoDisponible(Exception):
    def __init__(self, detalle):
        self.detalle = detalle
        super().__init__(detalle['mensaje'])


def normalizar(texto):
    texto = ''.join(c for c in unicodedata.normalize('NFKD', texto)
                    if not unicodedata.combining(c)).lower()
    return ' '.join(re.sub(r'[^a-z0-9\s]', ' ', texto).split())


def material_canonico(texto):
    nombre = normalizar(texto)
    aliases = {'hojas de papel': 'papel', 'hojas': 'papel',
               'cinta': 'cinta adhesiva', 'lapices': 'lapiz', 'lapices de escribir': 'lapiz'}
    return aliases.get(nombre, nombre)


def abrir_base(base=None):
    ruta = Path(base or BASE).resolve()
    # Modo lectura: una ruta equivocada no crea una base vacía.
    con = sqlite3.connect(ruta.as_uri() + '?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    return con


def filas_nap(con, grado=None):
    if not con.execute("SELECT 1 FROM sqlite_master WHERE name='guias_nap'").fetchone():
        return []
    filas=[]
    for r in con.execute("SELECT g.*,c.ficha_json FROM guias_nap g JOIN nap_contenidos c ON c.id=g.contenido_id WHERE g.estado IN ('borrador','revisada') AND (? IS NULL OR c.grado=?)",(grado,grado)):
        ficha=json.loads(r['ficha_json'])
        filas.append({**dict(r),'grado':ficha['grado'],'contenido':ficha['titulo'],
            'terminos_json':'[]','pagina_impresa':ficha['pagina_impresa'],
            'pagina_pdf':ficha['pagina_pdf'],'verificado':int(ficha['referencia_cotejada']),
            'documento':'NAP Educación Primaria, Segundo Ciclo','fuente_url':ficha['fuente_url']})
    return filas


def modalidades(actividad_id):
    # Restricciones de las guías actuales: no adaptar automáticamente trabajo cooperativo.
    if actividad_id in {'A01','A02','A03','A04'}:
        return ['grupos']
    if actividad_id == 'A05':
        return ['parejas','grupos']  # La prueba necesita a otra persona sosteniendo la base.
    return ['individual','parejas','grupos'] if actividad_id in {'A06','A07','A08'} else ['grupos']


def ajustar_contexto(guia, datos):
    contexto={'conocimientos_previos':datos.get('conocimientos_previos',''),
              'modalidad':datos.get('modalidad','grupos'),
              'dificultad':datos.get('dificultad','intermedia')}
    if contexto['modalidad'] != 'grupos':
        def lenguaje(valor):
            if isinstance(valor,str):
                for a,b in [('por grupo','por unidad de trabajo'),('cada grupo','cada unidad de trabajo'),('del grupo','de la unidad de trabajo'),('el grupo','la unidad de trabajo'),('los grupos','las unidades de trabajo')]:
                    valor=re.sub(re.escape(a),lambda m: b[0].upper()+b[1:] if m.group(0)[0].isupper() else b,valor,flags=re.IGNORECASE)
                return valor
            if isinstance(valor,list):return [lenguaje(v) for v in valor]
            if isinstance(valor,dict):return {k:lenguaje(v) for k,v in valor.items()}
            return valor
        guia=lenguaje(guia)
    nivel=contexto['dificultad']
    if nivel=='inicial':
        guia['etapas'][0]['acciones'].insert(0,'El docente muestra el primer paso con su modelo y comprueba que los alumnos puedan explicarlo antes de empezar.')
        guia['etapas'][1]['acciones'].insert(0,'Realizar los pasos de a uno; solicitar un control docente de cada unión o montaje antes de pasar a la prueba.')
        orientacion='Mayor acompañamiento: demostración inicial y controles durante el montaje. Se conserva la prueba final de la guía.'
    elif nivel=='avanzada':
        guia['etapas'][1]['acciones'].insert(0,'Antes del montaje, proponer dos soluciones usando los materiales declarados y justificar cuál probar; realizar la comparación dentro del tiempo de trabajo previsto.')
        guia['etapas'][-1]['acciones'].append('Explicar por qué se eligió una solución y cómo las observaciones de la prueba permiten revisar esa decisión.')
        guia['evidencias'].append('Comparación de dos alternativas y argumento de elección con los mismos materiales.')
        guia['criterios_evaluacion'].append('Justifica una decisión de diseño usando restricciones y resultados de la prueba.')
        orientacion='Mayor autonomía: comparar alternativas y justificar decisiones, con los mismos materiales y controles de seguridad.'
    else:
        orientacion='Seguir la secuencia de la guía con apoyo docente puntual y registrar los resultados de la prueba.'
    guia['orientaciones_contexto']=[orientacion]
    if contexto['conocimientos_previos']:
        guia['preparacion_docente'].append('Conocimientos previos informados: '+contexto['conocimientos_previos']+'. Comprobarlos en el inicio; la declaración no constituye una evaluación de los alumnos.')
    else:
        guia['preparacion_docente'].append('No se informaron conocimientos previos: comprobar al inicio si se comprenden la consigna y las operaciones necesarias.')
    guia['contexto_clase']=contexto
    return guia


def catalogo(grado=None, base=None):
    con = abrir_base(base)
    try:
        sql = '''SELECT a.id, a.titulo, a.duracion_minima, a.materiales_json,
                        c.id AS contenido_id, c.grado, c.titulo AS contenido
                 FROM actividades a JOIN contenidos c ON c.id=a.contenido_id
                 WHERE a.estado IN ('borrador', 'revisada')'''
        params = ()
        if grado is not None:
            sql += ' AND c.grado=?'; params = (grado,)
        sql += ' ORDER BY a.id'
        return [{**{k: row[k] for k in ('id','titulo','duracion_minima','contenido_id','grado','contenido')},
                 'materiales': json.loads(row['materiales_json']), 'modalidades':modalidades(row['id'])}
                for row in [*con.execute(sql, params),*filas_nap(con,grado)]]
    finally:
        con.close()


def buscar(datos, base=None):
    """Filtra guías estructuradas; no infiere requisitos de las fichas del PDF."""
    con = abrir_base(base)
    try:
        contenido = con.execute('SELECT grado FROM nap_contenidos WHERE id=?',
                                (datos['contenido_nap_id'],)).fetchone()
        if contenido is None or contenido['grado'] != datos['grado']:
            raise PedidoNoDisponible({'mensaje': 'El contenido no corresponde al grado elegido.'})
        vinculos = {r['recurso_id']: json.loads(r['ficha_json']) for r in con.execute(
            "SELECT recurso_id,ficha_json FROM nap_vinculos WHERE contenido_id=? AND tipo='guia'",
            (datos['contenido_nap_id'],))}
    finally:
        con.close()
    disponibles = {material_canonico(m) for m in datos['materiales']}
    compatibles, descartadas = [], []
    for guia in catalogo(datos['grado'], base):
        if guia['id'] not in vinculos:
            continue
        faltantes = [m['nombre'] for m in guia['materiales']
                     if material_canonico(m['nombre']) not in disponibles]
        motivos = []
        if faltantes:
            motivos.append('Faltan materiales: ' + ', '.join(faltantes))
        if datos['duracion_minutos'] < guia['duracion_minima']:
            motivos.append(f"Necesita al menos {guia['duracion_minima']} minutos.")
        if datos['modalidad'] not in guia['modalidades']:
            motivos.append('Modalidades disponibles: ' + ', '.join(guia['modalidades']))
        ficha = {**vinculos[guia['id']], 'titulo': guia['titulo'],
                 'contenido_generador': guia['id'], 'materiales': guia['materiales'],
                 'duracion_minima': guia['duracion_minima']}
        if motivos:
            descartadas.append({**ficha, 'materiales_faltantes': faltantes, 'motivos': motivos})
        else:
            compatibles.append(ficha)
    return {'compatibles': compatibles, 'no_compatibles': descartadas,
            'mensaje': 'Coincidencia por nombres de materiales; confirmar cantidades y condiciones antes de la clase.',
            'alcance': 'Guías desarrolladas vinculadas al contenido. Las 100 fichas del PDF siguen en el banco para revisión.'}


def generar(datos, base=None):
    con = abrir_base(base)
    try:
        filas = con.execute('''SELECT a.*, c.grado, c.titulo AS contenido,
                c.terminos_json, c.pagina_impresa, c.pagina_pdf, c.verificado,
                d.titulo AS documento FROM actividades a
                JOIN contenidos c ON c.id=a.contenido_id
                JOIN documentos d ON d.id=c.documento_id
                WHERE c.grado=? AND a.estado IN ('borrador', 'revisada') ORDER BY a.id''',
                (datos['grado'],)).fetchall()
        filas = [*filas, *filas_nap(con,datos['grado'])]
        consulta = normalizar(datos['contenido'])
        candidatas = [r for r in filas if consulta in {
            normalizar(r['contenido']), normalizar(r['titulo']), normalizar(r['contenido_id']), normalizar(r['id']),
            *[normalizar(t) for t in json.loads(r['terminos_json'])]}]
        if not candidatas:
            raise PedidoNoDisponible({'mensaje': 'No hay una actividad cargada para ese contenido y grado.',
                'contenidos_disponibles': sorted({r['contenido'] for r in filas})})
        materiales = {material_canonico(m) for m in datos['materiales']}
        problemas = []
        for actividad in candidatas:
            modalidad=datos.get('modalidad','grupos')
            if modalidad not in modalidades(actividad['id']):
                problemas.append({'mensaje':'Esta guía necesita otra modalidad de trabajo.', 'modalidades_disponibles':modalidades(actividad['id'])})
                continue
            requeridos = json.loads(actividad['materiales_json'])
            faltantes = [m['nombre'] for m in requeridos if material_canonico(m['nombre']) not in materiales]
            if faltantes:
                problemas.append({'mensaje': 'Esta actividad requiere materiales adicionales.',
                                  'materiales_faltantes': faltantes})
                continue
            if datos['duracion_minutos'] < actividad['duracion_minima']:
                problemas.append({'mensaje': f"Esta actividad requiere al menos {actividad['duracion_minima']} minutos."})
                continue
            guia = ajustar_contexto(json.loads(actividad['guia_json']),datos)
            tamano = {'individual':1,'parejas':2,'grupos':actividad['alumnos_por_grupo']}[modalidad]
            grupos = (datos['cantidad_alumnos'] + tamano - 1) // tamano
            etiqueta={'individual':'puestos individuales','parejas':'parejas','grupos':'grupos'}[modalidad]
            indicacion=f"Distribuir los alumnos en grupos de hasta {tamano}." if modalidad=='grupos' else ('Trabajo individual: un puesto y un kit por estudiante.' if modalidad=='individual' else 'Trabajar en parejas; si queda un estudiante sin pareja, preparar un puesto asistido por el docente, ya incluido en la cantidad de kits.')
            etapas = guia['etapas']
            total_base = sum(e['minutos'] for e in etapas)
            if total_base > datos['duracion_minutos']:
                raise ValueError('La duración mínima guardada no coincide con las etapas.')
            # El tiempo adicional se asigna al trabajo práctico; el total siempre coincide.
            etapas[1]['minutos'] += datos['duracion_minutos'] - total_base
            materiales_por_grupo = []
            preparacion = list(guia['preparacion_docente'])
            for material in requeridos:
                cantidad = material['cantidad_por_grupo']
                if cantidad is None:
                    materiales_por_grupo.append(f"{material['nombre']}: cantidad a confirmar.")
                else:
                    materiales_por_grupo.append(f"{cantidad} {material['unidad']} de {material['nombre']}.")
                    preparacion.append(f"Preparar {cantidad * grupos} {material['unidad']} de {material['nombre']} para {grupos} {etiqueta}.")
            avisos = list(guia.get('avisos', []))
            if not actividad['verificado']:
                avisos.append('Referencia tomada del inventario del TFG; cotejo con el documento original pendiente.')
            if modalidad!='grupos':
                avisos.append('Un kit por unidad de trabajo. Revisar disponibilidad y turnos docentes al cambiar la modalidad; el tiempo sigue siendo estimado.')
            if datos.get('dificultad')=='avanzada':
                avisos.append('La comparación de alternativas se realiza dentro del tiempo previsto; confirmar que sea viable para este curso.')
            if actividad['estado'] == 'borrador':
                avisos.append('Actividad en borrador: revisar antes de utilizarla con alumnos.')
            return {**guia, 'id': actividad['id'], 'titulo': actividad['titulo'],
                'metodo': 'Plantilla recuperada de la base SQLite',
                'grado': datos['grado'], 'duracion_minutos': datos['duracion_minutos'],
                'organizacion': {'cantidad_grupos': grupos,
                    'cantidad_unidades':grupos,'etiqueta':etiqueta,'alumnos_por_unidad':tamano,'modalidad':modalidad,'indicacion':indicacion},
                'preparacion_docente': preparacion, 'materiales_por_grupo': materiales_por_grupo, 'etiqueta_materiales':{'individual':'Materiales por estudiante','parejas':'Materiales por pareja','grupos':'Materiales por grupo'}[modalidad],
                'etapas': etapas, 'avisos': avisos,
                'fuente': {'contenido_id': actividad['contenido_id'], 'documento': actividad['documento'],
                    'pagina_impresa': actividad['pagina_impresa'], 'pagina_pdf': actividad['pagina_pdf'],
                    'verificada': bool(actividad['verificado'])}}
        raise PedidoNoDisponible(problemas[0])
    finally:
        con.close()
