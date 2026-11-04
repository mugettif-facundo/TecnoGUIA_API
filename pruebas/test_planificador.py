"""Pruebas de la integración del planificador (0.10.0). Usan una copia temporal de la base: la real no se toca.
   .venv\\Scripts\\python.exe -m unittest pruebas.test_planificador -v
"""
import json, os, sqlite3, sys, tempfile, threading, unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fastapi.testclient import TestClient
import motor, seguridad

H = {'X-TecnoGUIA': '1'}


class FalsoOllama(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _r(self, d):
        b = json.dumps(d).encode(); self.send_response(200); self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self): self._r({'models': [{'name': 'qwen3:1.7b'}]} if self.path == '/api/tags' else {'version': '0.40.3'})
    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0)); c = json.loads(self.rfile.read(n)); self._r({'message': {'content': json.dumps({'eco': c.get('model')})}, 'done': True})


class PruebasPlanificador(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.carpeta = tempfile.mkdtemp()
        motor.BASE = Path(cls.carpeta) / 'prueba.db'
        con = sqlite3.connect(motor.BASE)
        con.execute('CREATE TABLE propuestas_guardadas(id TEXT PRIMARY KEY)')
        con.row_factory = sqlite3.Row
        seguridad.preparar(con)
        seguridad.crear_usuario(con, 'admin1', 'Admin Uno', 'administrador', 'Zeta-Sol-2026', debe_cambiar_clave=False)
        seguridad.crear_usuario(con, 'ana', 'Ana Pérez', 'docente', 'Mate-Luna-2026', debe_cambiar_clave=False)
        seguridad.crear_usuario(con, 'luis', 'Luis Gómez', 'docente', 'Rio-Monte-2026', debe_cambiar_clave=False)
        seguridad.crear_usuario(con, 'nuevo', 'Nuevo Docente', 'docente', 'Temporal2026', debe_cambiar_clave=True)
        con.close()
        cls.srv = HTTPServer(('127.0.0.1', 0), FalsoOllama); threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        import planificador; planificador.OLLAMA_URL = 'http://127.0.0.1:%d' % cls.srv.server_port
        import main
        cls.app = main.app

    @classmethod
    def tearDownClass(cls):
        try: cls.srv.shutdown()
        except Exception: pass

    def cliente(self, usuario=None, clave=None):
        c = TestClient(self.app)
        if usuario:
            r = c.post('/sesion', json={'usuario': usuario, 'clave': clave}, headers=H); self.assertEqual(r.status_code, 200, r.text)
        return c

    def test_01_pagina_exige_sesion(self):
        c = TestClient(self.app)
        self.assertIn(c.get('/planificador/', follow_redirects=False).status_code, (302, 303, 307))
        self.assertEqual(c.get('/planificador/api/almacen/actividades').status_code, 401)
        self.assertEqual(c.get('/planificador/api/compartidas').status_code, 401)
        self.assertEqual(c.get('/planificador/api/ollama/api/tags').status_code, 401)

    def test_02_con_sesion_carga_la_pantalla(self):
        c = self.cliente('ana', 'Mate-Luna-2026')
        r = c.get('/planificador/'); self.assertEqual(r.status_code, 200); self.assertIn('sesion.js', r.text)
        self.assertEqual(c.get('/planificador/js/motor.js').status_code, 200)
        self.assertEqual(c.get('/planificador/datos/corpus.js').status_code, 200)
        self.assertEqual(c.get('/planificador', follow_redirects=False).status_code, 307)

    def test_03_clave_temporal_bloquea(self):
        c = self.cliente('nuevo', 'Temporal2026')
        self.assertEqual(c.get('/planificador/api/almacen/actividades').status_code, 403)
        self.assertIn(c.get('/planificador/', follow_redirects=False).status_code, (302, 303, 307))

    def test_04_datos_separados_por_usuario(self):
        a, l = self.cliente('ana', 'Mate-Luna-2026'), self.cliente('luis', 'Rio-Monte-2026')
        act = {'id': 'A-N01', 'titulo': 'Torre de papel', 'grados': [5], 'registros': ['C01'], 'autoria': 'Ana'}
        self.assertEqual(a.put('/planificador/api/almacen/actividades', json=act, headers=H).status_code, 200)
        self.assertEqual(l.put('/planificador/api/almacen/actividades', json=dict(act, titulo='Puente'), headers=H).status_code, 200)
        self.assertEqual([x['titulo'] for x in a.get('/planificador/api/almacen/actividades').json()], ['Torre de papel'])
        self.assertEqual([x['titulo'] for x in l.get('/planificador/api/almacen/actividades').json()], ['Puente'])
        self.assertEqual(a.delete('/planificador/api/almacen/actividades/A-N01').status_code, 403)  # sin encabezado de seguridad
        self.assertEqual(l.delete('/planificador/api/almacen/actividades/A-N01', headers=H).status_code, 200)
        self.assertEqual(len(a.get('/planificador/api/almacen/actividades').json()), 1)

    def test_05_autonumerados_y_validaciones(self):
        a = self.cliente('ana', 'Mate-Luna-2026')
        n1 = a.put('/planificador/api/almacen/registro', json={'modo': 'plantilla'}, headers=H).json()['n']
        n2 = a.put('/planificador/api/almacen/registro', json={'modo': 'IA'}, headers=H).json()['n']
        self.assertEqual(n2, n1 + 1)
        self.assertEqual(a.put('/planificador/api/almacen/otra', json={'id': '1'}, headers=H).status_code, 404)
        self.assertEqual(a.put('/planificador/api/almacen/actividades', json={'titulo': 'sin id'}, headers=H).status_code, 400)

    def test_06_banco_compartido_solo_admin(self):
        a, ad, l = self.cliente('ana', 'Mate-Luna-2026'), self.cliente('admin1', 'Zeta-Sol-2026'), self.cliente('luis', 'Rio-Monte-2026')
        a.put('/planificador/api/almacen/actividades', json={'id': 'A-N07', 'titulo': 'Para compartir', 'grados': [5], 'registros': ['C01']}, headers=H)
        self.assertEqual(a.get('/planificador/api/admin/actividades').status_code, 403)
        self.assertEqual(a.post('/planificador/api/admin/compartir', json={'usuario_id': 2, 'id': 'A-N07'}, headers=H).status_code, 403)
        self.assertIn(ad.get('/planificador/admin', follow_redirects=False).status_code, (200,))
        self.assertIn(a.get('/planificador/admin', follow_redirects=False).status_code, (302, 303, 307))
        lista = [x for x in ad.get('/planificador/api/admin/actividades').json() if x['id'] == 'A-N07']
        self.assertEqual(len(lista), 1)
        r = ad.post('/planificador/api/admin/compartir', json={'usuario_id': lista[0]['usuario_id'], 'id': 'A-N07'}, headers=H); self.assertEqual(r.status_code, 200)
        cid = r.json()['id']
        self.assertEqual(ad.post('/planificador/api/admin/compartir', json={'usuario_id': lista[0]['usuario_id'], 'id': 'A-N07'}, headers=H).status_code, 409)
        self.assertIn(cid, [x['id'] for x in l.get('/planificador/api/compartidas').json()])
        self.assertEqual(ad.delete('/planificador/api/admin/compartidas/' + cid, headers=H).status_code, 200)
        self.assertNotIn(cid, [x['id'] for x in l.get('/planificador/api/compartidas').json()])
        self.assertEqual(ad.get('/planificador/api/admin/registro.csv').status_code, 200)

    def test_07_puente_ollama(self):
        l = self.cliente('luis', 'Rio-Monte-2026')
        self.assertEqual(l.get('/planificador/api/ollama/api/tags').json()['models'][0]['name'], 'qwen3:1.7b')
        r = l.post('/planificador/api/ollama/api/chat', json={'model': 'qwen3:1.7b'}, headers=H)
        self.assertEqual(json.loads(r.json()['message']['content']), {'eco': 'qwen3:1.7b'})
        self.assertEqual(l.get('/planificador/api/ollama/api/delete').status_code, 404)

    def test_08_no_rompe_lo_existente(self):
        c = self.cliente('ana', 'Mate-Luna-2026')
        self.assertEqual(c.get('/sesion').status_code, 200)
        self.assertEqual(c.get('/formulario', follow_redirects=False).status_code, 200)
        self.assertEqual(c.get('/usuarios').status_code, 403)
        con = sqlite3.connect(motor.BASE); tablas = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}; con.close()
        self.assertTrue({'usuarios', 'sesiones', 'registro_accesos', 'propuestas_guardadas', 'planificador_datos', 'planificador_compartidas'} <= tablas)


if __name__ == '__main__':
    unittest.main(verbosity=2)
