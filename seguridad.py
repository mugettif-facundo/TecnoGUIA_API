"""Seguridad de TecnoGUIA: usuarios, perfiles, contraseñas, sesiones y registro de accesos.

Usa solo la biblioteca estándar de Python (no requiere instalar paquetes).

Perfiles:
  docente        Genera, edita y guarda actividades. Ve solo sus propias propuestas.
  administrador  Todo lo del docente; además ve todas las propuestas, gestiona
                 usuarios y consulta el registro de accesos.

Protección aplicada:
  - Contraseñas con PBKDF2-HMAC-SHA256 (600.000 iteraciones, sal aleatoria de 16 bytes).
    Nunca se guardan en texto plano.
  - Sesiones con un token aleatorio de 256 bits; en la base se guarda solo su
    huella SHA-256. Vencen a las 8 horas o al cerrar sesión.
  - Bloqueo temporal tras 5 intentos fallidos (15 minutos).
  - Contraseña temporal obligatoria de cambiar cuando la asigna un administrador.
  - Registro de accesos y acciones relevantes.
"""
import base64, hashlib, hmac, secrets, sqlite3
from datetime import datetime, timedelta, timezone

PERFILES = ('docente', 'administrador')
ITERACIONES = 600_000
DURACION_SESION = timedelta(hours=8)
MAX_INTENTOS = 5
BLOQUEO = timedelta(minutes=15)
LARGO_MINIMO_CLAVE = 8
COOKIE = 'tecnoguia_sesion'


class ErrorSeguridad(Exception):
    def __init__(self, mensaje, codigo=400):
        self.mensaje = mensaje; self.codigo = codigo
        super().__init__(mensaje)


def ahora():
    return datetime.now(timezone.utc)


def _iso(fecha):
    return fecha.isoformat(timespec='seconds')


# ---------- Estructura en la base ----------

ESQUEMA = '''
CREATE TABLE IF NOT EXISTS usuarios(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  usuario TEXT NOT NULL UNIQUE,
  nombre TEXT NOT NULL,
  perfil TEXT NOT NULL CHECK(perfil IN ('docente','administrador')),
  clave_hash TEXT NOT NULL,
  activo INTEGER NOT NULL DEFAULT 1 CHECK(activo IN (0,1)),
  debe_cambiar_clave INTEGER NOT NULL DEFAULT 1 CHECK(debe_cambiar_clave IN (0,1)),
  intentos_fallidos INTEGER NOT NULL DEFAULT 0,
  bloqueado_hasta TEXT,
  creado_en TEXT NOT NULL,
  ultimo_ingreso TEXT
);
CREATE TABLE IF NOT EXISTS sesiones(
  token_hash TEXT PRIMARY KEY,
  usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
  creada_en TEXT NOT NULL,
  expira_en TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS registro_accesos(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  fecha TEXT NOT NULL,
  usuario TEXT,
  evento TEXT NOT NULL,
  detalle TEXT,
  ip TEXT
);
CREATE INDEX IF NOT EXISTS idx_registro_fecha ON registro_accesos(fecha);
'''


def preparar(con):
    """Crea las tablas de seguridad y agrega el autor a las propuestas. Es idempotente."""
    con.executescript(ESQUEMA)
    columnas = [c[1] for c in con.execute('PRAGMA table_info(propuestas_guardadas)')]
    if columnas and 'usuario_id' not in columnas:
        con.execute('ALTER TABLE propuestas_guardadas ADD COLUMN usuario_id INTEGER REFERENCES usuarios(id)')
    con.commit()


def esta_preparada(con):
    tablas = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if not {'usuarios', 'sesiones', 'registro_accesos'} <= tablas:
        return False
    columnas = [c[1] for c in con.execute('PRAGMA table_info(propuestas_guardadas)')]
    return 'usuario_id' in columnas


# ---------- Contraseñas ----------

def hash_clave(clave, iteraciones=None):
    iteraciones = iteraciones or ITERACIONES
    sal = secrets.token_bytes(16)
    derivada = hashlib.pbkdf2_hmac('sha256', clave.encode('utf-8'), sal, iteraciones)
    return 'pbkdf2_sha256$%d$%s$%s' % (iteraciones, base64.b64encode(sal).decode(), base64.b64encode(derivada).decode())


def verificar_clave(clave, guardado):
    try:
        algoritmo, iteraciones, sal, esperado = guardado.split('$')
        if algoritmo != 'pbkdf2_sha256':
            return False
        derivada = hashlib.pbkdf2_hmac('sha256', clave.encode('utf-8'), base64.b64decode(sal), int(iteraciones))
        return hmac.compare_digest(derivada, base64.b64decode(esperado))
    except (ValueError, TypeError):
        return False


# Se usa para que un usuario inexistente tarde lo mismo que uno existente.
_HASH_FICTICIO = hash_clave(secrets.token_urlsafe(16))


def validar_clave_nueva(clave, usuario=''):
    if len(clave) < LARGO_MINIMO_CLAVE:
        raise ErrorSeguridad(f'La contraseña debe tener al menos {LARGO_MINIMO_CLAVE} caracteres.', 422)
    if len(clave) > 200:
        raise ErrorSeguridad('La contraseña es demasiado larga.', 422)
    if usuario and usuario.lower() in clave.lower():
        raise ErrorSeguridad('La contraseña no puede contener el nombre de usuario.', 422)
    if clave.isdigit() or clave.isalpha():
        raise ErrorSeguridad('La contraseña debe combinar letras y números o símbolos.', 422)


def normalizar_usuario(usuario):
    usuario = (usuario or '').strip().lower()
    if not (3 <= len(usuario) <= 40) or not all(c.isalnum() or c in '._-' for c in usuario):
        raise ErrorSeguridad('El usuario debe tener entre 3 y 40 caracteres: letras, números, punto, guion o guion bajo.', 422)
    return usuario


# ---------- Registro ----------

def registrar(con, evento, usuario=None, detalle=None, ip=None):
    con.execute('INSERT INTO registro_accesos(fecha,usuario,evento,detalle,ip) VALUES (?,?,?,?,?)',
                (_iso(ahora()), usuario, evento, (detalle or '')[:500] or None, ip))
    con.commit()


def leer_registro(con, limite=200):
    return [dict(r) for r in con.execute('SELECT fecha,usuario,evento,detalle,ip FROM registro_accesos ORDER BY id DESC LIMIT ?', (limite,))]


# ---------- Usuarios ----------

def _publico(fila):
    return {'id': fila['id'], 'usuario': fila['usuario'], 'nombre': fila['nombre'], 'perfil': fila['perfil'],
            'activo': bool(fila['activo']), 'debe_cambiar_clave': bool(fila['debe_cambiar_clave']),
            'creado_en': fila['creado_en'], 'ultimo_ingreso': fila['ultimo_ingreso']}


def crear_usuario(con, usuario, nombre, perfil, clave, debe_cambiar_clave=True, autor=None):
    usuario = normalizar_usuario(usuario)
    nombre = (nombre or '').strip()
    if not 2 <= len(nombre) <= 80:
        raise ErrorSeguridad('Indicá un nombre de entre 2 y 80 caracteres.', 422)
    if perfil not in PERFILES:
        raise ErrorSeguridad('Perfil no válido.', 422)
    validar_clave_nueva(clave, usuario)
    try:
        cur = con.execute('INSERT INTO usuarios(usuario,nombre,perfil,clave_hash,debe_cambiar_clave,creado_en) VALUES (?,?,?,?,?,?)',
                          (usuario, nombre, perfil, hash_clave(clave), int(debe_cambiar_clave), _iso(ahora())))
    except sqlite3.IntegrityError as exc:
        raise ErrorSeguridad('Ya existe ese nombre de usuario.', 409) from exc
    con.commit()
    registrar(con, 'usuario_creado', autor, f'{usuario} ({perfil})')
    return obtener_usuario(con, cur.lastrowid)


def obtener_usuario(con, usuario_id):
    fila = con.execute('SELECT * FROM usuarios WHERE id=?', (usuario_id,)).fetchone()
    return _publico(fila) if fila else None


def listar_usuarios(con):
    return [_publico(f) for f in con.execute('SELECT * FROM usuarios ORDER BY perfil DESC, usuario')]


def _administradores_activos(con):
    return con.execute("SELECT COUNT(*) FROM usuarios WHERE perfil='administrador' AND activo=1").fetchone()[0]


def modificar_usuario(con, usuario_id, autor, nombre=None, perfil=None, activo=None):
    fila = con.execute('SELECT * FROM usuarios WHERE id=?', (usuario_id,)).fetchone()
    if not fila:
        raise ErrorSeguridad('No existe ese usuario.', 404)
    deja_de_ser_admin = fila['perfil'] == 'administrador' and fila['activo'] and (perfil == 'docente' or activo is False)
    if deja_de_ser_admin and _administradores_activos(con) <= 1:
        raise ErrorSeguridad('Debe quedar al menos un administrador activo.', 409)
    cambios = []
    if nombre is not None:
        nombre = nombre.strip()
        if not 2 <= len(nombre) <= 80:
            raise ErrorSeguridad('Indicá un nombre de entre 2 y 80 caracteres.', 422)
        con.execute('UPDATE usuarios SET nombre=? WHERE id=?', (nombre, usuario_id)); cambios.append('nombre')
    if perfil is not None:
        if perfil not in PERFILES:
            raise ErrorSeguridad('Perfil no válido.', 422)
        con.execute('UPDATE usuarios SET perfil=? WHERE id=?', (perfil, usuario_id)); cambios.append('perfil=' + perfil)
    if activo is not None:
        con.execute('UPDATE usuarios SET activo=?, intentos_fallidos=0, bloqueado_hasta=NULL WHERE id=?', (int(activo), usuario_id))
        cambios.append('activo' if activo else 'desactivado')
        if not activo:
            con.execute('DELETE FROM sesiones WHERE usuario_id=?', (usuario_id,))
    if perfil is not None:
        con.execute('DELETE FROM sesiones WHERE usuario_id=?', (usuario_id,))  # el nuevo perfil rige desde el próximo ingreso
    con.commit()
    registrar(con, 'usuario_modificado', autor, fila['usuario'] + ': ' + ', '.join(cambios))
    return obtener_usuario(con, usuario_id)


def restablecer_clave(con, usuario_id, clave_temporal, autor):
    fila = con.execute('SELECT usuario FROM usuarios WHERE id=?', (usuario_id,)).fetchone()
    if not fila:
        raise ErrorSeguridad('No existe ese usuario.', 404)
    validar_clave_nueva(clave_temporal, fila['usuario'])
    con.execute('UPDATE usuarios SET clave_hash=?, debe_cambiar_clave=1, intentos_fallidos=0, bloqueado_hasta=NULL WHERE id=?',
                (hash_clave(clave_temporal), usuario_id))
    con.execute('DELETE FROM sesiones WHERE usuario_id=?', (usuario_id,))
    con.commit()
    registrar(con, 'clave_restablecida', autor, fila['usuario'])


def cambiar_clave_propia(con, usuario_id, actual, nueva, token_actual=None):
    fila = con.execute('SELECT * FROM usuarios WHERE id=?', (usuario_id,)).fetchone()
    if not fila or not verificar_clave(actual, fila['clave_hash']):
        raise ErrorSeguridad('La contraseña actual no es correcta.', 403)
    if actual == nueva:
        raise ErrorSeguridad('La nueva contraseña debe ser distinta de la actual.', 422)
    validar_clave_nueva(nueva, fila['usuario'])
    con.execute('UPDATE usuarios SET clave_hash=?, debe_cambiar_clave=0 WHERE id=?', (hash_clave(nueva), usuario_id))
    # Cierra las demás sesiones abiertas de ese usuario.
    if token_actual:
        con.execute('DELETE FROM sesiones WHERE usuario_id=? AND token_hash<>?', (usuario_id, _huella(token_actual)))
    con.commit()
    registrar(con, 'clave_cambiada', fila['usuario'])


# ---------- Sesiones ----------

def _huella(token):
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def ingresar(con, usuario, clave, ip=None):
    """Devuelve (token, usuario_publico). Mensaje genérico ante cualquier error de credenciales."""
    generico = ErrorSeguridad('Usuario o contraseña incorrectos.', 401)
    try:
        usuario = normalizar_usuario(usuario)
    except ErrorSeguridad:
        verificar_clave(clave or '', _HASH_FICTICIO)
        raise generico
    fila = con.execute('SELECT * FROM usuarios WHERE usuario=?', (usuario,)).fetchone()
    if fila is None:
        verificar_clave(clave or '', _HASH_FICTICIO)
        registrar(con, 'ingreso_fallido', usuario, 'usuario inexistente', ip)
        raise generico
    if fila['bloqueado_hasta'] and datetime.fromisoformat(fila['bloqueado_hasta']) > ahora():
        registrar(con, 'ingreso_bloqueado', usuario, None, ip)
        raise ErrorSeguridad('Demasiados intentos fallidos. Esperá 15 minutos o pedí al administrador que desbloquee la cuenta.', 429)
    if not verificar_clave(clave or '', fila['clave_hash']):
        intentos = fila['intentos_fallidos'] + 1
        bloqueo = _iso(ahora() + BLOQUEO) if intentos >= MAX_INTENTOS else None
        con.execute('UPDATE usuarios SET intentos_fallidos=?, bloqueado_hasta=? WHERE id=?',
                    (0 if bloqueo else intentos, bloqueo, fila['id']))
        con.commit()
        registrar(con, 'ingreso_fallido', usuario, 'cuenta bloqueada 15 min' if bloqueo else f'intento {intentos}', ip)
        raise generico
    if not fila['activo']:
        registrar(con, 'ingreso_rechazado', usuario, 'cuenta desactivada', ip)
        raise generico
    token = secrets.token_urlsafe(32)
    momento = ahora()
    con.execute('DELETE FROM sesiones WHERE expira_en<?', (_iso(momento),))
    con.execute('INSERT INTO sesiones VALUES (?,?,?,?)', (_huella(token), fila['id'], _iso(momento), _iso(momento + DURACION_SESION)))
    con.execute('UPDATE usuarios SET intentos_fallidos=0, bloqueado_hasta=NULL, ultimo_ingreso=? WHERE id=?', (_iso(momento), fila['id']))
    con.commit()
    registrar(con, 'ingreso', usuario, None, ip)
    return token, obtener_usuario(con, fila['id'])


def usuario_de_sesion(con, token):
    """Usuario activo de una sesión vigente, o None."""
    if not token or len(token) > 200:
        return None
    fila = con.execute('''SELECT u.*, s.expira_en FROM sesiones s JOIN usuarios u ON u.id=s.usuario_id
                          WHERE s.token_hash=?''', (_huella(token),)).fetchone()
    if not fila:
        return None
    if datetime.fromisoformat(fila['expira_en']) <= ahora() or not fila['activo']:
        con.execute('DELETE FROM sesiones WHERE token_hash=?', (_huella(token),)); con.commit()
        return None
    return _publico(fila)


def cerrar_sesion(con, token, usuario=None):
    if token:
        con.execute('DELETE FROM sesiones WHERE token_hash=?', (_huella(token),)); con.commit()
        registrar(con, 'salida', usuario)


def conectar(ruta):
    # FastAPI puede abrir la conexión en un hilo y usarla en otro dentro del mismo pedido;
    # cada pedido tiene su propia conexión y la usa de a un paso, así que es seguro.
    con = sqlite3.connect(ruta, timeout=10, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    return con
