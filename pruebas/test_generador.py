"""Pruebas del generador con Ollama SIMULADO (no evalúan la calidad real del modelo).

Uso, desde la carpeta del proyecto y con la base creada:
    .venv\\Scripts\\python.exe -m unittest pruebas.test_generador -v
La base se abre solo en modo lectura; no se modifica.
"""
import copy, json, sys, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import ia_generadora as g, ia_local, motor

REAL_CONTEXTO = g.cargar_contexto_local()
MATS = ['cartón corrugado', 'sorbetes plásticos', 'palitos de madera', 'tijeras escolares', 'cinta de papel']


def pedido(**cambios):
    base = dict(grado=6, contenido_nap_id='N61', tema='Molinete para explicar cómo se obtiene energía del viento',
                duracion_minutos=80, cantidad_alumnos=25, alumnos_por_grupo=4, conocimientos_previos='Usan tijeras',
                modalidad='grupos', dificultad='intermedia',
                materiales=[{'nombre': m, 'cantidad': None, 'unidad': 'unidad'} for m in MATS])
    base.update(cambios)
    return base


def actividad(**cambios):
    a = {
        'titulo': 'Molinete de viento',
        'plan': {'producto_o_proceso': 'Cada grupo arma un molinete de cartón con eje de sorbete.',
                 'relacion_con_contenido': 'Modela cómo se capta el viento para obtener energía.',
                 'que_se_observa': 'El molinete gira al soplar; los alumnos nombran recurso, captación y transformación.',
                 'alcance': 'No se genera ni mide electricidad.'},
        'prueba_final': {'procedimiento': 'Soplar a un palmo de distancia y contar vueltas en 10 segundos con 4 y con 6 aspas.',
                         'criterio_exito': 'El molinete gira y el grupo explica la transformación de la energía del viento.',
                         'recursos': ['L001', 'L002']},
        'objetivos': ['Identificar el recurso y la transformación de energía en el molinete.',
                      'Comparar el giro con distinta cantidad de aspas.'],
        'justificacion_curricular': 'Generación de energía a partir del viento.',
        'materiales': [{'id': 'L001', 'cantidad': 1, 'distribucion': 'por_unidad_trabajo', 'detalle': 'Un cuadrado de cartón del ancho de una mano.'},
                       {'id': 'L002', 'cantidad': 1, 'distribucion': 'por_unidad_trabajo', 'detalle': 'Un sorbete como eje.'},
                       {'id': 'L004', 'cantidad': 3, 'distribucion': 'compartido', 'detalle': 'Tijeras compartidas.'}],
        'preparacion_docente': ['Recortar 7 cuadrados de cartón.', 'Separar 7 sorbetes.'],
        'consigna': 'Construyan un molinete que gire con el soplido.',
        'etapas': [{'nombre': 'Inicio', 'minutos': 15, 'acciones': [{'descripcion': 'Conversar sobre molinos.', 'recursos': []}]},
                   {'nombre': 'Construcción', 'minutos': 40, 'acciones': [{'descripcion': 'Cortar desde las esquinas hacia el centro.', 'recursos': ['L001', 'L004']}]},
                   {'nombre': 'Prueba', 'minutos': 25, 'acciones': [{'descripcion': 'Soplar y contar vueltas.', 'recursos': ['L001', 'L002']}]}],
        'explicacion': 'El viento empuja las aspas; la energía del movimiento del aire se transforma en giro.',
        'seguridad': ['Tijeras con supervisión.', 'No soplar cerca de la cara de un compañero.'],
        'evidencias': ['Molinete que gira.', 'Explicación oral de la transformación de energía.'],
        'criterios_evaluacion': ['Nombra recurso y transformación de energía.', 'Compara resultados.'],
        'preguntas_docentes': ['¿De dónde viene la energía?', '¿Qué cambia con más aspas?'],
        'orientaciones': ['Mostrar un molinete terminado.'],
        'problemas_frecuentes': [{'problema': 'No gira.', 'revision': 'Roce en el eje.', 'correccion': 'Agrandar el orificio.'},
                                 {'problema': 'Aspas aplastadas.', 'revision': 'Doblez.', 'correccion': 'Doblar sin aplastar.'}]}
    a.update(cambios)
    return a


class OllamaFalso:
    def __init__(self, a):
        self.a = a; self.llamadas = []
    def __call__(self, ruta, cuerpo=None, timeout=5):
        self.llamadas.append(cuerpo)
        return {'done': True, 'done_reason': 'stop', 'model': 'falso', 'message': {'content': json.dumps(self.a, ensure_ascii=False)}}


def correr(a, p=None):
    falso = OllamaFalso(a)
    with mock.patch.object(ia_local, 'consultar', falso):
        r = g.generar(p or pedido())
    return r, falso


@unittest.skipUnless(motor.BASE.is_file(), 'Falta tecnoguia.db')
class PruebasGenerador(unittest.TestCase):
    # Por defecto, sin lugar de escuela: las pruebas no dependen de lo que el docente configure.
    def setUp(self):
        sin_escuela = {**REAL_CONTEXTO, 'localidad_escuela': ''}
        p = mock.patch.object(g, 'cargar_contexto_local', return_value=sin_escuela)
        p.start(); self.addCleanup(p.stop)

    def usar_contexto_real(self):
        mock.patch.stopall()
        p = mock.patch.object(g, 'cargar_contexto_local', return_value=copy.deepcopy(REAL_CONTEXTO))
        p.start(); self.addCleanup(p.stop)

    def test_caso_correcto_sin_revision_obligatoria(self):
        r, falso = correr(actividad())
        self.assertEqual(r['control_calidad']['revision_obligatoria'], [])
        self.assertEqual(r['organizacion']['cantidad_unidades'], 7)
        self.assertIn('plan_ia', r)
        contexto = json.loads(falso.llamadas[0]['messages'][1]['content'])
        self.assertIn('orientacion_del_contenido', contexto)
        self.assertEqual(list(contexto)[-1], 'orientacion_del_contenido')
        self.assertEqual(list(falso.llamadas[0]['format']['properties'])[:3], ['titulo', 'plan', 'prueba_final'])

    def test_desvio_a_estructuras_en_energia(self):
        a = actividad(plan={'producto_o_proceso': 'Torre de cartón.', 'relacion_con_contenido': 'Estructuras.',
                            'que_se_observa': 'La torre se mantiene en pie.', 'alcance': 'Ninguno.'},
                      prueba_final={'procedimiento': 'Empujar la torre suavemente.', 'criterio_exito': 'La torre resiste y es estable.', 'recursos': ['L001']},
                      objetivos=['Construir una torre estable.', 'Trabajar en equipo.'])
        r, _ = correr(a)
        textos = ' '.join(r['control_calidad']['revision_obligatoria'])
        self.assertIn('desvío', textos)
        self.assertTrue(r['avisos'][0].startswith('ATENCIÓN'))

    def test_recursos_reparados_en_vez_de_error(self):
        a = actividad()
        a['etapas'][1]['acciones'][0]['recursos'] = ['L001', 'L004', 'L005', 'X99']  # L005 declarada pero no en materiales; X99 inventada
        r, _ = correr(a)
        obl = ' '.join(r['control_calidad']['revision_obligatoria'])
        self.assertIn('X99', obl); self.assertIn('cinta de papel', obl)
        self.assertIn('L005', [m['id'] for m in r['recursos_utilizados']])
        self.assertNotIn('X99', json.dumps(r['etapas']))
        self.assertIn('X99', json.dumps(r['ia']['salida_cruda']))  # la salida original se conserva

    def test_material_no_declarado_en_texto_es_aviso(self):
        a = actividad()
        a['etapas'][1]['acciones'][0]['descripcion'] = 'Unir las aspas con pegamento.'
        p = pedido(); p['materiales'] = p['materiales'][:4]  # sin cinta: ningún adhesivo declarado
        r, _ = correr(a, p)
        self.assertTrue(any('pegamento' in t for t in r['control_calidad']['revision_obligatoria']))

    def test_cantidad_superior_a_disponible_es_aviso(self):
        p = pedido(); p['materiales'][0]['cantidad'] = 3
        r, _ = correr(actividad(), p)
        self.assertTrue(any('informaste 3' in t for t in r['control_calidad']['revision_obligatoria']))

    def test_tiempos_ajustados(self):
        a = actividad(); a['etapas'][2]['minutos'] = 5  # suma 60
        r, _ = correr(a)
        self.assertEqual(sum(e['minutos'] for e in r['etapas']), 80)
        self.assertIsNotNone(r['ajuste_tiempos'])

    def test_lista_sin_separar_no_llama_al_modelo(self):
        for nombre in ['carton motores', 'tijeras y silicona', 'sorbetes palitos']:
            p = pedido(materiales=[{'nombre': nombre, 'cantidad': None, 'unidad': 'unidad'}])
            falso = OllamaFalso(actividad())
            with mock.patch.object(ia_local, 'consultar', falso), self.assertRaises(ia_local.ErrorIA) as ctx:
                g.generar(p)
            self.assertEqual(ctx.exception.codigo, 422); self.assertEqual(falso.llamadas, [])

    def test_nombres_compuestos_legitimos(self):
        cat = frozenset(motor.normalizar(m['nombre']) for m in g.catalogo_materiales()['materiales'])
        for nombre in ['silicona caliente', 'motor de corriente continua', 'cinta de papel', 'pistola de silicona',
                       'goma eva', 'papel aluminio', 'motores', 'bandas elásticas'] + [m['nombre'] for m in g.catalogo_materiales()['materiales']]:
            g.revisar_nombre_material(nombre, cat)

    def test_silicona_caliente_sin_pistola_queda_fuera(self):
        p = pedido(); p['materiales'].append({'nombre': 'silicona caliente', 'cantidad': None, 'unidad': 'unidad'})
        r, falso = correr(actividad(), p)
        contexto = json.loads(falso.llamadas[0]['messages'][1]['content'])
        self.assertNotIn('silicona caliente', json.dumps(contexto, ensure_ascii=False))
        self.assertTrue(any('adhesivos calientes' in t for t in r['avisos']))

    def test_orientaciones_completas(self):
        datos = g.cargar_orientaciones()
        claves = {'foco', 'requiere_construccion', 'la_prueba_debe_mostrar', 'ideas_de_producto', 'objetivos_ejemplo', 'evitar', 'palabras_clave'}
        ids = {'N51', 'N52', 'N53', 'N54', 'N55', 'N56', 'N57', 'N61', 'N62', 'N63', 'N64', 'N65'}
        self.assertEqual(set(datos['contenidos']), ids)
        for i, o in datos['contenidos'].items():
            self.assertEqual(set(o), claves, i)

    def test_resultado_se_puede_guardar(self):
        # Mismo contrato que valida POST /propuestas (sin necesitar FastAPI).
        r, _ = correr(actividad())
        self.assertEqual(sum(e['minutos'] for e in r['etapas']), r['duracion_minutos'])
        for k in ['objetivos', 'preparacion_docente', 'materiales_por_grupo', 'seguridad', 'evidencias', 'criterios_evaluacion', 'avisos']:
            self.assertTrue(r[k], k)
        g.PedidoGeneracion.model_validate(r['solicitud_generacion'])
        json.dumps(r, ensure_ascii=False)

    # --- Contexto local (automático: el lugar de la escuela se configura en contexto_local.json) ---
    def con_conexion(self, texto, **cambios):
        a = actividad(**cambios)
        a['plan'] = {'producto_o_proceso': a['plan']['producto_o_proceso'], 'conexion_local': texto,
                     **{k: v for k, v in a['plan'].items() if k != 'producto_o_proceso'}}
        return a

    def test_contexto_local_completo(self):
        datos = REAL_CONTEXTO
        ids = set(g.cargar_orientaciones()['contenidos'])
        self.assertIn(datos['localidad_escuela'], datos['localidades'])
        for localidad, refs in datos['localidades'].items():
            for r in refs:
                self.assertEqual({'id', 'referencia', 'contenidos', 'palabras_clave', 'fuente', 'verificada'}, set(r), r.get('id'))
                self.assertTrue(r['fuente'].startswith('https://'), r['id'])
                self.assertTrue(set(r['contenidos']) <= ids, r['id'])

    def test_sin_localidad_configurada_no_envia_contexto_local(self):
        r, falso = correr(actividad())
        self.assertNotIn('contexto_local', json.loads(falso.llamadas[0]['messages'][1]['content']))
        self.assertIsNone(r['contexto_local'])

    def test_localidad_de_la_escuela_se_aplica_sola(self):
        self.usar_contexto_real()
        a = self.con_conexion('¿Por qué hay aerogeneradores en Toro Negro? Nuestro molinete funciona igual a escala.')
        r, falso = correr(a)  # el pedido no trae localidad, como el formulario
        enviado = json.loads(falso.llamadas[0]['messages'][1]['content'])
        self.assertIn('Toro Negro', enviado['contexto_local']['referencias'][0])
        self.assertEqual(list(enviado)[-1], 'orientacion_del_contenido')  # la orientación sigue al final
        self.assertIn('conexion_local', falso.llamadas[0]['format']['$defs']['PlanLocal']['properties'])
        self.assertEqual(r['contexto_local']['localidad'], 'San Luis')
        self.assertEqual([x['id'] for x in r['contexto_local']['referencias']], ['SL-01'])
        self.assertFalse(any('no usó la referencia local' in o for o in r['control_calidad']['observaciones']))
        g.PedidoGeneracion.model_validate(r['solicitud_generacion'])

    def test_contenido_sin_referencia_no_agrega_nada(self):
        self.usar_contexto_real()
        a = actividad(titulo='Torre de cartón', plan={**actividad()['plan'], 'producto_o_proceso': 'Columnas de cartón plegado.'})
        r, falso = correr(a, pedido(grado=5, contenido_nap_id='N57'))
        self.assertNotIn('contexto_local', json.loads(falso.llamadas[0]['messages'][1]['content']))
        self.assertIsNone(r['contexto_local'])
        self.assertFalse(any('San Luis' in x for x in r['avisos']))

    def test_referencia_local_no_usada_es_observacion(self):
        self.usar_contexto_real()
        r, _ = correr(self.con_conexion('En nuestra provincia hay mucho viento.'))
        self.assertTrue(any('no usó la referencia local' in o for o in r['control_calidad']['observaciones']))

    def test_referencia_no_verificada_no_se_envia(self):
        # SL-02 (N62) está marcada como no verificada: no debe llegar a la IA.
        self.usar_contexto_real()
        refs, _, localidad = g.referencias_locales('', 'N62')
        self.assertEqual((refs, localidad), ([], 'San Luis'))

    def test_localidad_desconocida_no_llama_al_modelo(self):
        falso = OllamaFalso(actividad())
        with mock.patch.object(ia_local, 'consultar', falso):
            with self.assertRaises(ia_local.ErrorIA) as e:
                g.generar(pedido(localidad='Atlantis'))
        self.assertEqual(e.exception.codigo, 422)
        self.assertEqual(falso.llamadas, [])

if __name__ == '__main__':
    unittest.main()
