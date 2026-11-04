"""Pruebas de perfiles y seguridad. Trabajan sobre una COPIA temporal de tecnoguia.db;
la base real no se modifica.

Uso, desde la carpeta del proyecto:
    .venv\\Scripts\\python.exe -m unittest pruebas.test_seguridad -v
Las pruebas de la API necesitan httpx (lo usa el cliente de pruebas de FastAPI):
    .venv\\Scripts\\python.exe -m pip install httpx
"""
import shutil, sqlite3, sys, tempfile, unittest
from datetime import timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
import motor, seguridad

BASE_REAL = motor.BASE
seguridad.ITERACIONES = 1_000  # solo para que las pruebas sean rápidas; el programa usa 600.000

try:
    from fastapi.testclient import TestClient
    import main, crear_admin
    HAY_CLIENTE = True
except Exception as exc:  # falta httpx o FastAPI
    HAY_CLIENTE = False; MOTIVO = str(exc)

ORIGEN = {'X-TecnoGUIA': '1'}


def copia_base():
    carpeta = Path(tempfile.mkdtemp())
    destino = carpeta / 'tecnoguia.db'
    shutil.copy(BASE_REAL, destino)
    return carpeta, destino


@unittest.skipUnless(BASE_REAL.is_file(), 'Falta tecnoguia.db')
class PruebasModulo(unittest.TestCase):
    def setUp(self):
        self.carpeta, ruta = copia_base()
        self.con = seguridad.conectar(ruta)
        seguridad.preparar(self.con)
        self.admin = seguridad.crear_usuario(self.con, 'admin', 'Admin Prueba', 'administrador', 'Sol-Punta-2026', False)

    def tearDown(self):
        self.con.close(); shutil.rmtree(self.carpeta, ignore_errors=True)

    def test_clave_no_se_guarda_en_texto_plano(self):
        guardado = self.con.execute("SELECT clave_hash FROM usuarios WHERE usuario='admin'").fetchone()[0]
        self.assertNotIn('Sol-Punta-2026', guardado)
        self.assertTrue(guardado.startswith('pbkdf2_sha256$'))
        self.assertTrue(seguridad.verificar_clave('Sol-Punta-2026', guardado))
        self.assertFalse(seguridad.verificar_clave('otra-clave-1', guardado))

    def test_politica_de_claves(self):
        for mala in ['corta1', '12345678901', 'solamenteletras', 'docente123x']:
            with self.assertRaises(seguridad.ErrorSeguridad):
                seguridad.validar_clave_nueva(mala, 'docente')

    def test_bloqueo_tras_intentos_fallidos(self):
        for _ in range(seguridad.MAX_INTENTOS):
            with self.assertRaises(seguridad.ErrorSeguridad) as ctx:
                seguridad.ingresar(self.con, 'admin', 'incorrecta-1')
            self.assertEqual(ctx.exception.codigo, 401)
        with self.assertRaises(seguridad.ErrorSeguridad) as ctx:
            seguridad.ingresar(self.con, 'admin', 'Sol-Punta-2026')  # aun con la clave correcta
        self.assertEqual(ctx.exception.codigo, 429)

    def test_mensaje_generico_para_usuario_inexistente(self):
        with self.assertRaises(seguridad.ErrorSeguridad) as ctx:
            seguridad.ingresar(self.con, 'nadie', 'algo-1234')
        self.assertEqual(ctx.exception.mensaje, 'Usuario o contraseña incorrectos.')

    def test_sesion_vence_y_se_guarda_solo_la_huella(self):
        token, _ = seguridad.ingresar(self.con, 'admin', 'Sol-Punta-2026')
        self.assertIsNotNone(seguridad.usuario_de_sesion(self.con, token))
        self.assertEqual(self.con.execute('SELECT COUNT(*) FROM sesiones WHERE token_hash=?', (token,)).fetchone()[0], 0)
        vencida = seguridad._iso(seguridad.ahora() - timedelta(seconds=1))
        self.con.execute('UPDATE sesiones SET expira_en=?', (vencida,)); self.con.commit()
        self.assertIsNone(seguridad.usuario_de_sesion(self.con, token))

    def test_usuario_desactivado_no_ingresa(self):
        doc = seguridad.crear_usuario(self.con, 'doc', 'Docente', 'docente', 'Rio-Quinto-77', False)
        token, _ = seguridad.ingresar(self.con, 'doc', 'Rio-Quinto-77')
        seguridad.modificar_usuario(self.con, doc['id'], 'admin', activo=False)
        self.assertIsNone(seguridad.usuario_de_sesion(self.con, token))
        with self.assertRaises(seguridad.ErrorSeguridad):
            seguridad.ingresar(self.con, 'doc', 'Rio-Quinto-77')

    def test_queda_al_menos_un_administrador(self):
        with self.assertRaises(seguridad.ErrorSeguridad):
            seguridad.modificar_usuario(self.con, self.admin['id'], 'otro', perfil='docente')

    def test_preparar_es_idempotente(self):
        seguridad.preparar(self.con); seguridad.preparar(self.con)
        self.assertTrue(seguridad.esta_preparada(self.con))


@unittest.skipUnless(BASE_REAL.is_file(), 'Falta tecnoguia.db')
@unittest.skipUnless(HAY_CLIENTE, 'Instalá httpx para probar la API: python -m pip install httpx')
class PruebasAPI(unittest.TestCase):
    def setUp(self):
        self.carpeta, self.ruta = copia_base()
        with sqlite3.connect(self.ruta) as con:
            self.previas = con.execute('SELECT COUNT(*) FROM propuestas_guardadas').fetchone()[0]
        self.admin, self.asignadas = crear_admin.configurar(self.ruta, 'admin', 'Admin Prueba', 'Sol-Punta-2026')
        motor.BASE = self.ruta

    def tearDown(self):
        motor.BASE = BASE_REAL; shutil.rmtree(self.carpeta, ignore_errors=True)

    def cliente(self, usuario=None, clave=None):
        c = TestClient(main.app, follow_redirects=False)
        if usuario:
            r = c.post('/sesion', json={'usuario': usuario, 'clave': clave}, headers=ORIGEN)
            self.assertEqual(r.status_code, 200, r.text)
        return c

    def crear_docente(self, admin, usuario, nombre):
        r = admin.post('/usuarios', json={'usuario': usuario, 'nombre': nombre, 'perfil': 'docente', 'clave_temporal': 'temporal-123'}, headers=ORIGEN)
        self.assertEqual(r.status_code, 201, r.text)
        c = self.cliente(usuario, 'temporal-123')
        r = c.post('/sesion/clave', json={'actual': 'temporal-123', 'nueva': 'nueva-clave-2026'}, headers=ORIGEN)
        self.assertEqual(r.status_code, 200, r.text)
        return c

    def guia_catalogo(self, c):
        g = motor.catalogo(5)[0]
        r = c.post('/actividades/generar', headers=ORIGEN, json={'grado': 5, 'contenido': g['contenido'], 'duracion_minutos': 60, 'cantidad_alumnos': 25,
                   'materiales': [m['nombre'] for m in g['materiales']]})
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def test_sin_sesion_todo_esta_cerrado(self):
        c = self.cliente()
        self.assertEqual(c.get('/formulario').status_code, 303)
        self.assertEqual(c.get('/ingresar').status_code, 200)
        for ruta in ['/curriculo', '/catalogo', '/propuestas', '/materiales', '/ia/estado', '/usuarios', '/registro']:
            self.assertEqual(c.get(ruta).status_code, 401, ruta)
        pedido = {'grado': 6, 'contenido_nap_id': 'N61', 'tema': 'Energía del viento', 'duracion_minutos': 80, 'cantidad_alumnos': 25,
                  'materiales': [{'nombre': 'cartón', 'cantidad': None, 'unidad': 'unidad'}]}
        self.assertEqual(c.post('/actividades/crear-ia', json=pedido, headers=ORIGEN).status_code, 401)

    def test_propuestas_anteriores_quedan_del_administrador(self):
        self.assertEqual(self.asignadas, self.previas)
        admin = self.cliente('admin', 'Sol-Punta-2026')
        self.assertEqual(len(admin.get('/propuestas').json()), self.previas)

    def test_clave_temporal_obliga_a_cambiarla(self):
        admin = self.cliente('admin', 'Sol-Punta-2026')
        admin.post('/usuarios', json={'usuario': 'nuevo', 'nombre': 'Nuevo Docente', 'perfil': 'docente', 'clave_temporal': 'temporal-123'}, headers=ORIGEN)
        c = self.cliente('nuevo', 'temporal-123')
        r = c.get('/curriculo')
        self.assertEqual(r.status_code, 403); self.assertTrue(r.json()['detail']['cambiar_clave'])
        self.assertEqual(c.get('/formulario').status_code, 303)
        c.post('/sesion/clave', json={'actual': 'temporal-123', 'nueva': 'mi-clave-2026'}, headers=ORIGEN)
        self.assertEqual(c.get('/curriculo').status_code, 200)
        self.assertEqual(c.get('/formulario').status_code, 200)

    def test_docente_no_accede_a_administracion(self):
        doc = self.crear_docente(self.cliente('admin', 'Sol-Punta-2026'), 'ana', 'Ana Docente')
        self.assertEqual(doc.get('/usuarios').status_code, 403)
        self.assertEqual(doc.get('/registro').status_code, 403)
        self.assertEqual(doc.post('/usuarios', json={'usuario': 'x1x', 'nombre': 'X', 'perfil': 'administrador', 'clave_temporal': 'temporal-123'}, headers=ORIGEN).status_code, 403)
        r = doc.get('/administracion')
        self.assertEqual((r.status_code, r.headers['location']), (303, '/formulario'))

    def test_cada_docente_ve_solo_sus_propuestas(self):
        admin = self.cliente('admin', 'Sol-Punta-2026')
        ana = self.crear_docente(admin, 'ana', 'Ana Docente')
        beto = self.crear_docente(admin, 'beto', 'Beto Docente')
        r = ana.post('/propuestas', json=self.guia_catalogo(ana), headers=ORIGEN)
        self.assertEqual(r.status_code, 201, r.text)
        id_ana = r.json()['id']
        self.assertEqual([p['id'] for p in ana.get('/propuestas').json()], [id_ana])
        self.assertEqual(beto.get('/propuestas').json(), [])
        self.assertEqual(beto.get('/propuestas/' + id_ana).status_code, 404)
        self.assertEqual(ana.get('/propuestas/' + id_ana).status_code, 200)
        todas = admin.get('/propuestas').json()
        self.assertEqual(len(todas), self.previas + 1)
        self.assertEqual(next(p for p in todas if p['id'] == id_ana)['autor'], 'Ana Docente')
        self.assertEqual(admin.get('/propuestas/' + id_ana).status_code, 200)

    def test_pedidos_sin_encabezado_propio_se_rechazan(self):
        admin = self.cliente('admin', 'Sol-Punta-2026')
        r = admin.post('/usuarios', json={'usuario': 'x1x', 'nombre': 'X', 'perfil': 'docente', 'clave_temporal': 'temporal-123'})
        self.assertEqual(r.status_code, 403)

    def test_cerrar_sesion_y_desactivar(self):
        admin = self.cliente('admin', 'Sol-Punta-2026')
        ana = self.crear_docente(admin, 'ana', 'Ana Docente')
        usuarios = {u['usuario']: u for u in admin.get('/usuarios').json()}
        admin.patch('/usuarios/%d' % usuarios['ana']['id'], json={'activo': False}, headers=ORIGEN)
        self.assertEqual(ana.get('/curriculo').status_code, 401)
        self.assertEqual(admin.patch('/usuarios/%d' % usuarios['admin']['id'], json={'activo': False}, headers=ORIGEN).status_code, 409)
        admin.delete('/sesion', headers=ORIGEN)
        self.assertEqual(admin.get('/usuarios').status_code, 401)

    def test_cookie_protegida_y_registro(self):
        c = TestClient(main.app, follow_redirects=False)
        r = c.post('/sesion', json={'usuario': 'admin', 'clave': 'Sol-Punta-2026'}, headers=ORIGEN)
        cookie = r.headers['set-cookie'].lower()
        self.assertIn('httponly', cookie); self.assertIn('samesite=strict', cookie)
        c.post('/sesion', json={'usuario': 'admin', 'clave': 'mal-123456'}, headers=ORIGEN)
        eventos = [e['evento'] for e in c.get('/registro').json()]
        self.assertIn('ingreso', eventos); self.assertIn('ingreso_fallido', eventos)


if __name__ == '__main__':
    unittest.main()
