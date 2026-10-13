"""Importa sin sobrescribir las 12 guías y los 13 fragmentos del HTML original."""
import json
import sqlite3
from pathlib import Path

CARPETA = Path(__file__).resolve().parent
BASE = CARPETA / 'tecnoguia.db'
CATALOGO = CARPETA / 'catalogo_original.json'
ORIGEN = 'index__2_con_variedad2222.html (versión aportada el 08/10/2026)'


def importar(base=BASE, catalogo=CATALOGO):
    datos = json.loads(Path(catalogo).read_text(encoding='utf-8'))
    if not Path(base).is_file():
        raise RuntimeError('Falta tecnoguia.db. Ejecutá primero crear_base.py.')
    con = sqlite3.connect(base)
    try:
        con.execute('PRAGMA foreign_keys = ON')
        con.executescript('''
        CREATE TABLE IF NOT EXISTS guias_originales (
            id TEXT PRIMARY KEY,
            tema TEXT NOT NULL UNIQUE,
            guia_json TEXT NOT NULL,
            archivo_origen TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'importada_pendiente_revision'
        );
        CREATE TABLE IF NOT EXISTS fragmentos_originales (
            id TEXT PRIMARY KEY,
            tema TEXT NOT NULL,
            eje TEXT NOT NULL,
            grados_json TEXT NOT NULL,
            documento_json TEXT NOT NULL,
            seccion TEXT NOT NULL,
            conceptos_json TEXT NOT NULL,
            texto TEXT NOT NULL,
            registro_json TEXT NOT NULL,
            archivo_origen TEXT NOT NULL,
            verificado INTEGER NOT NULL DEFAULT 0 CHECK (verificado IN (0, 1))
        );
        CREATE TABLE IF NOT EXISTS guia_fragmento_original (
            guia_id TEXT NOT NULL REFERENCES guias_originales(id),
            fragmento_id TEXT NOT NULL REFERENCES fragmentos_originales(id),
            PRIMARY KEY (guia_id, fragmento_id)
        );
        ''')
        with con:
            for numero, (tema, guia) in enumerate(datos['guias'].items(), 1):
                con.execute('''INSERT OR IGNORE INTO guias_originales
                    (id, tema, guia_json, archivo_origen) VALUES (?, ?, ?, ?)''',
                    (f'G{numero:02}', tema, json.dumps(guia, ensure_ascii=False), ORIGEN))
            for frag in datos['corpus']:
                con.execute('''INSERT OR IGNORE INTO fragmentos_originales
                    (id, tema, eje, grados_json, documento_json, seccion,
                     conceptos_json, texto, registro_json, archivo_origen)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (frag['id'], frag['tema'], frag['eje'],
                     json.dumps(frag['grados'], ensure_ascii=False),
                     json.dumps(frag['doc'], ensure_ascii=False), frag['seccion'],
                     json.dumps(frag['conceptos'], ensure_ascii=False), frag['texto'],
                     json.dumps(frag, ensure_ascii=False), ORIGEN))
                row = con.execute('SELECT id FROM guias_originales WHERE tema = ?',
                                  (frag['tema'],)).fetchone()
                if row:
                    con.execute('INSERT OR IGNORE INTO guia_fragmento_original VALUES (?, ?)',
                                (row[0], frag['id']))
        print('Importación terminada; las ediciones existentes se conservaron.')
        for tabla in ('guias_originales', 'fragmentos_originales', 'guia_fragmento_original'):
            cantidad = con.execute(f'SELECT COUNT(*) FROM {tabla}').fetchone()[0]
            print(f'{tabla}: {cantidad}')
    finally:
        con.close()


if __name__ == '__main__':
    importar()
