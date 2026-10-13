"""Repara acentos rotos en tecnoguia.db ("TecnolÃ³gicos" -> "Tecnológicos").

Causa: en versiones anteriores, asociar_nap.py leía vinculos_nap.json sin
indicar UTF-8. En Windows eso usa otra codificación (cp1252) y cada letra
acentuada quedó guardada como dos caracteres raros. Los ejes y contenidos NAP
quedaron así en la base, y la IA también los recibía rotos.

Qué hace:
  1. Crea una copia de respaldo de la base (tecnoguia_respaldo_FECHA.db).
  2. Busca en las tablas los pares de caracteres rotos y los reemplaza por
     la letra correcta. El texto que ya estaba bien no se toca.
  3. No modifica las propuestas guardadas, salvo que lo pidas con
     --incluir-propuestas (solo corrige acentos, no cambia su contenido).

Uso (con Uvicorn DETENIDO):
    .venv\\Scripts\\python.exe reparar_acentos.py --simular     (solo muestra qué cambiaría)
    .venv\\Scripts\\python.exe reparar_acentos.py               (repara)
    .venv\\Scripts\\python.exe reparar_acentos.py --incluir-propuestas
Se puede ejecutar más de una vez: si no hay nada roto, no cambia nada.
"""
import argparse, re, sqlite3, sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent / 'tecnoguia.db'
# Una letra acentuada en UTF-8 leída como cp1252 se ve como "Ã" o "Â" seguida de otro carácter.
PAR_ROTO = re.compile(r'[ÂÃ].')


def arreglar(texto):
    def reemplazo(m):
        par = m.group(0)
        try:
            correcto = par.encode('cp1252').decode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            return par  # no era un acento roto: se deja igual
        return correcto if len(correcto) == 1 else par
    return PAR_ROTO.sub(reemplazo, texto)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--simular', action='store_true', help='Muestra los cambios sin guardar nada.')
    ap.add_argument('--incluir-propuestas', action='store_true', help='También corrige acentos en propuestas guardadas.')
    ap.add_argument('--base', default=str(BASE))
    args = ap.parse_args()
    ruta = Path(args.base)
    if not ruta.is_file():
        sys.exit('No se encontró ' + str(ruta))

    con = sqlite3.connect(ruta)
    try:
        con.execute('BEGIN IMMEDIATE')  # falla si otro programa está escribiendo
        con.rollback()
    except sqlite3.OperationalError:
        sys.exit('La base está en uso. Detené Uvicorn (Ctrl+C) y volvé a ejecutar.')

    tablas = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
    cambios = []  # (tabla, columna, rowid, antes, despues)
    for tabla in tablas:
        if tabla == 'propuestas_guardadas' and not args.incluir_propuestas:
            continue
        columnas = [c[1] for c in con.execute(f'PRAGMA table_info("{tabla}")')]
        for col in columnas:
            for rowid, valor in con.execute(f'SELECT rowid, "{col}" FROM "{tabla}" WHERE typeof("{col}")=\'text\' AND ("{col}" LIKE \'%Ã%\' OR "{col}" LIKE \'%Â%\')'):
                nuevo = arreglar(valor)
                if nuevo != valor:
                    cambios.append((tabla, col, rowid, valor, nuevo))

    if not cambios:
        print('No se encontraron acentos rotos. No hay nada para reparar.')
        return
    resumen = {}
    for t, c, *_ in cambios:
        resumen[(t, c)] = resumen.get((t, c), 0) + 1
    print('Registros con acentos rotos:')
    for (t, c), n in sorted(resumen.items()):
        print(f'  {t}.{c}: {n}')
    print('\nEjemplos:')
    for t, c, _, antes, despues in cambios[:5]:
        i = next(k for k, (x, y) in enumerate(zip(antes, despues)) if x != y)
        desde = max(0, i - 25)
        print(f'  {t}: ...{antes[desde:desde + 60]}\n     -> ...{despues[desde:desde + 55]}')
    if not args.incluir_propuestas and 'propuestas_guardadas' in tablas:
        n = con.execute("SELECT COUNT(*) FROM propuestas_guardadas WHERE guia_json LIKE '%Ã%' OR guia_json LIKE '%Â%'").fetchone()[0]
        if n:
            print(f'\nAviso: {n} propuesta(s) guardada(s) también tienen acentos rotos (por ejemplo en la referencia curricular).')
            print('No se tocaron. Para corregirlas, ejecutá con --incluir-propuestas.')

    if args.simular:
        print('\nSimulación: no se guardó ningún cambio.')
        return

    respaldo = ruta.with_name(f'tecnoguia_respaldo_{datetime.now():%Y%m%d_%H%M%S}.db')
    n = 2
    while respaldo.exists():  # nunca sobrescribir un respaldo anterior
        respaldo = ruta.with_name(f'tecnoguia_respaldo_{datetime.now():%Y%m%d_%H%M%S}_{n}.db'); n += 1
    with sqlite3.connect(respaldo) as destino:
        con.backup(destino)
    print('\nRespaldo creado:', respaldo.name)
    with con:
        for t, c, rowid, _, nuevo in cambios:
            con.execute(f'UPDATE "{t}" SET "{c}"=? WHERE rowid=?', (nuevo, rowid))
    con.close()
    print(f'Listo: se repararon {len(cambios)} registros. Reiniciá Uvicorn y recargá el formulario con Ctrl+F5.')


if __name__ == '__main__':
    main()
