"""Importa guías adicionales y sus vínculos sin reemplazar ediciones."""
import json,sqlite3
from pathlib import Path
CARPETA=Path(__file__).resolve().parent

def agregar(base=None):
 ruta=Path(base or CARPETA/'tecnoguia.db')
 if not ruta.is_file():raise RuntimeError('Falta tecnoguia.db.')
 actividades=json.loads((CARPETA/'guias_nuevas_nap.json').read_text(encoding='utf-8'))
 with sqlite3.connect(ruta) as con:
  con.execute('PRAGMA foreign_keys=ON')
  if not con.execute("SELECT 1 FROM sqlite_master WHERE name='nap_contenidos'").fetchone():raise RuntimeError('Ejecutá asociar_nap.py primero.')
  con.execute('''CREATE TABLE IF NOT EXISTS guias_nap(id TEXT PRIMARY KEY,contenido_id TEXT NOT NULL REFERENCES nap_contenidos(id),titulo TEXT NOT NULL,duracion_minima INTEGER NOT NULL,alumnos_por_grupo INTEGER NOT NULL,materiales_json TEXT NOT NULL,guia_json TEXT NOT NULL,estado TEXT NOT NULL,origen TEXT NOT NULL)''')
  for a in actividades:
   con.execute('INSERT OR IGNORE INTO guias_nap VALUES (?,?,?,?,?,?,?,?,?)',(a['id'],a['contenido_id'],a['titulo'],a['duracion_minima'],a['alumnos_por_grupo'],json.dumps(a['materiales'],ensure_ascii=False),json.dumps(a['guia'],ensure_ascii=False),a['estado'],a['origen']))
   for v in [a['vinculo'],*a.get('vinculos_adicionales',[])]:
    if v['tipo']=='proyecto' and not con.execute('SELECT 1 FROM proyectos_unicos_pdf WHERE id=?',(v['recurso_id'],)).fetchone():raise RuntimeError('Falta importar '+v['recurso_id'])
    con.execute('INSERT OR IGNORE INTO nap_vinculos VALUES (?,?,?,?)',(v['contenido_id'],v['tipo'],v['recurso_id'],json.dumps(v,ensure_ascii=False)))
   print(a['id']+' disponible: '+a['titulo'])
  print('Se conservaron las ediciones existentes.')
if __name__=='__main__':agregar()
