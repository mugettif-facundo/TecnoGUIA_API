import sqlite3
from pathlib import Path
BASE=Path(__file__).resolve().parent/'tecnoguia.db'
def preparar(base=None):
 ruta=Path(base or BASE)
 if not ruta.is_file():raise RuntimeError('Falta tecnoguia.db. Ejecutá crear_base.py primero.')
 with sqlite3.connect(ruta) as con:
  con.execute('''CREATE TABLE IF NOT EXISTS propuestas_guardadas(id TEXT PRIMARY KEY,titulo TEXT NOT NULL,grado INTEGER NOT NULL CHECK(grado IN (5,6)),creada_en TEXT NOT NULL,guia_json TEXT NOT NULL)''')
  print('Guardado de propuestas disponible; los registros existentes se conservaron.')
if __name__=='__main__':preparar()
