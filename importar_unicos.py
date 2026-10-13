import json
import sqlite3
from pathlib import Path

CARPETA = Path(__file__).resolve().parent


def importar(base=None):
    base = Path(base) if base else CARPETA / 'tecnoguia.db'
    if not base.is_file():
        raise RuntimeError('Falta tecnoguia.db. Instalá primero la base inicial.')
    datos = json.loads((CARPETA / 'proyectos_unicos.json').read_text(encoding='utf-8'))
    if len(datos) != 100 or {p['numero'] for p in datos} != set(range(1, 101)):
        raise ValueError('El catálogo debe contener los proyectos 1 a 100.')
    con = sqlite3.connect(base)
    try:
        con.executescript('''CREATE TABLE IF NOT EXISTS proyectos_unicos_pdf (
            id TEXT PRIMARY KEY,
            numero INTEGER NOT NULL UNIQUE,
            titulo TEXT NOT NULL,
            bloque INTEGER NOT NULL,
            pagina_pdf INTEGER NOT NULL,
            materiales_originales TEXT NOT NULL,
            principio_original TEXT NOT NULL,
            ficha_json TEXT NOT NULL,
            fuente TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'pendiente_revision',
            contenido_id TEXT,
            FOREIGN KEY (contenido_id) REFERENCES contenidos(id)
        );''')
        con.execute('PRAGMA foreign_keys = ON')
        with con:
            for p in datos:
                con.execute('''INSERT OR IGNORE INTO proyectos_unicos_pdf
                    (id,numero,titulo,bloque,pagina_pdf,materiales_originales,
                     principio_original,ficha_json,fuente) VALUES (?,?,?,?,?,?,?,?,?)''',
                    (p['id'],p['numero'],p['titulo'],(p['numero']-1)//20+1,p['pagina_pdf'],
                     p['materiales_originales'],p['principio_original'],
                     json.dumps(p,ensure_ascii=False),p['fuente']))
        print('Proyectos del PDF:', con.execute('SELECT COUNT(*) FROM proyectos_unicos_pdf').fetchone()[0])
        print('Se conservaron las ediciones existentes. Propuestas pendientes de revisión.')
    finally:
        con.close()


if __name__ == '__main__':
    importar()
