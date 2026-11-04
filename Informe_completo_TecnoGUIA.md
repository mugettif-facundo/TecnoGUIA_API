# TecnoGUIA — Informe técnico completo (versión 0.8, 13/10/2026)

> Documento de traspaso para que otra persona o IA pueda continuar el desarrollo. Describe todo lo programado hasta hoy, cómo se ejecuta, la base de datos, la API, la IA, los controles, las pruebas, los resultados reales y lo pendiente.

## 1. Qué es y para quién

**TecnoGUIA** es una aplicación web local que ayuda a docentes de **Educación Tecnológica de 5.º y 6.º grado (Argentina)** a preparar actividades alineadas con los **NAP** (Núcleos de Aprendizaje Prioritarios, Educación Primaria, Segundo Ciclo, páginas impresas 73 a 80).

- Es el **Trabajo Final de Grado (TFG)** de un docente de **La Punta, San Luis**.
- Corre **todo en la PC del docente**, sin servicios pagos ni claves de API: FastAPI + SQLite + IA local con **Ollama** (modelo `qwen3:1.7b`).
- **Principio del proyecto:** distinguir siempre lo comprobado de lo supuesto. La IA no inventa materiales ni datos locales, todo borrador lleva avisos y requiere revisión docente, y nada se presenta como "validado".

**Tres modos de uso en el formulario:**
1. **Generar una actividad nueva con IA** (modo principal): grado + eje + contenido NAP + tema + materiales disponibles → borrador completo.
2. **Buscar una guía existente:** filtra 8 guías desarrolladas por contenido, materiales, tiempo y modalidad. La adaptación es determinística, sin IA.
3. **Adaptar con IA local** una guía existente: la IA solo reescribe objetivos y agrega preguntas y orientaciones; el montaje no cambia.

Además hay un **banco de 100 fichas de proyectos** tomadas de un PDF, como ideas pendientes de desarrollar.

## 2. Instalación y ejecución (Windows)

- Carpeta: `C:\Users\MakerCompetencia\TecnoGUIA_API`
- Python 3.13 en el entorno virtual `.venv`. Dependencias: `fastapi`, `uvicorn`, `pydantic` v2 (y `httpx` solo para el TestClient). No hay `requirements.txt`; conviene crearlo.
- Ollama para Windows con `ollama pull qwen3:1.7b`. Se consulta solo en `http://127.0.0.1:11434`.

**Arranque en PowerShell** (no usar `cd /d`, que es de CMD):
```
cd C:\Users\MakerCompetencia\TecnoGUIA_API
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```
Formulario: `http://127.0.0.1:8000/formulario` (recargar con Ctrl+F5). Documentación automática: `http://127.0.0.1:8000/docs`.

**Modelo alternativo:** variable `TECNOGUIA_MODELO` (por ejemplo `qwen3:4b`) antes de iniciar Uvicorn.

**Creación de la base desde cero** (scripts idempotentes, que no pisan ediciones), en este orden:
`crear_base.py` → `importar_actividades.py` → `agregar_actividades.py` → `importar_unicos.py` → `asociar_nap.py` → `agregar_grua.py` → `agregar_guias_nap.py` → `preparar_guardado.py`.

**Git:** hay un repositorio en la carpeta (rama `fix/leeme-errata`; commits `be54b6c` "Versión inicial (0.7.1)" y `7b5b836`). `.gitignore` excluye `.venv/`, `__pycache__/`, `*.db`, `evaluaciones/` y `evaluacion_log.txt`. **Los cambios de la 0.8 todavía no tienen commit.**

## 3. Archivos

### Código principal
| Archivo | Función |
| --- | --- |
| `main.py` | API FastAPI: rutas, modelos de entrada y guardado de propuestas |
| `motor.py` | Catálogo, búsqueda y adaptación determinística de guías (sin IA). Utilidades `normalizar`, `abrir_base` (SQLite solo lectura) |
| `ia_local.py` | Cliente HTTP de Ollama (`consultar`, `estado`), semáforo de un turno (`TURNO`), modo "adaptar guía" (`adaptar`) |
| `ia_generadora.py` | Generación completa con IA: esquema de salida, prompt, contexto, reparaciones y controles de calidad |
| `formulario_multi.html` | Interfaz completa (HTML + JS sin framework): formulario, resultado, editor, guardado, impresión y descarga .txt |
| `formulario.html` | Formulario viejo (sin uso) |
| `main.bat` | Restos de una primera API de prueba (sin uso) |

### Datos (JSON, editables con el Bloc de notas en UTF-8)
| Archivo | Contenido |
| --- | --- |
| `orientaciones_contenido.json` | Ficha didáctica por cada uno de los 12 contenidos (ver 6.3) |
| `contexto_local.json` | Lugar de la escuela y referencias locales verificadas (ver 6.5) |
| `materiales_catalogo.json` | 249 materiales y herramientas (`id`, `nombre`, `categoria`, `alias`) |
| `vinculos_nap.json` | Ejes, 12 contenidos y 52 vínculos contenido ↔ guía o proyecto |
| `catalogo_original.json`, `actividades_nuevas.json`, `grua_manual.json`, `guias_nuevas_nap.json` | Guías A01 a A08 y material de origen |
| `proyectos_unicos.json`, `proyectos_pdf.json` | Banco de 100 proyectos del PDF (y versión anterior) |

### Utilidades
| Archivo | Función |
| --- | --- |
| `comprobar_ia.py` | Verifica que Ollama esté abierto y que el modelo esté descargado |
| `diagnosticar_ia.py` | Dos respuestas cortas: tiempo de carga, velocidad y CPU/GPU (`ollama ps`) |
| `evaluar_casos.py` | Corre casos fijos con Ollama real y deja JSON + `planilla_docente.csv` en `evaluaciones\<fecha>_<modelo>\` |
| `reparar_acentos.py` | Repara mojibake (`Ã³` → `ó`) en la base, con respaldo y opciones `--simular` e `--incluir-propuestas` |
| `pruebas/test_generador.py` | 18 pruebas unitarias con Ollama simulado |

### Documentación existente
`LEEME.txt` (historial completo de versiones), `ACTIVAR_IA.txt`, `CAMBIOS_0.7.txt`, `CAMBIOS_0.7.1.txt`, `CAMBIOS_0.8.txt`, `Guia_A06.txt`, `Guia_A07.txt`, `Guia_A08.txt`, `Guia_grua_manual.txt`, `Informe_traspaso_0.8.md` (resumen de una página).

## 4. Base de datos SQLite (`tecnoguia.db`)

| Tabla | Filas | Uso |
| --- | --- | --- |
| `nap_ejes(id, nombre)` | 3 | PT Procesos tecnológicos, MT Medios técnicos, RS Tecnología y sociedad |
| `nap_contenidos(id, grado, eje_id, ficha_json)` | 12 | Contenidos curriculares (los usa el generador IA) |
| `nap_vinculos(contenido_id, tipo, recurso_id, ficha_json)` | 52 | Relación muchos a muchos contenido ↔ guía o proyecto, con justificación, consigna de enfoque y evidencia |
| `guias_nap(...)` | 4 | Guías A05 a A08 vinculadas a contenidos NAP |
| `actividades(...)` | 4 | Guías A01 a A04 (primer catálogo) |
| `contenidos`, `documentos` | 13 / 2 | Inventario curricular del primer flujo |
| `guias_originales`, `fragmentos_originales`, `guia_fragmento_original` | 12 / 13 / 13 | Importación del HTML original |
| `proyectos_unicos_pdf(...)` | 100 | Banco de proyectos del PDF (título, materiales, principio, página) |
| `propuestas_guardadas(id, titulo, grado, creada_en, guia_json)` | 2 | Propuestas editadas y guardadas por el docente |

**`ficha_json` de un contenido:** `id, grado, eje_id, titulo, sintesis, pagina_impresa, pagina_pdf, fuente_url, tipo_texto, referencia_cotejada, actividades`.

**Los 12 contenidos:**

| ID | Grado | Eje | Título |
| --- | --- | --- | --- |
| N51 | 5 | PT | Transporte y distribución |
| N55 | 5 | PT | Producción en serie |
| N56 | 5 | PT | Comunicación del procedimiento |
| N57 | 5 | PT | Resistencia de estructuras |
| N52 | 5 | MT | Mecanismos y movimientos |
| N53 | 5 | MT | Almacenamiento de energía |
| N54 | 5 | RS | Herramientas y máquinas |
| N61 | 6 | PT | Generación de energía |
| N65 | 6 | PT | Representación de procesos |
| N62 | 6 | MT | Control manual y automático |
| N63 | 6 | MT | Diseño de máquinas |
| N64 | 6 | RS | Cambios en el control |

**Guías desarrolladas (borradores):** A01 Torre de papel · A02 Pequeña fábrica de tarjetas · A03 Instructivo que otro grupo pueda seguir · A04 Del procedimiento al diagrama · A05 Grúa de hilo con manivela (N52) · A06 Pinza extendida (N52) · A07 Barco con banda elástica (N53) · A08 Clasificador de fichas por tamaño (N63).

**Debilidad conocida:** casi todo está dentro de columnas `*_json`, lo que impide consultar o medir. Por ejemplo, no se puede saber cuántas propuestas de N61 se desviaron ni cuál fue la calificación docente.

## 5. API (`main.py`)

| Método y ruta | Qué hace |
| --- | --- |
| `GET /` | Estado: "API conectada a SQLite" |
| `GET /formulario` | Sirve `formulario_multi.html` |
| `GET /catalogo?grado=` | Guías A01 a A08 con materiales y modalidades |
| `GET /proyectos` | Banco de 100 proyectos |
| `GET /curriculo?grado=` | Ejes y contenidos con sus actividades vinculadas |
| `GET /materiales` | Catálogo de 249 recursos |
| `POST /actividades/buscar` | Guías compatibles con contenido, materiales, tiempo y modalidad, con los motivos de las descartadas |
| `POST /actividades/generar` | Adapta una guía del catálogo a tiempo, alumnos y modalidad, sin IA (`motor.generar`) |
| `GET /ia/estado` | Comprueba Ollama y el modelo |
| `POST /actividades/generar-ia` | Guía del catálogo + IA que reescribe objetivos, preguntas y orientaciones (`ia_local.adaptar`) |
| `POST /actividades/crear-ia` | **Generación completa con IA** (`ia_generadora.generar`), espera de hasta 600 s |
| `POST /propuestas` | Guarda una propuesta editada (valida tiempos y, si es IA, su origen curricular) |
| `GET /propuestas`, `GET /propuestas/{id}` | Lista y recupera propuestas guardadas |

Errores: `422` para pedidos inválidos (contenido de otro grado, materiales mal separados, localidad inexistente), `429` si ya hay una generación en curso, `502` si el modelo devuelve algo inutilizable, `504` por tiempo agotado.

## 6. Generación completa con IA (`ia_generadora.py`)

### 6.1 Pedido (`PedidoGeneracion`)
`grado` (5 o 6), `contenido_nap_id`, `tema`, `duracion_minutos`, `cantidad_alumnos`, `alumnos_por_grupo` (por defecto 4), `conocimientos_previos`, `modalidad` (individual, parejas o grupos), `dificultad` (inicial, intermedia o avanzada), `materiales[]` (cada uno `{nombre | id, cantidad|null, unidad}`), y los opcionales `localidad` y `contexto_escuela` (el formulario no los envía).

### 6.2 Flujo de `generar()`
1. `recuperar()`: ficha del contenido desde SQLite, comprobando que corresponda al grado.
2. `orientacion_para()`: ficha didáctica del contenido (`orientaciones_contenido.json`).
3. `referencias_locales()`: referencias verificadas del lugar de la escuela para ese contenido.
4. `preparar_recursos()`: asigna IDs `L001`, `L002`, etc., y detecta listas mal separadas ("carton motores" → error 422 sin llamar al modelo). Si hay silicona caliente sin pistola, la excluye y avisa.
5. `unidades_trabajo()`: cantidad de grupos, por ejemplo 25 alumnos en grupos de 4 → 7 unidades.
6. `construir_instrucciones()` (prompt de sistema) + `construir_contexto()` (JSON del usuario: pedido, contenido curricular, recursos disponibles, contexto local si hay y, **al final**, la orientación del contenido, porque los modelos chicos atienden mejor a lo último).
7. `consultar_modelo()`: `/api/chat` con `format` = esquema JSON de Pydantic, `think:false`, `temperature 0.3`, `num_ctx 8192`, `num_predict 5000` y `keep_alive 10m`. Un solo turno a la vez.
8. Controles posteriores (6.4). Corrigen lo seguro y avisan el resto, sin descartar una generación de varios minutos.
9. Armado de la propuesta para el editor.

### 6.3 Esquema de salida (`ActividadIA`): el orden importa
Ollama obliga al modelo a escribir los campos en este orden, y eso funciona como planificación inversa:
`titulo` → `plan {producto_o_proceso, [conexion_local], relacion_con_contenido, que_se_observa, alcance}` → `prueba_final {procedimiento, criterio_exito, recursos[]}` → `objetivos` → `justificacion_curricular` → `materiales[] {id, cantidad, distribucion: por_unidad_trabajo|compartido, detalle}` → `preparacion_docente` → `consigna` → `etapas[] {nombre, minutos, acciones[] {descripcion, recursos[]}}` → `explicacion`, `seguridad`, `evidencias`, `criterios_evaluacion`, `preguntas_docentes`, `orientaciones`, `problemas_frecuentes[] {problema, revision, correccion}`.

Cuando hay una referencia local se usa `ActividadIALocal`, cuyo `plan` (`PlanLocal`) agrega el campo obligatorio `conexion_local`.

**`orientaciones_contenido.json`** (versión 2026-10-10.1, propuesta pendiente de revisión docente) trae por contenido: `foco`, `requiere_construccion`, `la_prueba_debe_mostrar`, `ideas_de_producto`, `objetivos_ejemplo`, `evitar` y `palabras_clave`. Este último no se envía a la IA: se usa para detectar desvíos.

### 6.4 Controles y reparaciones
| Función | Qué hace |
| --- | --- |
| `reparar_recursos` | Quita IDs inventados, agrega a materiales los recursos que usan los pasos y avisa si se pide más de lo disponible |
| `revisar_recursos_en_texto` | Avisa si el texto menciona pegamento, tijeras, regla, lápiz, pesas, pilas o cables no declarados, y si hay una carga sin identificar |
| `reforzar_silicona` | Con silicona caliente y pistola, agrega uso exclusivo del docente y enfriamiento, y quita negaciones de calor |
| `distribuir_tiempos` | Si los minutos no suman el total, reparte proporcionalmente (mínimo 1 por etapa) y lo registra |
| `revisar_pertinencia` | Busca `palabras_clave` del contenido en plan, objetivos y prueba. Marca desvíos, por ejemplo una actividad de energía que solo evalúa estabilidad |
| `revisar_uso_local` | Observación si la IA no usó la referencia local enviada |
| `validar_salida` | Integridad final (tiempos y recursos coherentes) |

Los problemas graves van a `control_calidad.revision_obligatoria` y se muestran con el prefijo **ATENCIÓN** en un recuadro "Revisión obligatoria antes de usar". Los leves van a `observaciones`. La salida original del modelo se guarda en `ia.salida_cruda`. Además se registran `version_prompt` (hoy `2026-10-12.2`) y `version_orientaciones`.

### 6.5 Contexto local automático (versión 0.8)
- En `contexto_local.json`, `"localidad_escuela": "San Luis"` se aplica sola, sin campos en el formulario.
- Solo se envían referencias con `"verificada": true` y cuyo `contenidos` incluya el contenido elegido.
- Hoy hay dos referencias:
  - **SL-01**, Parque Eólico San Luis Norte en Toro Negro, para N61. Verificada.
  - **SL-02**, seguidores solares de la planta de Toro Negro, para N62. No verificada, así que no se usa.
- **Por qué no se busca en Internet:** el modelo de 1.7B no puede buscar y, si se le pide contexto de San Luis, inventa lugares.
- **Por qué el campo es obligatorio:** en la prueba real, una instrucción suelta fue ignorada. Con `conexion_local` en el esquema, la IA sí usó la referencia.
- La propuesta guarda `contexto_local {localidad, contexto_escuela, version, referencias[{id, referencia, fuente}]}`, que se muestra en pantalla, en la impresión y en el .txt.

### 6.6 Propuesta devuelta
`id` (`IA-<uuid>`), `titulo`, `grado`, `duracion_minutos`, `objetivos`, `preparacion_docente`, `consigna`, `explicacion`, `seguridad`, `evidencias`, `criterios_evaluacion`, `etapas`, `ajuste_tiempos`, `prueba_final`, `plan_ia`, `justificacion_curricular`, `problemas_frecuentes`, `organizacion`, `materiales_por_grupo` (texto con cantidad por unidad y total), `recursos_utilizados`, `solicitud_generacion`, `contexto_clase`, `contexto_local`, `aporte_ia`, `avisos`, `fuente` (documento NAP y página), `control_calidad` e `ia` (modelo, tiempos, salida cruda y ficha recuperada).

## 7. Formulario (`formulario_multi.html`)
- Selectores de grado, eje y contenido (desde `/curriculo`), con la síntesis y el enlace al documento oficial de los NAP.
- **Modo IA:** tema, materiales en texto libre separados por coma, punto y coma o línea (muestra cómo los interpreta), conocimientos previos, modalidad, dificultad, alumnos por grupo, minutos y cantidad de alumnos. Botones "Comprobar IA local" y "Generar actividad con IA", con reloj de espera de hasta 620 s.
- **Resultado:** recuadro de revisión obligatoria, plan (con "Conexión con el lugar"), objetivos, materiales, etapas, prueba, seguridad, problemas frecuentes y avisos.
- **Editor:** se pueden editar todos los campos. "Actualizar vista previa", "Guardar como nueva propuesta" (`POST /propuestas`), "Mis propuestas guardadas", "Ver versión para imprimir / guardar PDF" y "Descargar guía en texto".
- **Modo catálogo:** búsqueda por materiales y "Preparar guía". Banco de 100 proyectos con buscador.

## 8. Historial de versiones
| Versión | Cambio principal |
| --- | --- |
| Primeras | Catálogo de 12 guías y 13 fragmentos; 100 proyectos del PDF; asociación NAP (12 contenidos, 52 vínculos); guías A05 a A08 |
| Siguientes | Editar, guardar, recuperar, imprimir y PDF; contexto de clase (modalidad, dificultad, conocimientos previos); búsqueda por materiales |
| IA 1 | Adaptar objetivos con Ollama (`/actividades/generar-ia`) |
| IA 2 | Generación completa (`/actividades/crear-ia`), materiales en texto libre, espera de 600 s, `diagnosticar_ia.py`, controles de silicona, tiempos y recursos |
| 0.7 (10/10) | Orientación didáctica por contenido; plan y prueba antes que el resto; prompt más corto; se reparan errores en lugar de descartar la generación; control de desvío curricular; `evaluar_casos.py`; 11 pruebas |
| 0.7.1 (12/10) | `asociar_nap.py` lee en UTF-8; `reparar_acentos.py`. **Aplicado en la PC:** 63 registros reparados |
| 0.8 (12-13/10) | Contexto local automático (`contexto_local.json`, `conexion_local` obligatorio); 18 pruebas |

## 9. Pruebas y evaluación real

**Pruebas unitarias:** `.\.venv\Scripts\python.exe -m unittest pruebas.test_generador -v` → **18 pruebas OK**. Usan Ollama simulado y la base en modo lectura. Cubren: caso correcto, desvío a estructuras en energía, reparación de recursos, materiales no declarados, cantidades, ajuste de tiempos, listas mal separadas, nombres compuestos, silicona sin pistola, orientaciones completas, que el resultado se pueda guardar, y 7 pruebas de contexto local.

**Evaluación real (12/10/2026, qwen3:1.7b, 25 alumnos, grupos de 4, 80 min)**, en `evaluaciones\20261012_2044_qwen3-1.7b\` con `analisis_preliminar.txt`:

| Resultado | Casos |
| --- | --- |
| Pertinencia curricular correcta | 7 de 7 |
| Copia literal del ejemplo del prompt ("2 rectángulos de cartón de 10 x 20 cm para la base") | 7 de 7 |
| Cantidades absurdas (25 por grupo, 175 en total) | 4 de 7 |
| "Revisión obligatoria" con algún aviso | 2 de 7 (solo por cargas sin identificar) |
| Tiempo por generación | 313 a 467 s |

Otros problemas observados: medidas y usos inventados (palitos de 1 m, "unir con tijeras"), títulos genéricos ("Actividad de Educación Tecnológica"), el modelo propone de 35 a 60 minutos y el ajuste estira etapas, y menciona un LED no declarado. El caso "carton motores" se rechazó con 422, que es lo correcto.

**Caso San Luis:** en la 1.ª corrida la IA ignoró la referencia y el control lo detectó. En la 2.ª corrida, con el campo obligatorio, escribió "En el Parque Eólico San Luis Norte, los alumnos observan los aerogeneradores…" (usa la referencia, pero sugiere una visita: revisar redacción).

## 10. Pendiente, en orden sugerido
1. **Quitar el ejemplo literal del prompt**, en la regla 4 de `construir_instrucciones()` en `ia_generadora.py`.
2. **Nuevos controles:**
   - cantidad por grupo igual a la cantidad de alumnos, o más de 2 tijeras por grupo;
   - título genérico o igual al tema o al contenido;
   - LED, pilas o tester mencionados sin estar declarados;
   - acciones repetidas entre etapas;
   - aviso fuerte si la IA propone menos del 60 % del tiempo.
3. Repetir `evaluar_casos.py` y comparar con la evaluación anterior. Probar `--modelo qwen3:4b`. Ojo: los casos de N61 ahora reciben la referencia de San Luis.
4. **Referencias locales:**
   - cargar más, verificadas por el docente (industrias de La Punta, diques, transporte);
   - revisar SL-02;
   - mejorar la redacción de `conexion_local` para que sea una pregunta de inicio y no una visita.
5. **Base de datos:**
   - banco de ejemplos revisados por contenido, para pasarle uno a la IA como modelo;
   - tipo y uso de cada material (herramienta, unión, carga, electrónica; quién lo usa; qué necesita para funcionar);
   - sinónimos;
   - columnas de seguimiento en `propuestas_guardadas` (contenido_id, modelo, version_prompt, estado de revisión y calificación docente).
6. Revisar las 12 orientaciones didácticas (son una propuesta) y el nombre oficial del tercer eje.
7. Crear `requirements.txt`, hacer commit de la 0.8 y borrar archivos sin uso (`formulario.html`, `main.bat`).

## 11. Avisos para quien continúe
- **Codificación:** leer y escribir siempre con `encoding='utf-8'`. Windows usa cp1252 por defecto y eso causó los acentos rotos.
- **Archivos de datos:** el docente edita los JSON con el Bloc de notas. Mantenerlos legibles y reiniciar Uvicorn después de cambiarlos.
- **Modelo:** el modelo es chico. Funcionan mejor los campos obligatorios en el esquema y las instrucciones cortas y específicas del caso que agregar reglas generales.
- **Ollama:** no generar desde el formulario mientras corre `evaluar_casos.py`, porque los dos usarían Ollama a la vez.
- **Comprobaciones:** todas las pruebas automáticas usan IA simulada. La calidad real solo se mide con `evaluar_casos.py` y con revisión docente.
