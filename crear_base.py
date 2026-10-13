"""Inicializa TecnoGUIA sin borrar registros ni reemplazar ediciones previas."""
import json
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent / "tecnoguia.db"

CONTENIDOS = [
    ("C01", 5, "Estructuras", "SL", 262, 262, "Comparar estructuras permite relacionar la disposición de sus elementos con los esfuerzos que soportan.", ["estructuras", "construcción de estructuras", "estructuras resistentes"]),
    ("C02", 5, "Operaciones y transporte", "SL", 262, 262, "En actividades de recolección, transporte y distribución se pueden reconocer operaciones que se repiten en procesos distintos.", ["operaciones", "transporte", "distribución"]),
    ("C03", 5, "Energía en los procesos", "NAP", 72, 74, "Al transformar materiales se utiliza energía para realizar operaciones como mezclar o modificar su temperatura.", ["energía", "transformación de materiales"]),
    ("C04", 5, "Secuencia de operaciones", "SL", 263, 263, "Las operaciones de un proceso pueden organizarse una después de otra o realizarse al mismo tiempo.", ["secuencia", "operaciones sucesivas", "operaciones simultáneas"]),
    ("C05", 5, "Producción en serie", "SL", 263, 263, "Producir muchas unidades semejantes requiere reorganizar las tareas respecto de la elaboración de una sola unidad.", ["producción en serie", "organización del trabajo"]),
    ("C06", 5, "Representación técnica", "SL", 263, 263, "Los instructivos y las representaciones gráficas permiten comunicar cómo se realiza un proceso tecnológico.", ["instructivos", "representación técnica"]),
    ("C07", 6, "Producción de energía", "SL", 325, 325, "El análisis de la generación de energía permite comparar modos de producción y su aprovechamiento en diferentes contextos.", ["producción de energía", "generación de energía"]),
    ("C08", 6, "Control de procesos", "SL", 325, 325, "En los procesos que actúan sobre materiales o energía se pueden identificar operaciones destinadas a controlar su realización.", ["control", "control de procesos"]),
    ("C09", 6, "Dependencia entre operaciones", "NAP", 76, 78, "Las relaciones entre tareas sucesivas y simultáneas influyen en el tiempo total y en los efectos de una demora.", ["dependencia", "tareas sucesivas", "tareas simultáneas"]),
    ("C10", 6, "Línea de producción", "NAP", 76, 78, "Una simulación de producción permite distribuir tareas, recursos y puestos considerando el tiempo total.", ["línea de producción", "puestos", "distribución de tareas"]),
    ("C11", 6, "Calidad y desperdicios", "NAP", 76, 78, "En una producción se revisan la calidad, la cantidad obtenida y los desperdicios del proceso.", ["calidad", "desperdicios"]),
    ("C12", 6, "Diagramas de procesos", "SL", 325, 325, "Los diagramas y gráficos ayudan a comunicar el orden de las operaciones y la organización del trabajo.", ["diagramas", "diagramas de procesos"]),
    ("C13", 6, "Gestión de información técnica", "NAP", 77, 79, "Las tecnologías de información permiten buscar, organizar, conservar y comunicar contenidos vinculados con un proceso.", ["información técnica", "gestión de información"]),
]

ESQUEMA = """
CREATE TABLE IF NOT EXISTS documentos (
    id TEXT PRIMARY KEY,
    titulo TEXT NOT NULL,
    organismo TEXT NOT NULL,
    anio INTEGER,
    estado TEXT NOT NULL DEFAULT 'pendiente_cotejo',
    archivo_original TEXT
);
CREATE TABLE IF NOT EXISTS contenidos (
    id TEXT PRIMARY KEY,
    grado INTEGER NOT NULL CHECK (grado IN (5, 6)),
    eje TEXT NOT NULL CHECK (eje = 'Procesos tecnológicos'),
    titulo TEXT NOT NULL,
    documento_id TEXT NOT NULL REFERENCES documentos(id),
    pagina_impresa INTEGER NOT NULL CHECK (pagina_impresa > 0),
    pagina_pdf INTEGER NOT NULL CHECK (pagina_pdf > 0),
    sintesis TEXT NOT NULL,
    tipo_texto TEXT NOT NULL DEFAULT 'parafrasis_tfg',
    terminos_json TEXT NOT NULL,
    verificado INTEGER NOT NULL DEFAULT 0 CHECK (verificado IN (0, 1)),
    origen_registro TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS actividades (
    id TEXT PRIMARY KEY,
    contenido_id TEXT NOT NULL REFERENCES contenidos(id),
    titulo TEXT NOT NULL,
    duracion_minima INTEGER NOT NULL CHECK (duracion_minima > 0),
    alumnos_por_grupo INTEGER NOT NULL CHECK (alumnos_por_grupo > 0),
    materiales_json TEXT NOT NULL,
    guia_json TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'borrador',
    origen TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_contenidos_grado ON contenidos(grado);
CREATE INDEX IF NOT EXISTS idx_actividades_contenido ON actividades(contenido_id);
"""

GUIA_TORRE = {
    "objetivos": [
        "Construir una estructura que se mantenga de pie.",
        "Relacionar la base y las uniones con la estabilidad."
    ],
    "preparacion_docente": [
        "Preparar cuatro hojas por grupo y cinta adhesiva.",
        "Probar previamente el armado y despejar las mesas."
    ],
    "consigna": "Construyan una torre que permanezca de pie sin sujetarla durante 20 segundos.",
    "etapas": [
        {"nombre": "Exploración", "minutos": 10, "acciones": ["Conversar sobre qué hace estable una torre.", "Distribuir las tareas del grupo."]},
        {"nombre": "Construcción", "minutos": 30, "acciones": ["Reservar una hoja para la base.", "Enrollar las otras tres hojas formando tres tubos.", "Fijar el borde de cada tubo con cinta.", "Colocar los tubos de pie formando un triángulo.", "Unir los tubos entre sí con pequeños tramos de cinta.", "Apoyarlos sobre la hoja base y fijarlos a ella."]},
        {"nombre": "Prueba y mejora", "minutos": 15, "acciones": ["Soltar la torre y contar 20 segundos en voz alta.", "Revisar la base y las uniones si se cae.", "Modificar el armado y repetir la prueba."]},
        {"nombre": "Cierre", "minutos": 5, "acciones": ["Explicar qué modificación mejoró la estabilidad."]}
    ],
    "explicacion": "La disposición de los elementos y las uniones influye en la estabilidad. La prueba permite revisar el diseño; no mide por sí sola la resistencia a cargas.",
    "seguridad": ["Trabajar sobre mesas, sin subirse a muebles.", "No colocar objetos pesados sobre la torre."],
    "evidencias": ["Estructura construida y prueba de estabilidad.", "Explicación oral de una mejora."],
    "criterios_evaluacion": ["Relaciona base y uniones con la estabilidad.", "Prueba y propone mejoras.", "Explica sus decisiones."],
    "avisos": ["Confirmar las cantidades de materiales.", "Actividad de demostración pendiente de revisión docente; cotejar su relación con C01 antes de la evaluación formal."]
}


def crear_base():
    con = sqlite3.connect(BASE)
    try:
        con.execute("PRAGMA foreign_keys = ON")
        con.executescript(ESQUEMA)
        with con:
            con.executemany(
                "INSERT OR IGNORE INTO documentos (id, titulo, organismo, anio) VALUES (?, ?, ?, ?)",
                [
                    ("SL", "Diseño Curricular Jurisdiccional de Educación Primaria, Resolución 005-ME-2019", "Ministerio de Educación de San Luis", 2019),
                    ("NAP", "Núcleos de Aprendizajes Prioritarios, segundo ciclo de Educación Primaria", "Ministerio de Educación de la Nación", None)
                ]
            )
            for cid, grado, titulo, doc, impresa, pdf, sintesis, terminos in CONTENIDOS:
                con.execute(
                    """INSERT OR IGNORE INTO contenidos
                    (id, grado, eje, titulo, documento_id, pagina_impresa, pagina_pdf,
                     sintesis, terminos_json, origen_registro)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (cid, grado, "Procesos tecnológicos", titulo, doc, impresa, pdf,
                     sintesis, json.dumps(terminos, ensure_ascii=False),
                     "Inventario C01–C13 de Mugetti facundo matias - TFG 1.2.docx, pp. 19–20; cotejo con originales pendiente")
                )
            con.execute(
                """INSERT OR IGNORE INTO actividades
                (id, contenido_id, titulo, duracion_minima, alumnos_por_grupo,
                 materiales_json, guia_json, origen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                ("A01", "C01", "Construimos una torre de papel", 60, 5,
                 json.dumps([
                     {"nombre": "papel", "cantidad_por_grupo": 4, "unidad": "hojas"},
                     {"nombre": "cinta adhesiva", "cantidad_por_grupo": None, "unidad": "cantidad a confirmar por el docente"}
                 ], ensure_ascii=False), json.dumps(GUIA_TORRE, ensure_ascii=False),
                 "Plantilla de demostración desarrollada durante la creación de la API; pendiente de validación docente")
            )
        print(f"Base disponible: {BASE}")
        for tabla in ("documentos", "contenidos", "actividades"):
            cantidad = con.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
            print(f"{tabla}: {cantidad}")
        print("Los registros existentes se conservaron. Referencias pendientes de cotejo.")
    finally:
        con.close()


if __name__ == "__main__":
    crear_base()
