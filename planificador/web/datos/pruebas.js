/* Protocolo de pruebas del TFG (Entrega 2).
   Anexo A: 36 consultas de recuperación — 24 directas, 6 paráfrasis, 6 fuera de cobertura.
   "esperado": registros aceptables (C01–C13) o [] cuando debe rechazarse por falta de cobertura.
   Anexo B: comprobaciones funcionales F01–F09 (se ejecutan a mano; la página registra el resultado). */
var TG_PRUEBAS = [
  { id: 'P01', grado: 5, tipo: 'directa',    consulta: 'Comparar dos estructuras de papel por resistencia.', esperado: ['C01'] },
  { id: 'P02', grado: 5, tipo: 'directa',    consulta: 'Construir y analizar un puente liviano con cartón.', esperado: ['C01'] },
  { id: 'P03', grado: 5, tipo: 'directa',    consulta: 'Reconocer operaciones de transporte de materiales en una producción.', esperado: ['C02'] },
  { id: 'P04', grado: 5, tipo: 'directa',    consulta: 'Organizar recolección y distribución de objetos por etapas.', esperado: ['C02'] },
  { id: 'P05', grado: 5, tipo: 'directa',    consulta: 'Describir la energía utilizada para mezclar o calentar materiales.', esperado: ['C03'] },
  { id: 'P06', grado: 5, tipo: 'directa',    consulta: 'Preparar una actividad sobre energía en la transformación de materiales.', esperado: ['C03'] },
  { id: 'P07', grado: 5, tipo: 'directa',    consulta: 'Ordenar operaciones sucesivas en un proceso de elaboración.', esperado: ['C04'] },
  { id: 'P08', grado: 5, tipo: 'directa',    consulta: 'Distinguir tareas que pueden hacerse simultáneamente.', esperado: ['C04'] },
  { id: 'P09', grado: 5, tipo: 'directa',    consulta: 'Simular la producción de una unidad y de varias unidades iguales.', esperado: ['C05'] },
  { id: 'P10', grado: 5, tipo: 'directa',    consulta: 'Comparar organización artesanal y producción repetida.', esperado: ['C05'] },
  { id: 'P11', grado: 5, tipo: 'directa',    consulta: 'Redactar un instructivo ilustrado para un proceso tecnológico.', esperado: ['C06'] },
  { id: 'P12', grado: 5, tipo: 'directa',    consulta: 'Representar mediante dibujos los pasos de fabricación.', esperado: ['C06'] },
  { id: 'P13', grado: 6, tipo: 'directa',    consulta: 'Comparar formas de generación de energía.', esperado: ['C07'] },
  { id: 'P14', grado: 6, tipo: 'directa',    consulta: 'Analizar cómo se obtiene energía para una actividad productiva.', esperado: ['C07'] },
  { id: 'P15', grado: 6, tipo: 'directa',    consulta: 'Reconocer controles en un sistema sencillo de riego.', esperado: ['C08'] },
  { id: 'P16', grado: 6, tipo: 'directa',    consulta: 'Identificar operaciones de control en una actividad productiva.', esperado: ['C08'] },
  { id: 'P17', grado: 6, tipo: 'directa',    consulta: 'Analizar cómo una demora afecta el tiempo total del proceso.', esperado: ['C09'] },
  { id: 'P18', grado: 6, tipo: 'directa',    consulta: 'Comparar tareas sucesivas y paralelas en una elaboración.', esperado: ['C09'] },
  { id: 'P19', grado: 6, tipo: 'directa',    consulta: 'Organizar puestos de trabajo para una pequeña línea de producción.', esperado: ['C10'] },
  { id: 'P20', grado: 6, tipo: 'directa',    consulta: 'Distribuir tareas y recursos en una producción simulada.', esperado: ['C10'] },
  { id: 'P21', grado: 6, tipo: 'directa',    consulta: 'Estudiar desperdicios y control de calidad en un producto.', esperado: ['C11'] },
  { id: 'P22', grado: 6, tipo: 'directa',    consulta: 'Registrar cantidad producida, defectos y materiales descartados.', esperado: ['C11'] },
  { id: 'P23', grado: 6, tipo: 'directa',    consulta: 'Dibujar un diagrama de operaciones para elaborar un objeto.', esperado: ['C12'] },
  { id: 'P24', grado: 6, tipo: 'directa',    consulta: 'Organizar la información técnica que necesita un proceso.', esperado: ['C13'] },
  { id: 'P25', grado: 5, tipo: 'paráfrasis', consulta: '¿Cómo hacemos para que un material recorra varios puestos de trabajo?', esperado: ['C02'] },
  { id: 'P26', grado: 5, tipo: 'paráfrasis', consulta: '¿Qué hace funcionar una máquina cuando transforma algo?', esperado: ['C03'] },
  { id: 'P27', grado: 5, tipo: 'paráfrasis', consulta: '¿Qué cambia si fabricamos diez iguales en vez de uno solo?', esperado: ['C05'] },
  { id: 'P28', grado: 6, tipo: 'paráfrasis', consulta: '¿De dónde viene la energía que usa una comunidad?', esperado: ['C07'] },
  { id: 'P29', grado: 6, tipo: 'paráfrasis', consulta: '¿Cómo organizamos tareas al mismo tiempo para terminar antes?', esperado: ['C09'] },
  { id: 'P30', grado: 6, tipo: 'paráfrasis', consulta: '¿Podemos dibujar el orden de las acciones de un trabajo?', esperado: ['C12'] },
  { id: 'P31', grado: 4, tipo: 'sin cobertura', consulta: 'Construir un puente de cartón para cuarto grado.', esperado: [] },
  { id: 'P32', grado: 7, tipo: 'sin cobertura', consulta: 'Elaborar una línea de producción para séptimo grado.', esperado: [] },
  { id: 'P33', grado: 5, tipo: 'sin cobertura', consulta: 'Analizar recursos poéticos de una canción.', esperado: [] },
  { id: 'P34', grado: 6, tipo: 'sin cobertura', consulta: 'Investigar las causas de la Revolución francesa.', esperado: [] },
  { id: 'P35', grado: 5, tipo: 'sin cobertura', consulta: 'Resolver ecuaciones cuadráticas.', esperado: [] },
  { id: 'P36', grado: 6, tipo: 'sin cobertura', consulta: 'Clasificar células según sus orgánulos.', esperado: [] }
];

/* Casos de generación (objetivo 5): adecuación curricular, contexto y materiales.
   Se ejecutan con Ollama desde la pestaña Pruebas; se registran indicadores automáticos y tiempo. */
var TG_CASOS_GENERACION = [
  { id: 'G01', grado: 5, duracion: 80, estudiantes: 25, dificultad: 'Intermedia', registro: 'C01',
    contenido: 'Comparar dos estructuras de papel por resistencia', materiales: 'hojas de papel, cinta de papel, tijeras, libros',
    contexto: 'En el barrio hay un tanque de agua elevado que los chicos ven todos los días' },
  { id: 'G02', grado: 5, duracion: 80, estudiantes: 25, dificultad: 'Intermedia', registro: 'C05',
    contenido: 'Simular la producción de una unidad y de varias unidades iguales', materiales: 'cartulina, tijeras, reglas, lápices de colores',
    contexto: '' },
  { id: 'G03', grado: 5, duracion: 40, estudiantes: 18, dificultad: 'Inicial', registro: 'C02',
    contenido: 'Reconocer operaciones de transporte de materiales en una producción', materiales: 'cajas chicas, hilo, tapitas, cinta de papel',
    contexto: 'Escuela rural; muchas familias trabajan en huertas y venden en ferias' },
  { id: 'G04', grado: 6, duracion: 80, estudiantes: 25, dificultad: 'Intermedia', registro: 'C07',
    contenido: 'Comparar formas de generación de energía', materiales: 'cartón, sorbetes, palitos de madera, tijeras, cinta de papel',
    contexto: 'Les interesa el viento; en la provincia hay parques eólicos' },
  { id: 'G05', grado: 6, duracion: 80, estudiantes: 28, dificultad: 'Avanzada', registro: 'C10',
    contenido: 'Organizar puestos de trabajo para una pequeña línea de producción', materiales: 'hojas de papel, lápices',
    contexto: '' },
  { id: 'G06', grado: 6, duracion: 120, estudiantes: 22, dificultad: 'Intermedia', registro: 'C12',
    contenido: 'Dibujar un diagrama de operaciones para elaborar un objeto', materiales: 'hojas de papel, lápices de colores, reglas',
    contexto: 'Los chicos preparan pan en la escuela para la feria de ciencias' }
];

var TG_PRUEBAS_FUNCIONALES = [
  { id: 'F01', caso: 'Guardar actividad propia A-N01 con autoría, materiales, procedimiento y contexto.', esperado: 'La actividad aparece identificada en el banco local.' },
  { id: 'F02', caso: 'Cerrar y reabrir el navegador; buscar A-N01.', esperado: 'La actividad sigue disponible en el mismo navegador y equipo.' },
  { id: 'F03', caso: 'Generar un borrador utilizando A-N01 y un registro curricular.', esperado: 'El sistema recupera y muestra las fuentes utilizadas.' },
  { id: 'F04', caso: 'Ingresar un formulario sin grado o contenido obligatorio.', esperado: 'Se solicita completar datos antes de generar.' },
  { id: 'F05', caso: 'Usar una consulta sin cobertura del corpus.', esperado: 'Se advierte falta de fuente; no se atribuye respaldo inexistente.' },
  { id: 'F06', caso: 'Detener Ollama e intentar generar.', esperado: 'Se informa que el servicio no está disponible.' },
  { id: 'F07', caso: 'Desconectar Internet y repetir un caso válido.', esperado: 'La interfaz y el modelo funcionan con recursos locales, si están correctamente instalados.' },
  { id: 'F08', caso: 'Modificar el borrador y registrar una actividad derivada propia.', esperado: 'Se conserva la edición y procedencia cuando el docente decide guardarla.' },
  { id: 'F09', caso: 'Borrar datos del navegador en entorno controlado y comprobar persistencia.', esperado: 'Se documenta la pérdida potencial de datos y la limitación del almacenamiento local.' }
];

/* Anexo D: valoración exploratoria docente (1 a 5 o «No puedo valorarlo»). */
var TG_VALORACION = [
  { id: 'V01', criterio: 'La interfaz permite completar los datos sin dificultad.' },
  { id: 'V02', criterio: 'Los contenidos y fuentes mostrados corresponden al grado y tema solicitados.' },
  { id: 'V03', criterio: 'La consigna y los pasos son claros para preparar la clase.' },
  { id: 'V04', criterio: 'La actividad puede realizarse con los materiales y el tiempo declarados.' },
  { id: 'V05', criterio: 'La propuesta considera el contexto y los intereses indicados por el docente.' },
  { id: 'V06', criterio: 'Las indicaciones de seguridad y los criterios de evaluación son suficientes para revisar la propuesta.' },
  { id: 'V07', criterio: 'El borrador sirve como punto de partida, aunque necesite modificaciones.' },
  { id: 'V08', criterio: 'Guardar y recuperar una actividad propia resulta comprensible y útil.' }
];
var TG_PREGUNTAS_ABIERTAS = ['¿Qué cambiaría antes de aplicar esta actividad?', '¿Qué materiales faltan?',
  '¿De qué fuente necesitaría comprobar más información?', '¿Qué actividad propia desearía registrar?'];

if (typeof module !== 'undefined') module.exports = { TG_PRUEBAS: TG_PRUEBAS, TG_PRUEBAS_FUNCIONALES: TG_PRUEBAS_FUNCIONALES,
  TG_CASOS_GENERACION: TG_CASOS_GENERACION, TG_VALORACION: TG_VALORACION, TG_PREGUNTAS_ABIERTAS: TG_PREGUNTAS_ABIERTAS };
