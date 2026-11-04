"""Restablece la contraseña de un usuario de TecnoGUIA (por ejemplo, el administrador si la olvidaste).
Ejecutar con el servidor DETENIDO, dentro de TecnoGUIA_API:
    .venv\\Scripts\\python.exe restablecer_clave.py
Muestra los usuarios, hace un respaldo de la base y fija una contraseña temporal: al ingresar te pide cambiarla."""
import getpass, sqlite3, sys
from datetime import datetime
from pathlib import Path
import seguridad

BASE = Path(__file__).resolve().parent / 'tecnoguia.db'
if not BASE.is_file():
    sys.exit('No encuentro tecnoguia.db. Ejecutá este archivo dentro de TecnoGUIA_API.')
try:
    t = sqlite3.connect(BASE); t.execute('BEGIN IMMEDIATE'); t.rollback(); t.close()
except sqlite3.OperationalError:
    sys.exit('La base está en uso. Cerrá el servidor (la ventana negra) y volvé a ejecutar.')
con = seguridad.conectar(BASE)
usuarios = con.execute('SELECT id, usuario, nombre, perfil, activo FROM usuarios ORDER BY id').fetchall()
print('Usuarios:')
for u in usuarios:
    print('  %s — %s (%s)%s' % (u['usuario'], u['nombre'], u['perfil'], '' if u['activo'] else ' [desactivado]'))
nombre = seguridad.normalizar_usuario(input('\nUsuario a restablecer: '))
fila = con.execute('SELECT id FROM usuarios WHERE usuario=?', (nombre,)).fetchone()
if not fila:
    sys.exit('No existe ese usuario.')
destino = BASE.with_name('tecnoguia_respaldo_%s.db' % datetime.now().strftime('%Y%m%d_%H%M%S'))
with sqlite3.connect(destino) as copia:
    con.backup(copia)
print('Respaldo creado:', destino.name)
while True:
    clave = getpass.getpass('Contraseña temporal nueva (no se ve): ')
    if clave != getpass.getpass('Repetila: '):
        print('No coinciden.\n'); continue
    try:
        seguridad.restablecer_clave(con, fila['id'], clave, 'restablecer_clave.py'); break
    except seguridad.ErrorSeguridad as e:
        print('Error:', e.mensaje, '\n')
print('Listo. Ingresá con esa contraseña; el sistema te va a pedir cambiarla.')
con.close()
