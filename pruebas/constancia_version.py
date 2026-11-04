"""Deja constancia de la versión integrada: commit, etiqueta, huellas SHA-256, equipo y fecha.
Uso (dentro de TecnoGUIA_API):   .venv\\Scripts\\python.exe pruebas\\constancia_version.py
Genera constancia_integrada_AAAAMMDD_HHMM.txt (para citar en el acta y el E3)."""
import ctypes, hashlib, os, platform, subprocess, sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARCHIVOS = ['main.py', 'seguridad.py', 'motor.py', 'ia_local.py', 'ia_generadora.py', 'planificador.py', 'ingresar.html', 'administracion.html', 'formulario_multi.html',
            'planificador/web/index.html', 'planificador/web/admin.html', 'planificador/web/js/app.js', 'planificador/web/js/sesion.js', 'planificador/web/js/motor.js',
            'planificador/web/datos/corpus.js', 'planificador/web/datos/banco.js', 'planificador/web/datos/pruebas.js']


def ejecutar(*cmd):
    try:
        return subprocess.run(cmd, cwd=RAIZ, capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception as e:
        return '(no disponible: %s)' % type(e).__name__


def ram():
    try:
        if os.name == 'nt':
            class MEM(ctypes.Structure):
                _fields_ = [('l', ctypes.c_ulong), ('u', ctypes.c_ulong), ('total', ctypes.c_ulonglong), ('a', ctypes.c_ulonglong), ('b', ctypes.c_ulonglong), ('c', ctypes.c_ulonglong), ('d', ctypes.c_ulonglong), ('e', ctypes.c_ulonglong), ('f', ctypes.c_ulonglong)]
            m = MEM(); m.l = ctypes.sizeof(MEM); ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)); return '%.1f GB' % (m.total / 1024 ** 3)
        return '%.1f GB' % (os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / 1024 ** 3)
    except Exception:
        return '(no disponible)'


def main():
    ahora = datetime.now()
    L = ['TecnoGUIA — constancia de la versión integrada (API 0.9 + planificador 0.12.1-web)', 'Fecha: ' + ahora.strftime('%d/%m/%Y %H:%M'), '',
         'Equipo: %s · %s' % (platform.node(), platform.platform()), 'Procesador: ' + (platform.processor() or '(no informado)'), 'Memoria RAM: ' + ram(),
         'Python: ' + sys.version.split()[0], 'Node: ' + ejecutar('node', '--version'), 'Ollama: ' + ejecutar('ollama', '--version').replace('\n', ' '), '',
         'Git commit: ' + ejecutar('git', 'rev-parse', 'HEAD'), 'Git etiqueta: ' + (ejecutar('git', 'describe', '--tags', '--exact-match') or '(sin etiqueta en este commit)'),
         'Árbol de trabajo: ' + ('(no es un repositorio git: hacé git init/commit antes)' if not ejecutar('git', 'rev-parse', 'HEAD') or ejecutar('git','rev-parse','HEAD').startswith('(') else ('SIN CAMBIOS pendientes' if not ejecutar('git', 'status', '--porcelain') else 'HAY CAMBIOS SIN COMMIT (hacé el commit antes de citar esta constancia)')), '',
         'Huellas SHA-256 (Get-FileHash <archivo> -Algorithm SHA256 debe dar lo mismo):']
    for f in ARCHIVOS:
        p = RAIZ / f
        L.append('%s  %s' % (hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else '(FALTA)'.ljust(64), f))
    L += ['', 'Referencia de la versión evaluada 0.12.1-web (deben coincidir las tres del planificador/web/js y datos):',
          '511eed92ee80c60310b23b1f6817f5f01afa18ed1946c17cbe8b0f479ff51ad3  js/motor.js',
          '89a21de3355b15a4c2f185d2e75cc5317a2555c26cb6ff1bbd6037487067ecfc  datos/corpus.js',
          '8da9d6acbe0b0603b1f32d152edf0f2296e710945b0979d1d33a8e1ee34ab859  datos/banco.js',
          '302a5f0323be19f0bb9a277f831886e166cb01df4d5aaa077977730aa0ae5bad  datos/pruebas.js']
    salida = RAIZ / ('constancia_integrada_%s.txt' % ahora.strftime('%Y%m%d_%H%M'))
    salida.write_text('\n'.join(L) + '\n', encoding='utf-8')
    print('\n'.join(L) + '\n\nGuardado en ' + str(salida))


if __name__ == '__main__':
    main()
