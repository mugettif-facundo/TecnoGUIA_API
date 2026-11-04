# TecnoGUIA — Informe de traspaso (versión 0.8, 13/10/2026)

**Qué es:** API en FastAPI + SQLite (`tecnoguia.db`) con un formulario web (`formulario_multi.html`) que genera actividades de Educación Tecnológica para 5.º y 6.º grado (NAP, Argentina) usando IA local: Ollama con **qwen3:1.7b**. Proyecto de TFG de un docente de La Punta, San Luis. Carpeta: `C:\Users\MakerCompetencia\TecnoGUIA_API`.

**Arranque (PowerShell):** `cd C:\Users\MakerCompetencia\TecnoGUIA_API` → `.\.venv\Scripts\python.exe -m uvicorn main:app --reload` → abrir `http://127.0.0.1:8000/formulario` (Ctrl+F5).

## Hecho en esta sesión
1. **0.7.1 – Acentos rotos reparados.** `reparar_acentos.py` corrigió 63 registros (ejes, contenidos, vínculos NAP y 2 propuestas). Respaldo: `tecnoguia_respaldo_20261012_204234.db`.
2. **Evaluación real de la 0.7 con `evaluar_casos.py`** (8 casos, qwen3:1.7b, 5 a 8 min por caso). Resultados en `evaluaciones\20261012_2044_qwen3-1.7b\`, con análisis en `analisis_preliminar.txt` y `planilla_docente.csv` para calificar.
   - Bien: pertinencia curricular en 7 de 7; plan y prueba coherentes; el caso "carton motores" se rechaza como corresponde.
   - Mal: copia literal del ejemplo del prompt ("2 rectángulos de cartón de 10 x 20 cm para la base") en 7 de 7; cantidades absurdas (25 por grupo, 175 en total) en 4 de 7; medidas y usos inventados ("unir con tijeras"); títulos genéricos; el modelo propone menos de 80 min y el ajuste proporcional infla etapas; "Revisión obligatoria" solo avisó en 2 de 7.
3. **0.8 – Contexto local automático** (sin cambios en el formulario).
   - `contexto_local.json` tiene `"localidad_escuela": "San Luis"` y referencias con fuente, contenidos NAP y `verificada`.
   - Solo se envían a la IA las referencias verificadas del contenido elegido. Hoy: Parque Eólico San Luis Norte (Toro Negro) → N61. Los seguidores solares → N62 quedan sin verificar.
   - Con referencia, el esquema JSON agrega el campo obligatorio `plan.conexion_local`. Una instrucción suelta fue ignorada por el modelo; con el campo obligatorio, la prueba real sí la usó.
   - Si la IA no la usa, aparece una observación. La propuesta registra la referencia y su fuente.
   - Archivos tocados: `ia_generadora.py`, `formulario_multi.html` (solo muestra el contexto), `pruebas\test_generador.py` (18 pruebas OK), `evaluar_casos.py`, `CAMBIOS_0.8.txt`.

## Pendiente (en orden sugerido)
1. Quitar el ejemplo literal del prompt (`ia_generadora.py`, regla 4 de `construir_instrucciones`).
2. Controles nuevos: cantidad por grupo igual al número de alumnos; título genérico o igual al tema; recursos no declarados en el texto (LED, pilas, tester); acciones repetidas entre etapas; aviso fuerte si la IA propone menos del 60 % del tiempo.
3. Volver a correr `evaluar_casos.py` y comparar. Probar `--modelo qwen3:4b`.
4. Cargar más referencias de San Luis verificadas por el docente (industrias de La Punta, diques, transporte) y revisar SL-02.
5. Recomendaciones de base ya propuestas: banco de ejemplos revisados por contenido; tipo y uso de cada material del catálogo; columnas de seguimiento en `propuestas_guardadas` (contenido, modelo, versión, calificación).
6. Hacer commit en git (rama `fix/leeme-errata`): los cambios de la 0.8 no están confirmados.

**Criterio del proyecto:** distinguir siempre lo comprobado de lo supuesto; la IA no inventa datos locales ni materiales; todo borrador requiere revisión docente.
