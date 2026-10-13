"""Agrega relaciones muchos-a-muchos sin sobrescribir revisiones existentes."""
import json,sqlite3
from pathlib import Path
CARPETA=Path(__file__).resolve().parent

def importar(base=None):
 ruta=Path(base or CARPETA/'tecnoguia.db')
 if not ruta.is_file():raise RuntimeError('Ejecutá crear_base.py primero.')
 datos=json.loads((CARPETA/'vinculos_nap.json').read_text(encoding='utf-8'))
 with sqlite3.connect(ruta) as con:
  con.execute('PRAGMA foreign_keys=ON')
  con.executescript('''CREATE TABLE IF NOT EXISTS nap_ejes(id TEXT PRIMARY KEY,nombre TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS nap_contenidos(id TEXT PRIMARY KEY,grado INTEGER NOT NULL CHECK(grado IN (5,6)),eje_id TEXT NOT NULL REFERENCES nap_ejes(id),ficha_json TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS nap_vinculos(contenido_id TEXT NOT NULL REFERENCES nap_contenidos(id),tipo TEXT NOT NULL CHECK(tipo IN ('guia','proyecto')),recurso_id TEXT NOT NULL,ficha_json TEXT NOT NULL,PRIMARY KEY(contenido_id,tipo,recurso_id));''')
  for e in datos['ejes']:con.execute('INSERT OR IGNORE INTO nap_ejes VALUES (?,?)',(e['id'],e['nombre']))
  for c in datos['contenidos']:con.execute('INSERT OR IGNORE INTO nap_contenidos VALUES (?,?,?,?)',(c['id'],c['grado'],c['eje_id'],json.dumps(c,ensure_ascii=False)))
  for v in datos['vinculos']:
   tabla='actividades' if v['tipo']=='guia' else 'proyectos_unicos_pdf'
   if not con.execute(f'SELECT 1 FROM {tabla} WHERE id=?',(v['recurso_id'],)).fetchone():raise RuntimeError('Falta importar el recurso '+v['recurso_id'])
   con.execute('INSERT OR IGNORE INTO nap_vinculos VALUES (?,?,?,?)',(v['contenido_id'],v['tipo'],v['recurso_id'],json.dumps(v,ensure_ascii=False)))
  print('Relaciones NAP disponibles:',con.execute('SELECT COUNT(*) FROM nap_vinculos').fetchone()[0])
if __name__=='__main__':importar()
