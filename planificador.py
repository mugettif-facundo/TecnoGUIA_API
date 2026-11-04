"""Planificador con fuentes curriculares (TecnoGUIA web 0.12.1) integrado a la API de TecnoGUIA 0.9.

Se monta dentro de la misma aplicación FastAPI y reutiliza su ingreso, sus perfiles y su base:
  * /planificador/          la pantalla (solo con sesión iniciada; si no, redirige a /ingresar);
  * /planificador/api/...   guarda en SQLite (tecnoguia.db), por usuario: actividades propias,
                            registro de generaciones, pruebas funcionales y valoraciones;
  * /planificador/api/ollama/...  puente hacia Ollama (que sigue en esta computadora);
  * /planificador/admin     (solo administradores) actividades de los docentes y banco compartido.
La búsqueda curricular y la generación del borrador siguen ocurriendo en el navegador
(planificador/web/js/motor.js, igual a la versión evaluada 0.12.1-web).
No toca ninguna tabla existente: agrega planificador_datos y planificador_compartidas.
"""
import csv, io, json, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import motor
import seguridad

VERSION = '0.10.0'
WEB = Path(__file__).resolve().parent / 'planificador' / 'web'
OLLAMA_URL = __import__('os').environ.get('OLLAMA_URL', 'http://127.0.0.1:11434').rstrip('/')
ALMACENES = {'actividades': 'id', 'funcionales': 'id', 'registro': 'n', 'valoraciones': 'n'}
RUTAS_OLLAMA = {'api/chat': 'POST', 'api/tags': 'GET', 'api/version': 'GET'}

ESQUEMA = '''
CREATE TABLE IF NOT EXISTS planificador_datos(
  usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
  almacen TEXT NOT NULL,
  clave TEXT NOT NULL,
  json TEXT NOT NULL,
  actualizado TEXT NOT NULL,
  PRIMARY KEY(usuario_id, almacen, clave)
);
CREATE TABLE IF NOT EXISTS planificador_compartidas(
  id TEXT PRIMARY KEY,
  json TEXT NOT NULL,
  origen_usuario_id INTEGER REFERENCES usuarios(id),
  origen_id TEXT,
  publicada TEXT NOT NULL,
  publicada_por INTEGER REFERENCES usuarios(id)
);
'''


def ahora():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def conexion():
    """Una conexión por pedido; crea las tablas propias si faltan (no toca las existentes)."""
    if not motor.BASE.is_file():
        raise HTTPException(503, 'Falta tecnoguia.db.')
    con = seguridad.conectar(motor.BASE)
    try:
        con.executescript(ESQUEMA)
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def _pedir_ollama(metodo, ruta, cuerpo):
    req = urllib.request.Request(OLLAMA_URL + '/' + ruta, data=cuerpo, method=metodo, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:  # Ollama apagado o sin respuesta
        return 503, json.dumps({'error': 'Ollama no responde en %s (%s)' % (OLLAMA_URL, type(e).__name__)}).encode()


class Compartir(BaseModel):
    usuario_id: int
    id: str


def montar(app, usuario_actual, solo_administrador, sesion_para_pagina):
    r = APIRouter(prefix='/planificador')

    def pagina(nombre):
        return FileResponse(WEB / nombre, headers={'Cache-Control': 'no-store', 'X-Frame-Options': 'DENY'})

    @r.get('', include_in_schema=False)
    def sin_barra():
        return RedirectResponse('/planificador/', status_code=307)

    @r.get('/', include_in_schema=False)
    def inicio(request: Request):
        u = sesion_para_pagina(request)
        if not u or u['debe_cambiar_clave']:
            return RedirectResponse('/ingresar', status_code=303)
        return pagina('index.html')

    @r.get('/admin', include_in_schema=False)
    def admin(request: Request):
        u = sesion_para_pagina(request)
        if not u or u['debe_cambiar_clave']:
            return RedirectResponse('/ingresar', status_code=303)
        if u['perfil'] != 'administrador':
            return RedirectResponse('/planificador/', status_code=303)
        return pagina('admin.html')

    # ---------- datos por usuario ----------
    def _almacen(nombre):
        if nombre not in ALMACENES:
            raise HTTPException(404, 'Almacén desconocido.')

    @r.get('/api/almacen/{nombre}')
    def listar(nombre: str, u=Depends(usuario_actual), con=Depends(conexion)):
        _almacen(nombre)
        filas = con.execute('SELECT json FROM planificador_datos WHERE usuario_id=? AND almacen=?', (u['id'], nombre)).fetchall()
        return [json.loads(f['json']) for f in filas]

    @r.put('/api/almacen/{nombre}')
    async def guardar(nombre: str, request: Request, u=Depends(usuario_actual), con=Depends(conexion)):
        _almacen(nombre)
        try:
            obj = await request.json()
        except Exception:
            raise HTTPException(400, 'El cuerpo no es JSON.')
        if not isinstance(obj, dict) or len(json.dumps(obj)) > 400_000:
            raise HTTPException(400, 'Dato inválido o demasiado grande.')
        campo = ALMACENES[nombre]
        if campo == 'n':
            if obj.get('n') in (None, ''):
                obj['n'] = con.execute('SELECT COALESCE(MAX(CAST(clave AS INTEGER)),0)+1 FROM planificador_datos WHERE usuario_id=? AND almacen=?', (u['id'], nombre)).fetchone()[0]
            obj['n'] = int(obj['n'])
        clave = str(obj.get(campo, '')).strip()
        if not clave or len(clave) > 60:
            raise HTTPException(400, 'Falta el identificador (%s).' % campo)
        con.execute('''INSERT INTO planificador_datos(usuario_id, almacen, clave, json, actualizado) VALUES (?,?,?,?,?)
                       ON CONFLICT(usuario_id, almacen, clave) DO UPDATE SET json=excluded.json, actualizado=excluded.actualizado''',
                    (u['id'], nombre, clave, json.dumps(obj, ensure_ascii=False), ahora()))
        if nombre == 'actividades':
            seguridad.registrar(con, 'planificador_actividad_guardada', u['usuario'], clave)
        return obj

    @r.delete('/api/almacen/{nombre}/{clave}')
    def borrar(nombre: str, clave: str, request: Request, u=Depends(usuario_actual), con=Depends(conexion)):
        _almacen(nombre)
        con.execute('DELETE FROM planificador_datos WHERE usuario_id=? AND almacen=? AND clave=?', (u['id'], nombre, clave))
        seguridad.registrar(con, 'planificador_borrar_' + nombre, u['usuario'], clave)
        return {'ok': True}

    @r.get('/api/compartidas')
    def compartidas(u=Depends(usuario_actual), con=Depends(conexion)):
        return [json.loads(f['json']) for f in con.execute('SELECT json FROM planificador_compartidas ORDER BY id')]

    # ---------- puente a Ollama ----------
    @r.api_route('/api/ollama/{ruta:path}', methods=['GET', 'POST'])
    async def ollama(ruta: str, request: Request, u=Depends(usuario_actual)):
        if RUTAS_OLLAMA.get(ruta) != request.method:
            raise HTTPException(404, 'Ruta no permitida.')
        cuerpo = await request.body() if request.method == 'POST' else None
        estado, datos = await run_in_threadpool(_pedir_ollama, request.method, ruta, cuerpo)
        return Response(content=datos, status_code=estado, media_type='application/json')

    # ---------- administración (solo administradores) ----------
    @r.get('/api/admin/actividades')
    def a_actividades(a=Depends(solo_administrador), con=Depends(conexion)):
        filas = con.execute('''SELECT d.usuario_id, u.usuario, u.nombre, d.clave, d.json, d.actualizado,
            (SELECT 1 FROM planificador_compartidas c WHERE c.origen_usuario_id=d.usuario_id AND c.origen_id=d.clave) AS compartida
            FROM planificador_datos d JOIN usuarios u ON u.id=d.usuario_id WHERE d.almacen='actividades' ORDER BY d.actualizado DESC''').fetchall()
        salida = []
        for f in filas:
            x = json.loads(f['json'])
            salida.append({'usuario_id': f['usuario_id'], 'usuario': f['usuario'], 'nombre': f['nombre'], 'id': f['clave'], 'titulo': x.get('titulo'),
                           'grados': x.get('grados'), 'registros': x.get('registros'), 'actualizado': f['actualizado'], 'compartida': bool(f['compartida'])})
        return salida

    @r.get('/api/admin/compartidas')
    def a_compartidas(a=Depends(solo_administrador), con=Depends(conexion)):
        return [{'id': f['id'], 'titulo': json.loads(f['json']).get('titulo'), 'publicada': f['publicada']} for f in con.execute('SELECT * FROM planificador_compartidas ORDER BY id')]

    @r.post('/api/admin/compartir')
    def a_compartir(d: Compartir, a=Depends(solo_administrador), con=Depends(conexion)):
        f = con.execute("SELECT json FROM planificador_datos WHERE usuario_id=? AND almacen='actividades' AND clave=?", (d.usuario_id, d.id)).fetchone()
        if not f:
            raise HTTPException(404, 'No existe la actividad.')
        if con.execute('SELECT 1 FROM planificador_compartidas WHERE origen_usuario_id=? AND origen_id=?', (d.usuario_id, d.id)).fetchone():
            raise HTTPException(409, 'Ya está en el banco compartido.')
        act = json.loads(f['json'])
        n = con.execute('SELECT COALESCE(MAX(CAST(SUBSTR(id,3) AS INTEGER)),0)+1 FROM planificador_compartidas').fetchone()[0]
        cid = 'A-C%02d' % n
        act.update({'id': cid, 'tipo': 'compartida', 'procedencia': 'Banco compartido de TecnoGUIA (publicada por administración; origen %s de un docente).' % d.id})
        con.execute('INSERT INTO planificador_compartidas(id,json,origen_usuario_id,origen_id,publicada,publicada_por) VALUES (?,?,?,?,?,?)',
                    (cid, json.dumps(act, ensure_ascii=False), d.usuario_id, d.id, ahora(), a['id']))
        seguridad.registrar(con, 'planificador_compartir', a['usuario'], '%s -> %s' % (d.id, cid))
        return {'id': cid}

    @r.delete('/api/admin/compartidas/{cid}')
    def a_quitar(cid: str, a=Depends(solo_administrador), con=Depends(conexion)):
        con.execute('DELETE FROM planificador_compartidas WHERE id=?', (cid,))
        seguridad.registrar(con, 'planificador_quitar_compartida', a['usuario'], cid)
        return {'ok': True}

    @r.get('/api/admin/registro.csv')
    def a_csv(a=Depends(solo_administrador), con=Depends(conexion)):
        filas = con.execute("SELECT u.usuario, d.json FROM planificador_datos d JOIN usuarios u ON u.id=d.usuario_id WHERE d.almacen='registro' ORDER BY d.actualizado").fetchall()
        cols = ['fecha', 'version', 'caso', 'borrador', 'grado', 'consulta', 'registro_usado', 'experiencias', 'modo', 'modelo', 'segundos', 'adecuacion', 'avisos', 'resultado']
        s = io.StringIO(); w = csv.writer(s); w.writerow(['usuario'] + cols)
        for f in filas:
            x = json.loads(f['json']); w.writerow([f['usuario']] + [x.get(c, '') for c in cols])
        return Response(content='﻿' + s.getvalue(), media_type='text/csv; charset=utf-8', headers={'Content-Disposition': 'attachment; filename=TecnoGUIA_planificador_registro_todos.csv'})

    app.include_router(r)
    app.mount('/planificador', StaticFiles(directory=WEB), name='planificador_web')
