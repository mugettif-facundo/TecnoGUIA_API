"""Agrega el planificador con fuentes curriculares a TecnoGUIA (integración 0.10.0).

Qué hace (es seguro repetirlo):
  * main.py            -> agrega al final 3 líneas que montan el planificador (copia: main.py.bak_integracion)
  * formulario_multi.html -> agrega un enlace «Planificador con fuentes curriculares» (copia: .bak_integracion)
  * administracion.html   -> agrega un enlace para administradores (copia: .bak_integracion)
No toca la base de datos: las tablas nuevas se crean solas al primer uso.
Ejecutar desde la carpeta TecnoGUIA_API:   .venv\\Scripts\\python.exe aplicar_integracion.py
"""
import shutil
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
MARCA = '# --- Planificador con fuentes curriculares (integración 0.10.0) ---'
BLOQUE = '\n\n' + MARCA + '\nimport planificador\nplanificador.montar(app, usuario_actual, solo_administrador, sesion_para_pagina)\n'


def leer(nombre):
    p = RAIZ / nombre
    if not p.is_file():
        raise SystemExit('No encuentro %s. Ejecutá este archivo dentro de la carpeta TecnoGUIA_API.' % nombre)
    return p, p.read_text(encoding='utf-8')


def respaldo(p):
    b = p.with_name(p.name + '.bak_integracion')
    if not b.exists():
        shutil.copy2(p, b)


def cambiar(nombre, viejo, nuevo, ya):
    p, t = leer(nombre)
    if ya in t:
        print('  = %s ya estaba integrado.' % nombre); return
    if t.count(viejo) != 1:
        raise SystemExit('  ! %s no tiene el texto esperado (%r): no se modificó. Avisame y lo ajusto.' % (nombre, viejo[:50]))
    respaldo(p)
    p.write_text(t.replace(viejo, nuevo), encoding='utf-8')
    print('  + %s actualizado (copia en %s.bak_integracion).' % (nombre, nombre))


def main():
    for f in ('planificador.py', 'planificador/web/index.html', 'planificador/web/js/app.js', 'planificador/web/js/sesion.js', 'planificador/web/js/motor.js'):
        if not (RAIZ / f).is_file():
            raise SystemExit('Falta %s: copiá todo el contenido del paquete dentro de TecnoGUIA_API.' % f)
    p, t = leer('main.py')
    if MARCA in t:
        print('  = main.py ya estaba integrado.')
    else:
        if 'usuario_actual' not in t or 'sesion_para_pagina' not in t or 'solo_administrador' not in t:
            raise SystemExit('  ! main.py no tiene las funciones de seguridad esperadas (versión 0.9).')
        respaldo(p)
        t = t.replace("version='0.9.0'", "version='0.10.0'") if "version='0.9.0'" in t else t
        p.write_text(t.rstrip('\n') + BLOQUE, encoding='utf-8')
        print('  + main.py actualizado (copia en main.py.bak_integracion).')
    cambiar('formulario_multi.html', '<a id="enlace_admin" href="/administracion" hidden>', '<a href="/planificador/">Planificador con fuentes curriculares</a> <a id="enlace_admin" href="/administracion" hidden>', 'href="/planificador/"')
    cambiar('administracion.html', '<a href="/formulario">Volver al generador</a>', '<a href="/planificador/admin">Actividades del planificador</a> <a href="/formulario">Volver al generador</a>', 'href="/planificador/admin"')
    print('\nListo. Iniciá TecnoGUIA como siempre (INICIAR_TECNOGUIA.bat). Nuevo: botón «Planificador con fuentes curriculares».')


if __name__ == '__main__':
    main()
