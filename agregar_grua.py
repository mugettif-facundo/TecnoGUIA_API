import json,sqlite3
from pathlib import Path
CARPETA=Path(__file__).resolve().parent

def agregar(base=None):
 ruta=Path(base or CARPETA/'tecnoguia.db')
 if not ruta.is_file():raise RuntimeError('Falta tecnoguia.db.')
 a=json.loads((CARPETA/'grua_manual.json').read_text(encoding='utf-8'))
 with sqlite3.connect(ruta) as con:
  con.execute('PRAGMA foreign_keys=ON')
  if not con.execute("SELECT 1 FROM sqlite_master WHERE name='nap_contenidos'").fetchone():raise RuntimeError('Ejecutá asociar_nap.py primero.')
  con.execute('''CREATE TABLE IF NOT EXISTS guias_nap(id TEXT PRIMARY KEY,contenido_id TEXT NOT NULL REFERENCES nap_contenidos(id),titulo TEXT NOT NULL,duracion_minima INTEGER NOT NULL,alumnos_por_grupo INTEGER NOT NULL,materiales_json TEXT NOT NULL,guia_json TEXT NOT NULL,estado TEXT NOT NULL,origen TEXT NOT NULL)''')
  con.execute('INSERT OR IGNORE INTO guias_nap VALUES (?,?,?,?,?,?,?,?,?)',(a['id'],a['contenido_id'],a['titulo'],a['duracion_minima'],a['alumnos_por_grupo'],json.dumps(a['materiales'],ensure_ascii=False),json.dumps(a['guia'],ensure_ascii=False),a['estado'],a['origen']))
  v=dict(contenido_id='N52',tipo='guia',recurso_id='A05',justificacion='El eje y el carretel giran juntos; las guías sostienen el eje y permiten su giro.',consigna_enfoque='Explicar cómo la manivela convierte el giro en ascenso y descenso de la carga.',evidencia='Boceto, pruebas y explicación de piezas móviles y fijas.',estado='propuesta_pendiente_revision')
  con.execute('INSERT OR IGNORE INTO nap_vinculos VALUES (?,?,?,?)',('N52','guia','A05',json.dumps(v,ensure_ascii=False)))
  print('A05 disponible en 5.º → Medios técnicos → Mecanismos y movimientos. Se conservaron las ediciones existentes.')
if __name__=='__main__':agregar()
