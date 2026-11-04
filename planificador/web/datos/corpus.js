/* Corpus curricular piloto C01–C13 — Eje Procesos tecnológicos, 5.º y 6.º grado.
   COTEJADO el 18/10/2026 contra los PDF oficiales guardados en la PC:
   - NAP Segundo ciclo (Educación_Primaria_Segundo_Ciclo.pdf): páginas impresas 72–73 (5.º) y 76–77 (6.º);
     la página del PDF es la impresa + 2.
   - Diseño Curricular Jurisdiccional de San Luis, Res. 005-ME-2019 (Diseño Educación Primaria.pdf):
     páginas 262–263 (5.º) y 324–326 (6.º); la página del PDF coincide con la impresa.
   Las síntesis son PARÁFRASIS de trabajo, no citas textuales. «fuentes» lista todos los documentos donde aparece
   el contenido; «documento»/«pagina» indican la fuente principal que se muestra primero.
   Reemplaza a los fragmentos F01–F13 del HTML anterior (ver Matriz F–C en TecnoGuIA_matriz_F_C.xlsx).
   «conceptos»: términos y sinónimos para la búsqueda por coincidencia (sin base vectorial).
   Se edita con el Bloc de notas guardando en UTF-8. */
var TG_DOCUMENTOS = {
  SL: { id: 'SL', titulo: 'Diseño Curricular Jurisdiccional de Educación Primaria (Resolución N.º 005-ME-2019)', organismo: 'Ministerio de Educación de San Luis', anio: 2019,
        url: 'https://sanluis.gov.ar/educacion/disenios-curriculares/' },
  NAP: { id: 'NAP', titulo: 'Núcleos de Aprendizajes Prioritarios. Segundo ciclo de Educación Primaria', organismo: 'Ministerio de Educación de la Nación', anio: null,
         url: 'https://www.educ.ar/recursos/adjuntos/descarga/22424/nap-educacion-primaria-segundo-ciclo?disposition=inline' }
};

var TG_CORPUS = [
  { id: 'C01', grado: 5, titulo: 'Estructuras', documento: 'SL', pagina: 262, verificado: true,
    fuentes: [{ documento: 'SL', pagina: 262, eje: 'Eje 1: procesos tecnológicos' }, { documento: 'NAP', pagina: 72, pagina_pdf: 74, eje: 'En relación con los procesos tecnológicos' }],
    sintesis: 'Comparar estructuras permite relacionar la disposición de sus elementos con los esfuerzos que soportan.',
    conceptos: ['estructura', 'estructuras resistentes', 'resistencia', 'resistente', 'puente', 'columna', 'torre', 'carga', 'soportar', 'esfuerzo', 'triangulación', 'plegado'] },
  { id: 'C02', grado: 5, titulo: 'Operaciones y transporte', documento: 'SL', pagina: 262, verificado: true,
    fuentes: [{ documento: 'SL', pagina: 262, eje: 'Eje 1: procesos tecnológicos' }, { documento: 'NAP', pagina: 72, pagina_pdf: 74, eje: 'En relación con los procesos tecnológicos' }],
    sintesis: 'En actividades de recolección, transporte y distribución se pueden reconocer operaciones que se repiten en procesos distintos.',
    conceptos: ['operaciones', 'transporte', 'transportar', 'traslado', 'trasladar', 'recolección', 'recolectar', 'distribución', 'distribuir', 'recorrer', 'recorrido', 'llevar', 'entrega', 'movimiento de materiales'] },
  { id: 'C03', grado: 5, titulo: 'Energía en los procesos', documento: 'NAP', pagina: 72, verificado: true,
    fuentes: [{ documento: 'NAP', pagina: 72, pagina_pdf: 74, eje: 'En relación con los procesos tecnológicos' }],
    sintesis: 'Al transformar materiales se utiliza energía para realizar operaciones como mezclar o modificar su temperatura.',
    conceptos: ['energía', 'transformación de materiales', 'transformar', 'mezclar', 'calentar', 'temperatura', 'máquina', 'funcionar', 'motor', 'combustible'] },
  { id: 'C04', grado: 5, titulo: 'Secuencia de operaciones', documento: 'SL', pagina: 263, verificado: true,
    fuentes: [{ documento: 'SL', pagina: 263, eje: 'Eje 1: procesos tecnológicos' }, { documento: 'NAP', pagina: 72, pagina_pdf: 74, eje: 'En relación con los procesos tecnológicos' }],
    sintesis: 'Las operaciones de un proceso pueden organizarse una después de otra o realizarse al mismo tiempo.',
    conceptos: ['secuencia', 'operaciones sucesivas', 'operaciones simultáneas', 'sucesivas', 'simultáneas', 'simultáneamente', 'ordenar', 'orden', 'elaboración', 'al mismo tiempo'] },
  { id: 'C05', grado: 5, titulo: 'Producción en serie', documento: 'SL', pagina: 263, verificado: true,
    fuentes: [{ documento: 'SL', pagina: 263, eje: 'Eje 1: procesos tecnológicos' }, { documento: 'NAP', pagina: 72, pagina_pdf: 74, eje: 'En relación con los procesos tecnológicos' }],
    sintesis: 'Producir muchas unidades semejantes requiere reorganizar las tareas respecto de la elaboración de una sola unidad.',
    conceptos: ['producción en serie', 'serie', 'producción', 'fabricar', 'unidades iguales', 'iguales', 'varias unidades', 'repetida', 'artesanal', 'organización del trabajo'] },
  { id: 'C06', grado: 5, titulo: 'Representación técnica', documento: 'SL', pagina: 263, verificado: true,
    fuentes: [{ documento: 'SL', pagina: 263, eje: 'Eje 1: procesos tecnológicos' }, { documento: 'NAP', pagina: 73, pagina_pdf: 75, eje: 'En relación con los procesos tecnológicos' }],
    sintesis: 'Los instructivos y las representaciones gráficas permiten comunicar cómo se realiza un proceso tecnológico.',
    conceptos: ['instructivo', 'instructivos', 'representación técnica', 'representar', 'dibujos', 'dibujar', 'ilustrado', 'pasos de fabricación', 'comunicar', 'gráfico'] },
  { id: 'C07', grado: 6, titulo: 'Producción de energía', documento: 'SL', pagina: 325, verificado: true,
    fuentes: [{ documento: 'SL', pagina: 325, eje: 'Eje 1: procesos tecnológicos' }, { documento: 'NAP', pagina: 76, pagina_pdf: 78, eje: 'En relación con los procesos tecnológicos' }],
    sintesis: 'El análisis de la generación de energía permite comparar modos de producción y su aprovechamiento en diferentes contextos.',
    conceptos: ['producción de energía', 'generación de energía', 'energía', 'generar', 'obtener energía', 'eólica', 'solar', 'hidráulica', 'renovable', 'comunidad', 'aprovechamiento'] },
  { id: 'C08', grado: 6, titulo: 'Control de procesos', documento: 'SL', pagina: 325, verificado: true,
    fuentes: [{ documento: 'SL', pagina: 325, eje: 'Eje 1: procesos tecnológicos' }, { documento: 'NAP', pagina: 76, pagina_pdf: 78, eje: 'En relación con los procesos tecnológicos' }],
    sintesis: 'En los procesos que actúan sobre materiales o energía se pueden identificar operaciones destinadas a controlar su realización.',
    conceptos: ['control', 'control de procesos', 'controles', 'controlar', 'operaciones de control', 'riego', 'sensor', 'automático', 'regular'] },
  { id: 'C09', grado: 6, titulo: 'Dependencia entre operaciones', documento: 'NAP', pagina: 76, verificado: true,
    fuentes: [{ documento: 'NAP', pagina: 76, pagina_pdf: 78, eje: 'En relación con los procesos tecnológicos' }, { documento: 'SL', pagina: 325, eje: 'Eje 1: procesos tecnológicos' }],
    sintesis: 'Las relaciones entre tareas sucesivas y simultáneas influyen en el tiempo total y en los efectos de una demora.',
    conceptos: ['dependencia', 'tareas sucesivas', 'tareas simultáneas', 'tareas paralelas', 'sucesivas', 'paralelas', 'demora', 'retraso', 'tiempo total', 'al mismo tiempo', 'terminar antes'] },
  { id: 'C10', grado: 6, titulo: 'Línea de producción', documento: 'NAP', pagina: 76, verificado: true,
    fuentes: [{ documento: 'NAP', pagina: 76, pagina_pdf: 78, eje: 'En relación con los procesos tecnológicos' }, { documento: 'SL', pagina: 324, eje: 'Orientación pedagógico-didáctica (simulación de producción)' }],
    sintesis: 'Una simulación de producción permite distribuir tareas, recursos y puestos considerando el tiempo total.',
    conceptos: ['línea de producción', 'puestos de trabajo', 'puestos', 'distribución de tareas', 'distribuir tareas', 'producción simulada', 'simulación', 'simulada'] },
  { id: 'C11', grado: 6, titulo: 'Calidad y desperdicios', documento: 'NAP', pagina: 76, verificado: true,
    fuentes: [{ documento: 'NAP', pagina: 76, pagina_pdf: 78, eje: 'En relación con los procesos tecnológicos' }],
    sintesis: 'En una producción se revisan la calidad, la cantidad obtenida y los desperdicios del proceso.',
    conceptos: ['calidad', 'control de calidad', 'desperdicios', 'defectos', 'descartados', 'cantidad producida', 'residuos'] },
  { id: 'C12', grado: 6, titulo: 'Diagramas de procesos', documento: 'SL', pagina: 325, verificado: true,
    fuentes: [{ documento: 'SL', pagina: 325, eje: 'Eje 1: procesos tecnológicos' }, { documento: 'NAP', pagina: 77, pagina_pdf: 79, eje: 'En relación con los procesos tecnológicos' }],
    sintesis: 'Los diagramas y gráficos ayudan a comunicar el orden de las operaciones y la organización del trabajo.',
    conceptos: ['diagrama', 'diagramas de procesos', 'diagrama de operaciones', 'dibujar', 'gráfico', 'orden de las acciones', 'orden de las operaciones', 'representar'] },
  { id: 'C13', grado: 6, titulo: 'Gestión de información técnica', documento: 'NAP', pagina: 77, verificado: true,
    fuentes: [{ documento: 'NAP', pagina: 77, pagina_pdf: 79, eje: 'En relación con los procesos tecnológicos' }, { documento: 'SL', pagina: 326, eje: 'Eje 2: medios técnicos (uso de TIC para la comunicación técnica)' }],
    sintesis: 'Las tecnologías de información permiten buscar, organizar, conservar y comunicar contenidos vinculados con un proceso.',
    conceptos: ['información técnica', 'gestión de información', 'información', 'datos técnicos', 'buscar información', 'conservar'] }
];

if (typeof module !== 'undefined') module.exports = { TG_CORPUS: TG_CORPUS, TG_DOCUMENTOS: TG_DOCUMENTOS };
