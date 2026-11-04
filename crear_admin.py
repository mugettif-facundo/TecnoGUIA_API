"""Prepara los usuarios de TecnoGUIA y crea el primer administrador.

Ejecutar UNA vez, con Uvicorn detenido:
    .venv\\Scripts\\python.exe crear_admin.py

Qué hace:
  1. Respalda la base (tecnoguia_respaldo_FECHA.db).
  2. Crea las tablas usuarios, sesiones y registro_accesos, y agrega a
     propuestas_guardadas la columna usuario_id (autor). No borra nada.
  3. Pide usuario, nombre y contraseña del primer administrador.
  4. Asigna al administrador las propuestas guardadas antes de esta versión,
     que no tenían autor.
Si ya existe un administrador, solo verifica la estructura: los demás usuarios
se crean desde la pantalla Administración.
"""
import argparse, getpass, sqlite3, sys
from datetime import datetime
from pathlib import Path

import seguridad

BASE = Path(__file__).resolve().parent / 'tecnoguia.db'


def respaldar(ruta):
    destino = ruta.with_name(f'tecnoguia_respaldo_{datetime.now():%Y%m%d_%H%M%S}.db')
    n = 2
    while destino.exists():
        destino = ruta.with_name(f'tecnoguia_respaldo_{datetime.now():%Y%m%d_%H%M%S}_{n}.db'); n += 1
    origen = sqlite3.connect(ruta)
    with sqlite3.connect(destino) as copia:
        origen.backup(copia)
    origen.close()
    return destino


def configurar(ruta, usuario, nombre, clave):
    """Crea el primer administrador y le asigna las propuestas sin autor. Devuelve (admin, propuestas_asignadas)."""
    con = seguridad.conectar(ruta)
    try:
        seguridad.preparar(con)
        admin = seguridad.crear_usuario(con, usuario, nombre, 'administrador', clave, debe_cambiar_clave=False, autor='crear_admin.py')
        cur = con.execute('UPDATE propuestas_guardadas SET usuario_id=? WHERE usuario_id IS NULL', (admin['id'],))
        con.commit()
        seguridad.registrar(con, 'propuestas_asignadas', 'crear_admin.py', f'{cur.rowcount} propuestas anteriores asignadas a {admin["usuario"]}')
        return admin, cur.rowcount
    finally:
        con.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default=str(BASE))
    ruta = Path(ap.parse_args().base)
    if not ruta.is_file():
        sys.exit('No se encontró ' + str(ruta) + '. Ejecutá primero crear_base.py y los scripts de importación.')
    con = sqlite3.connect(ruta)
    try:
        con.execute('BEGIN IMMEDIATE'); con.rollback()
    except sqlite3.OperationalError:
        sys.exit('La base está en uso. Detené Uvicorn (Ctrl+C) y volvé a ejecutar.')
    hay_admin = False
    if {'usuarios'} <= {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}:
        hay_admin = con.execute("SELECT COUNT(*) FROM usuarios WHERE perfil='administrador'").fetchone()[0] > 0
    con.close()

    print('Respaldo creado:', respaldar(ruta).name)
    if hay_admin:
        c = seguridad.conectar(ruta); seguridad.preparar(c); c.close()
        print('Ya existe un administrador. La estructura de seguridad está al día.')
        print('Creá los demás usuarios desde http://127.0.0.1:8000/administracion')
        return

    print('\nPrimer administrador de TecnoGUIA')
    while True:
        try:
            usuario = seguridad.normalizar_usuario(input('Usuario (ej.: fmugetti): '))
            nombre = input('Nombre y apellido: ').strip()
            clave = getpass.getpass('Contraseña (no se ve al escribir): ')
            if clave != getpass.getpass('Repetí la contraseña: '):
                print('Las contraseñas no coinciden. Probá de nuevo.\n'); continue
            admin, asignadas = configurar(ruta, usuario, nombre, clave)
            break
        except seguridad.ErrorSeguridad as exc:
            print('Error:', exc.mensaje, '\n')
    print(f'\nAdministrador creado: {admin["usuario"]} ({admin["nombre"]}).')
    print(f'Propuestas anteriores asignadas a este administrador: {asignadas}.')
    print('Iniciá Uvicorn y entrá en http://127.0.0.1:8000/ingresar')


if __name__ == '__main__':
    main()
