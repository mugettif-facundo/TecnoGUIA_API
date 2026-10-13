"""Agrega nuevas actividades sin reemplazar las existentes."""
import json
import sqlite3
from pathlib import Path

CARPETA = Path(__file__).resolve().parent


def agregar(base=None):
    base = Path(base) if base else CARPETA / 'tecnoguia.db'
    if not base.is_file():
        raise RuntimeError('Falta la base inicial tecnoguia.db en esta carpeta.')
    actividades = json.loads((CARPETA / 'actividades_nuevas.json').read_text(encoding='utf-8'))
    con = sqlite3.connect(base)
    try:
        con.execute('PRAGMA foreign_keys = ON')
        with con:
            for actividad in actividades:
                con.execute('''INSERT OR IGNORE INTO actividades
                    (id, contenido_id, titulo, duracion_minima, alumnos_por_grupo,
                     materiales_json, guia_json, estado, origen)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (actividad['id'], actividad['contenido_id'], actividad['titulo'],
                     actividad['duracion_minima'], actividad['alumnos_por_grupo'],
                     json.dumps(actividad['materiales'], ensure_ascii=False),
                     json.dumps(actividad['guia'], ensure_ascii=False), 'borrador',
                     'Propuesta nueva creada para TecnoGUIA; pendiente de revisión docente y curricular'))
        print('Actividades disponibles:')
        for fila in con.execute('''SELECT a.id, c.grado, a.titulo FROM actividades a
                                  JOIN contenidos c ON c.id=a.contenido_id ORDER BY a.id'''):
            print(f'{fila[0]} | {fila[1]}.º | {fila[2]}')
        print('No se reemplazaron registros existentes.')
    finally:
        con.close()


if __name__ == '__main__':
    agregar()
