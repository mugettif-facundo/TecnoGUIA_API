/* TecnoGUIA 0.13.0-full — interfaz. Datos curriculares: datos/*.js; actividades propias y registros: servidor (SQLite), por usuario.
   Cambios respecto de 0.12.1-web: almacenamiento en el servidor, puente a Ollama y arranque tras iniciar sesión. */
window.TG_ARRANCAR = function () {
  'use strict';
  var M = window.TG_MOTOR, CORPUS = window.TG_CORPUS, DOCS = window.TG_DOCUMENTOS, BANCO = window.TG_BANCO || [];
  var $ = function (id) { return document.getElementById(id); };
  var estado = { datos: null, busqueda: null, registro: null, propias: [], ultimo: null, p36: null };

  function el(tag, attrs, hijos) {
    var e = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) { if (k === 'text') e.textContent = attrs[k]; else if (k === 'class') e.className = attrs[k]; else e.setAttribute(k, attrs[k]); });
    (hijos || []).forEach(function (h) { if (h) e.append(h); });
    return e;
  }
  function mensaje(id, texto, tipo) { var c = $(id); c.replaceChildren(); if (texto) c.append(el('div', { class: 'caja ' + (tipo || ''), text: texto })); }
  function ahora() { return new Date().toLocaleString('es-AR'); }
  function documento(r) { return DOCS[r.documento] || { titulo: r.documento }; }

  /* ---------- Estado de conexión (objetivo 5: funcionamiento sin Internet) ---------- */
  function pintarConexion() {
    $('conexion').textContent = navigator.onLine ? 'Conexión a Internet: detectada' : 'Sin conexión a Internet: trabajando con recursos locales';
  }
  window.addEventListener('online', pintarConexion); window.addEventListener('offline', pintarConexion); pintarConexion();
  $('version').textContent = 'Versión ' + M.VERSION + ' · corpus C01–C13 (' + CORPUS.length + ') · banco ' + BANCO.length;

  /* ---------- Pestañas ---------- */
  document.querySelectorAll('nav button').forEach(function (b) {
    b.addEventListener('click', function () { mostrarPestana(b.dataset.panel); });
  });
  function mostrarPestana(id) {
    document.querySelectorAll('nav button').forEach(function (b) { b.setAttribute('aria-selected', String(b.dataset.panel === id)); });
    document.querySelectorAll('.vista').forEach(function (v) { v.classList.toggle('oculto', v.id !== id); });
    window.scrollTo(0, 0);
  }

  /* ---------- Almacenamiento en el servidor (RF08–RF09): SQLite, separado por usuario ---------- */
  function api(metodo, ruta, cuerpo) {
    return fetch(ruta, { method: metodo, credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-TecnoGuIA': '1' },
      body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo) }).then(function (r) {
      if (r.status === 401) { location.href = '/ingresar'; throw new Error('La sesión venció. Volvé a ingresar.'); }
      return r.json().catch(function () { return {}; }).then(function (j) { if (!r.ok) throw new Error(j.detail || ('Error ' + r.status)); return j; });
    });
  }
  var todos = function (a) { return api('GET', '/planificador/api/almacen/' + a); };
  var guardar = function (a, v) { return api('PUT', '/planificador/api/almacen/' + a, v); };
  var borrar = function (a, k) { return api('DELETE', '/planificador/api/almacen/' + a + '/' + encodeURIComponent(k)); };

  /* ---------- Planificar ---------- */
  function leerDatos() {
    return { grado: $('grado').value, duracion: $('duracion').value, estudiantes: $('estudiantes').value || '25', dificultad: $('dificultad').value,
      contenido: $('contenido').value.trim(), materiales: $('materiales').value.trim(), contexto: $('contexto').value.trim() };
  }
  function ocultarDesde(n) { ['panel-fuentes', 'panel-generar', 'panel-borrador'].slice(n).forEach(function (id) { $(id).classList.add('oculto'); }); }

  $('form').addEventListener('submit', function (ev) {
    ev.preventDefault(); ocultarDesde(0);
    var d = leerDatos(), faltan = [];
    if (!d.grado) faltan.push('grado'); if (!d.contenido) faltan.push('contenido o tema');
    if (faltan.length) { mensaje('estado-busqueda', 'Completá antes de generar: ' + faltan.join(' y ') + '.', 'error'); ($(d.grado ? 'contenido' : 'grado')).focus(); return; }
    estado.datos = d;
    var r = M.recuperar(d.contenido, d.grado, CORPUS); estado.busqueda = r;
    if (!r.cobertura) { mensaje('estado-busqueda', r.motivo, 'error'); return; }
    mensaje('estado-busqueda', '');
    mostrarFuentes(r); $('panel-fuentes').classList.remove('oculto'); $('panel-generar').classList.remove('oculto');
    $('panel-fuentes').scrollIntoView({ behavior: 'smooth' });
  });

  function mostrarFuentes(r) {
    var cont = $('fuentes'); cont.replaceChildren();
    r.registros.forEach(function (x, i) {
      var reg = x.registro, doc = documento(reg), id = 'reg-' + reg.id;
      var radio = el('input', { type: 'radio', name: 'registro', id: id, value: reg.id }); if (i === 0) radio.checked = true;
      radio.addEventListener('change', function () { elegirRegistro(reg); });
      cont.append(el('div', { class: 'caja fuente' }, [
        el('label', { for: id, style: 'display:flex;gap:8px;margin:0' }, [radio, el('span', {}, [
          el('b', { text: reg.id + ' · ' + reg.titulo + ' (' + reg.grado + '.º grado)' }),
          el('div', { text: reg.sintesis }),
          el('div', { class: 'nota', text: M.citarFuentes(reg, DOCS, doc) +
            ' · Síntesis de trabajo, no cita textual · Coincidencias: ' + x.terminos.join(', ') + ' (puntaje ' + x.puntaje + ')' })])])]));
    });
    if (r.registros.length > 1) cont.append(el('p', { class: 'nota', text: 'Hay más de un registro posible. Elegí el que corresponde a tu clase.' }));
    elegirRegistro(r.registros[0].registro);
  }

  function elegirRegistro(reg) {
    estado.registro = reg;
    var todas = M.experiencias(reg.id, estado.datos.grado, BANCO, estado.propias), cont = $('experiencias'); cont.replaceChildren();
    // v0.12: primero las del mismo tema; solo se marca por defecto la más cercana. Las de otro tema se muestran sin marcar.
    var relevantes = M.experienciasRelevantes(estado.datos.contenido, todas);
    var lista = relevantes.concat(todas.filter(function (a) { return relevantes.indexOf(a) < 0; }));
    if (!lista.length) { cont.append(el('p', { class: 'nota', text: 'No hay experiencias registradas para ' + reg.id + ' en ' + estado.datos.grado + '.º grado. Podés generar igual con la fuente curricular.' })); return; }
    lista.forEach(function (a, i) {
      var id = 'exp-' + a.id, cb = el('input', { type: 'checkbox', id: id, value: a.id }), mismoTema = relevantes.indexOf(a) >= 0;
      if (i === 0 && mismoTema) cb.checked = true;
      cont.append(el('div', { class: 'exp' }, [el('label', { for: id }, [cb, el('span', {}, [
        el('span', { class: 'etq' + (a.propia ? ' propia' : ''), text: a.propia ? 'Propia ' + a.id : a.id }), el('b', { text: a.titulo }),
        mismoTema ? null : el('span', { class: 'nota', text: ' · tema distinto: si la marcás, el modelo puede copiar otro producto' }),
        el('div', { class: 'nota', text: a.autoria + (a.materiales && a.materiales.length ? ' · Materiales: ' + a.materiales.slice(0, 6).join(', ') : '') })])])]));
    });
  }
  function experienciasElegidas() {
    var ids = Array.prototype.map.call(document.querySelectorAll('#experiencias input:checked'), function (c) { return c.value; });
    return M.experiencias(estado.registro.id, estado.datos.grado, BANCO, estado.propias).filter(function (a) { return ids.indexOf(a.id) >= 0; });
  }

  function idBorrador() { var d = new Date(), p = function (n) { return String(n).padStart(2, '0'); };
    return 'B-' + d.getFullYear() + p(d.getMonth() + 1) + p(d.getDate()) + '-' + p(d.getHours()) + p(d.getMinutes()) + p(d.getSeconds()); }

  function tarjetasIndicadores(ev) {
    var c = function (titulo, valor, clase) { return el('div', { class: clase }, [el('b', { text: titulo }), el('span', { text: valor })]); };
    return el('div', { class: 'ind' }, [
      c('Adecuación curricular', ev.adecuacion.nivel + (ev.adecuacion.terminos.length ? ': ' + ev.adecuacion.terminos.join(', ') : ''),
        ev.adecuacion.nivel === 'presente' ? 'bien' : ev.adecuacion.nivel === 'débil' ? 'medio' : 'mal'),
      c('Contexto', ev.contexto.nivel + (ev.contexto.usados.length ? ': ' + ev.contexto.usados.join(', ') : ''),
        ev.contexto.nivel === 'incorporado' ? 'bien' : ev.contexto.nivel === 'sin contexto declarado' ? 'medio' : 'mal'),
      c('Materiales no declarados', ev.materiales_no_declarados.length ? ev.materiales_no_declarados.join(', ') : 'ninguno', ev.materiales_no_declarados.length ? 'mal' : 'bien'),
      c('Tiempos', ev.tiempos_ok ? 'suman la duración' : 'no suman', ev.tiempos_ok ? 'bien' : 'mal'),
      c('Secciones', ev.secciones_faltantes.length ? 'faltan ' + ev.secciones_faltantes.join(', ') : 'completas', ev.secciones_faltantes.length ? 'mal' : 'bien')]);
  }

  function mostrarBorrador(b, meta, avisos) {
    meta.avisos = avisos; meta.id = idBorrador(); meta.indicadores = M.evaluarBorrador(b, meta.datos, meta.registro);
    var texto = M.aTexto(b, meta);
    $('borrador').value = texto; estado.ultimo = { meta: meta, texto: texto };
    $('indicadores').replaceChildren(tarjetasIndicadores(meta.indicadores));
    $('v-borrador').value = meta.id + ' · ' + meta.modo + (meta.modelo ? ' · ' + meta.modelo : '');
    var cont = $('avisos-borrador'); cont.replaceChildren();
    var graves = avisos.filter(function (a) { return /^ATENCIÓN/.test(a); });
    cont.append(el('div', { class: 'caja ' + (meta.modo.indexOf('IA') >= 0 ? 'fuente' : 'aviso'), text: 'Modo: ' + meta.modo + (meta.modelo ? ' · Modelo: ' + meta.modelo : '') + (meta.segundos != null ? ' · ' + meta.segundos + ' s' : '') }));
    if (graves.length) cont.append(el('div', { class: 'caja error', text: 'Revisión obligatoria: ' + graves.length + ' aviso(s). Están al final del borrador.' }));
    $('panel-borrador').classList.remove('oculto'); $('panel-borrador').scrollIntoView({ behavior: 'smooth' });
    registrar(Object.assign({ borrador: meta.id, modo: meta.modo, modelo: meta.modelo || '', segundos: meta.segundos, avisos: avisos.length, resultado: 'generado' },
      columnasIndicadores(meta.indicadores)));
  }
  function columnasIndicadores(ev) {
    return { adecuacion: ev.adecuacion.nivel, terminos_curriculares: ev.adecuacion.terminos.join(' '), contexto_uso: ev.contexto.nivel,
      materiales_no_declarados: ev.materiales_no_declarados.join(' | '), tiempos_ok: ev.tiempos_ok ? 'sí' : 'no', secciones_faltantes: ev.secciones_faltantes.join(' ') };
  }

  /* Generación con Ollama: la usan el botón y los casos G01–G06. Devuelve el borrador estructurado y los avisos. */
  async function generarConIA(datos, registro, exps, modelo, url, senal) {
    var inicio = Date.now();
    var resp = await fetch(url + '/api/chat', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-TecnoGuIA': '1' }, signal: senal,
      body: JSON.stringify(M.pedidoOllama(datos, registro, exps, modelo)) });
    if (resp.status === 503) throw new TypeError('Ollama no disponible');
    if (resp.status === 404) throw new Error('el modelo ' + modelo + ' no está descargado. En una terminal: ollama pull ' + modelo);
    if (!resp.ok) throw new Error('Ollama respondió con estado ' + resp.status);
    var json = await resp.json(), b;
    try { b = JSON.parse(json.message.content); } catch (e) { throw new Error('el modelo no devolvió un borrador con la estructura esperada. Volvé a generar.'); }
    var avisos = M.controlar(b, datos);
    if (json.done_reason === 'length') avisos.unshift('ATENCIÓN: la respuesta se cortó por longitud; puede faltar texto.');
    return { b: b, avisos: avisos, segundos: Math.round((Date.now() - inicio) / 1000) };
  }
  function textoError(e, url) {
    return e.name === 'AbortError' ? 'La generación se canceló (límite de 10 minutos o detenida).' :
      (e instanceof TypeError ? 'Ollama no está disponible en ' + url + '. Abrí Ollama en esta computadora y volvé a intentar.' : 'No se pudo generar con IA: ' + e.message);
  }

  function metaBase(modo) {
    return { modo: modo, fecha: ahora(), datos: estado.datos, registro: estado.registro, documento: documento(estado.registro), documentos: DOCS, experiencias: experienciasElegidas() };
  }

  $('btn-plantilla').addEventListener('click', function () {
    var meta = metaBase('Plantilla local (sin IA)');
    var b = M.generarPlantilla(estado.datos, estado.registro, meta.experiencias[0]);
    meta.segundos = 0;
    mostrarBorrador(b, meta, ['Borrador armado con plantilla fija: no fue generado por un modelo de IA. Completá cantidades y adaptá los pasos.']);
    mensaje('estado-gen', '');
  });

  var generando = false;
  $('btn-ia').addEventListener('click', async function () {
    if (generando) return;
    var modelo = $('modelo').value, url = $('url-ollama').value.replace(/\/+$/, ''), meta = metaBase('IA local (Ollama)');
    meta.modelo = modelo; generando = true; $('btn-ia').disabled = true; $('btn-plantilla').disabled = true;
    var inicio = Date.now(), ctrl = new AbortController(), limite = setTimeout(function () { ctrl.abort(); }, 600000);
    var reloj = setInterval(function () { mensaje('estado-gen', 'Generando con ' + modelo + '… ' + Math.round((Date.now() - inicio) / 1000) + ' s (puede tardar varios minutos).'); }, 1000);
    try {
      var r = await generarConIA(estado.datos, estado.registro, meta.experiencias, modelo, url, ctrl.signal);
      meta.segundos = r.segundos;
      mostrarBorrador(r.b, meta, r.avisos);
      mensaje('estado-gen', 'Borrador generado con IA local (' + modelo + ') en ' + meta.segundos + ' s. Revisalo antes de usarlo.', 'ok');
    } catch (e) {
      var texto = textoError(e, url);
      mensaje('estado-gen', texto + ' No se generó ningún borrador con IA; si lo necesitás, usá la plantilla local (queda identificada como tal).', 'error');
      registrar({ modo: 'IA local (Ollama)', modelo: modelo, segundos: Math.round((Date.now() - inicio) / 1000), avisos: 0, resultado: 'error: ' + texto });
    } finally { clearTimeout(limite); clearInterval(reloj); generando = false; $('btn-ia').disabled = false; $('btn-plantilla').disabled = false; }
  });

  async function comprobarOllama(silencioso) {
    var url = $('url-ollama').value.replace(/\/+$/, ''), ctrl = new AbortController(), t = setTimeout(function () { ctrl.abort(); }, 4000);
    try {
      var rt = await fetch(url + '/api/tags', { signal: ctrl.signal }); if (!rt.ok) throw new TypeError('sin Ollama'); var tags = await rt.json();
      var ver = await (await fetch(url + '/api/version')).json().catch(function () { return {}; });
      var nombres = (tags.models || []).map(function (m) { return m.name; }), sel = $('modelo'), previo = sel.value;
      if (nombres.length) {
        sel.replaceChildren(); nombres.forEach(function (n) { sel.append(el('option', { value: n, text: n })); });
        sel.value = nombres.indexOf(previo) >= 0 ? previo : (nombres.indexOf('qwen3:1.7b') >= 0 ? 'qwen3:1.7b' : nombres[0]);
      }
      estado.ollama = { version: ver.version || '?', modelos: nombres };
      if (!silencioso) mensaje('estado-gen', 'Ollama ' + (ver.version || '') + ' disponible. Modelos: ' + (nombres.join(', ') || 'ninguno descargado') + '.', nombres.length ? 'ok' : 'aviso');
    } catch (e) {
      estado.ollama = null;
      if (!silencioso) mensaje('estado-gen', 'Ollama no responde en ' + url + '. La plantilla local sigue disponible.', 'error');
    } finally { clearTimeout(t); }
  }
  $('btn-estado-ia').addEventListener('click', function () { comprobarOllama(false); });

  $('btn-copiar').addEventListener('click', async function () {
    try { await navigator.clipboard.writeText($('borrador').value); mensaje('estado-borrador', 'Borrador copiado.', 'ok'); }
    catch (e) { $('borrador').select(); document.execCommand('copy'); mensaje('estado-borrador', 'Borrador copiado.', 'ok'); }
  });
  function descargar(nombre, contenido, tipo) {
    var a = el('a', { href: URL.createObjectURL(new Blob([contenido], { type: tipo })), download: nombre });
    document.body.append(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
  }
  $('btn-descargar').addEventListener('click', function () { descargar('TecnoGuIA_borrador.txt', $('borrador').value, 'text/plain;charset=utf-8'); });

  /* F08: actividad derivada que conserva la edición y la procedencia. */
  $('btn-guardar-derivada').addEventListener('click', function () {
    if (!estado.ultimo) return;
    var m = estado.ultimo.meta, texto = $('borrador').value, titulo = (texto.split('\n')[3] || '').trim();
    limpiarAlta();
    $('a-titulo').value = titulo.charAt(0) + titulo.slice(1).toLowerCase();
    $('a-autoria').value = 'Docente, a partir de un borrador de TecnoGuIA (' + m.modo + (m.modelo ? ', ' + m.modelo : '') + ', ' + m.fecha + '; fuentes: ' +
      [m.registro.id].concat(m.experiencias.map(function (a) { return a.id; })).join(', ') + ')' + (texto !== estado.ultimo.texto ? '; editado por el docente' : '');
    $('a-grado').value = m.datos.grado; $('a-registro').value = m.registro.id; $('a-duracion').value = m.datos.duracion;
    $('a-materiales').value = m.datos.materiales; $('a-contexto').value = m.datos.contexto; $('a-procedimiento').value = texto;
    $('a-aplicacion').value = 'Sin registro'; mostrarPestana('propias');
    mensaje('estado-alta', 'Revisá los campos y presioná «Guardar actividad».', 'aviso'); $('a-titulo').focus();
  });

  /* ---------- Mis actividades ---------- */
  CORPUS.forEach(function (r) { $('a-registro').append(el('option', { value: r.id, text: r.id + ' · ' + r.titulo + ' (' + r.grado + '.º)' })); });
  function limpiarAlta() { $('form-alta').reset(); $('a-id').value = ''; $('btn-alta').textContent = 'Guardar actividad'; mensaje('estado-alta', ''); }
  $('btn-alta-limpiar').addEventListener('click', limpiarAlta);
  function proximoId() {
    var max = estado.propias.reduce(function (n, a) { var m = /^A-N(\d+)$/.exec(a.id); return m ? Math.max(n, Number(m[1])) : n; }, 0);
    return 'A-N' + String(max + 1).padStart(2, '0');
  }
  $('form-alta').addEventListener('submit', async function (ev) {
    ev.preventDefault();
    var v = function (id) { return $(id).value.trim(); };
    var faltan = [['a-titulo', 'título'], ['a-autoria', 'autoría'], ['a-materiales', 'materiales'], ['a-procedimiento', 'procedimiento']].filter(function (x) { return !v(x[0]); });
    if (faltan.length) { mensaje('estado-alta', 'Completá: ' + faltan.map(function (x) { return x[1]; }).join(', ') + '.', 'error'); $(faltan[0][0]).focus(); return; }
    var id = v('a-id') || proximoId(), previa = estado.propias.filter(function (a) { return a.id === id; })[0];
    var act = { id: id, tipo: 'propia', titulo: v('a-titulo'), eje: 'Procesos tecnológicos', grados: [Number($('a-grado').value)], registros: [$('a-registro').value],
      autoria: v('a-autoria'), procedencia: 'Actividad propia registrada en TecnoGuIA.', objetivo: v('a-objetivo') ? [v('a-objetivo')] : [],
      materiales: M.separarMateriales(v('a-materiales')), duracion: Number($('a-duracion').value) || null, consigna: v('a-consigna'),
      procedimiento: v('a-procedimiento').split('\n').map(function (s) { return s.trim(); }).filter(Boolean), seguridad: v('a-seguridad') ? [v('a-seguridad')] : [],
      contexto_adaptaciones: v('a-contexto'), aplicacion_anterior: v('a-aplicacion') || 'Sin registro', revision_docente: v('a-revision'),
      creada: previa ? previa.creada : new Date().toISOString(), actualizada: new Date().toISOString() };
    try { await guardar('actividades', act); await cargarPropias(); limpiarAlta(); mensaje('estado-alta', 'Actividad ' + id + ' guardada en tu cuenta.', 'ok'); }
    catch (e) { mensaje('estado-alta', 'No se pudo guardar: ' + e.message, 'error'); }
  });

  async function cargarPropias() {
    try { estado.propias = (await todos('actividades')).sort(function (a, b) { return a.id.localeCompare(b.id); }); }
    catch (e) { estado.propias = []; mensaje('estado-lista', e.message, 'error'); }
    var cont = $('lista-propias'); cont.replaceChildren();
    if (!estado.propias.length) { cont.append(el('p', { class: 'nota', text: 'Todavía no guardaste actividades propias.' })); return; }
    estado.propias.forEach(function (a) {
      var editar = el('button', { class: 'b gris', type: 'button', text: 'Editar' }), quitar = el('button', { class: 'b gris', type: 'button', text: 'Eliminar' });
      editar.addEventListener('click', function () { cargarEnAlta(a); });
      quitar.addEventListener('click', async function () {
        if (!confirm('¿Eliminar definitivamente la actividad ' + a.id + ' de tu cuenta?')) return;
        await borrar('actividades', a.id); await cargarPropias(); mensaje('estado-lista', 'Actividad ' + a.id + ' eliminada.', 'ok');
      });
      cont.append(el('div', { class: 'exp' }, [el('span', { class: 'etq propia', text: a.id }), el('b', { text: a.titulo }),
        el('div', { class: 'nota', text: a.grados[0] + '.º grado · ' + a.registros.join(', ') + ' · ' + a.autoria + ' · actualizada ' + new Date(a.actualizada).toLocaleString('es-AR') }),
        el('div', { class: 'botones' }, [editar, quitar])]));
    });
  }
  function cargarEnAlta(a) {
    $('a-id').value = a.id; $('a-titulo').value = a.titulo; $('a-autoria').value = a.autoria; $('a-grado').value = a.grados[0]; $('a-registro').value = a.registros[0];
    $('a-duracion').value = a.duracion || ''; $('a-aplicacion').value = a.aplicacion_anterior || ''; $('a-objetivo').value = (a.objetivo || []).join('\n');
    $('a-materiales').value = (a.materiales || []).join(', '); $('a-consigna').value = a.consigna || ''; $('a-procedimiento').value = (a.procedimiento || []).join('\n');
    $('a-seguridad').value = (a.seguridad || []).join('\n'); $('a-contexto').value = a.contexto_adaptaciones || ''; $('a-revision').value = a.revision_docente || '';
    $('btn-alta').textContent = 'Guardar cambios en ' + a.id; mensaje('estado-alta', 'Editando ' + a.id + '.', 'aviso'); $('a-titulo').focus();
  }
  $('btn-exportar').addEventListener('click', function () {
    descargar('TecnoGuIA_actividades_propias_' + new Date().toISOString().slice(0, 10) + '.json', JSON.stringify({ app: 'TecnoGuIA', version: M.VERSION, actividades: estado.propias }, null, 1), 'application/json');
  });
  $('importar').addEventListener('change', async function () {
    var f = this.files[0]; if (!f) return;
    try {
      var d = JSON.parse(await f.text()), lista = (d.actividades || []).filter(function (a) { return a && /^A-N\d+$/.test(a.id) && a.titulo && a.registros && a.grados; });
      for (var i = 0; i < lista.length; i++) await guardar('actividades', lista[i]);
      await cargarPropias(); mensaje('estado-lista', lista.length + ' actividad(es) importadas.', 'ok');
    } catch (e) { mensaje('estado-lista', 'El archivo no es una copia válida de TecnoGuIA.', 'error'); }
    this.value = '';
  });

  /* ---------- Banco ---------- */
  (function () {
    var cont = $('lista-banco');
    BANCO.forEach(function (a) {
      var det = el('details', {}, [el('summary', {}, [el('span', { class: 'etq', text: a.id }), el('b', { text: a.titulo + ' · ' + a.grados.join('.º y ') + '.º · ' + a.registros.join(', ') })]),
        el('p', { class: 'nota', text: 'Autoría: ' + a.autoria }), el('p', { class: 'nota', text: 'Procedencia: ' + a.procedencia }),
        el('p', { text: 'Materiales: ' + a.materiales.join(', ') }), a.consigna ? el('p', { text: 'Consigna: ' + a.consigna }) : null,
        a.procedimiento.length ? el('ol', {}, a.procedimiento.map(function (p) { return el('li', { text: p }); })) : el('p', { class: 'nota', text: 'Sin pasos desarrollados.' }),
        el('p', { class: 'nota', text: 'Aplicación anterior: ' + a.aplicacion_anterior + ' · Revisión docente: ' + a.revision_docente })]);
      cont.append(el('div', { class: 'exp' }, [det]));
    });
  })();

  /* ---------- Pruebas y registro (HU11) ---------- */
  function csv(filas) {
    return '﻿' + filas.map(function (f) { return f.map(function (c) { return '"' + String(c == null ? '' : c).replace(/"/g, '""') + '"'; }).join(';'); }).join('\r\n');
  }
  $('btn-p36').addEventListener('click', function () {
    var filas = window.TG_PRUEBAS.map(function (p) {
      var r = M.recuperar(p.consulta, p.grado, CORPUS), obt = r.registros.map(function (x) { return x.registro.id; });
      var ok = p.esperado.length ? p.esperado.indexOf(obt[0]) >= 0 : !r.cobertura;
      return { p: p, obt: obt, ok: ok, motivo: r.cobertura ? '' : r.motivo };
    });
    estado.p36 = filas;
    var cub = filas.filter(function (f) { return f.p.esperado.length; }), sin = filas.filter(function (f) { return !f.p.esperado.length; });
    var okc = cub.filter(function (f) { return f.ok; }).length, oks = sin.filter(function (f) { return f.ok; }).length;
    $('resumen-p36').replaceChildren(el('div', { class: 'caja ' + (okc === cub.length && oks === sin.length ? 'ok' : 'aviso'),
      text: 'Recuperación pertinente: ' + okc + ' de ' + cub.length + ' (' + Math.round(100 * okc / cub.length) + ' %). Rechazo correcto: ' + oks + ' de ' + sin.length +
        ' (' + Math.round(100 * oks / sin.length) + ' %). Corpus ' + CORPUS.length + ' registros · versión ' + M.VERSION + ' · ' + ahora() + '.' }));
    var t = el('table', {}, [el('thead', {}, [el('tr', {}, ['ID', 'Grado', 'Tipo', 'Consulta', 'Esperado', 'Obtenido', 'Resultado'].map(function (h) { return el('th', { text: h }); }))])]);
    var tb = el('tbody'); t.append(tb);
    filas.forEach(function (f) {
      tb.append(el('tr', {}, [el('td', { text: f.p.id }), el('td', { text: f.p.grado + '.º' }), el('td', { text: f.p.tipo }), el('td', { text: f.p.consulta }),
        el('td', { text: f.p.esperado.join(', ') || 'Rechazo' }), el('td', { text: f.obt.join(', ') || 'Sin cobertura' }),
        el('td', { class: f.ok ? 'ok' : 'mal', text: f.ok ? 'Correcto' : 'Incorrecto' })]));
    });
    $('tabla-p36').replaceChildren(t); $('btn-p36-csv').disabled = false;
  });
  $('btn-p36-csv').addEventListener('click', function () {
    var f = [['ID', 'Fecha', 'Versión', 'Grado', 'Tipo', 'Consulta', 'Esperado', 'Obtenido (orden)', 'Resultado', 'Motivo']].concat(estado.p36.map(function (x) {
      return [x.p.id, ahora(), M.VERSION, x.p.grado, x.p.tipo, x.p.consulta, x.p.esperado.join(', ') || 'Rechazo', x.obt.join(', ') || 'Sin cobertura', x.ok ? 'Correcto' : 'Incorrecto', x.motivo];
    }));
    descargar('TecnoGuIA_P01-P36_' + new Date().toISOString().slice(0, 10) + '.csv', csv(f), 'text/csv;charset=utf-8');
  });

  async function pintarFuncionales() {
    var guardadas = {}; try { (await todos('funcionales')).forEach(function (x) { guardadas[x.id] = x; }); } catch (e) { }
    var t = el('table', {}, [el('thead', {}, [el('tr', {}, ['Código', 'Caso', 'Esperado', 'Resultado', 'Observación', 'Fecha'].map(function (h) { return el('th', { text: h }); }))])]), tb = el('tbody'); t.append(tb);
    window.TG_PRUEBAS_FUNCIONALES.forEach(function (f) {
      var g = guardadas[f.id] || {}, sel = el('select', { 'aria-label': 'Resultado ' + f.id }), obs = el('input', { 'aria-label': 'Observación ' + f.id, value: g.observacion || '' }), fecha = el('td', { text: g.fecha || '' });
      ['Pendiente', 'Cumple', 'Cumple parcialmente', 'No cumple'].forEach(function (o) { sel.append(el('option', { value: o, text: o })); }); sel.value = g.resultado || 'Pendiente';
      var guardarF = async function () { var v = { id: f.id, resultado: sel.value, observacion: obs.value, fecha: ahora(), version: M.VERSION }; await guardar('funcionales', v); fecha.textContent = v.fecha; };
      sel.addEventListener('change', guardarF); obs.addEventListener('change', guardarF);
      tb.append(el('tr', {}, [el('td', { text: f.id }), el('td', { text: f.caso }), el('td', { text: f.esperado }), el('td', {}, [sel]), el('td', {}, [obs]), fecha]));
    });
    $('tabla-f').replaceChildren(t);
  }

  function registrar(extra) {
    var d = estado.datos || {}, r = estado.registro || {};
    var fila = Object.assign({ fecha: new Date().toISOString(), version: M.VERSION, version_corpus: 'C01–C13 (' + CORPUS.length + ')',
      internet: navigator.onLine ? 'conectado' : 'sin conexión', caso: '', grado: d.grado, consulta: d.contenido, contexto: d.contexto || '', materiales: d.materiales,
      registros: (estado.busqueda && estado.busqueda.registros || []).map(function (x) { return x.registro.id; }).join(', '), registro_usado: r.id || '',
      experiencias: (estado.registro ? experienciasElegidas() : []).map(function (a) { return a.id; }).join(', ') }, extra);
    guardar('registro', fila).then(pintarRegistro).catch(function () { });
  }
  async function pintarRegistro() {
    var filas = []; try { filas = (await todos('registro')).reverse(); } catch (e) { }
    if (!filas.length) { $('tabla-reg').replaceChildren(el('p', { class: 'nota', text: 'Sin generaciones registradas todavía.' })); return; }
    var t = el('table', {}, [el('thead', {}, [el('tr', {}, ['Fecha', 'Caso', 'Internet', 'Grado', 'Consulta', 'Registro', 'Modo', 'Modelo', 'Seg.', 'Adecuación', 'Contexto', 'Avisos', 'Resultado'].map(function (h) { return el('th', { text: h }); }))])]), tb = el('tbody'); t.append(tb);
    filas.slice(0, 50).forEach(function (f) {
      tb.append(el('tr', {}, [new Date(f.fecha).toLocaleString('es-AR'), f.caso, f.internet, f.grado, f.consulta, f.registro_usado, f.modo, f.modelo, f.segundos, f.adecuacion, f.contexto_uso, f.avisos, f.resultado].map(function (c) { return el('td', { text: c == null ? '' : String(c) }); })));
    });
    $('tabla-reg').replaceChildren(t);
  }
  $('btn-reg-csv').addEventListener('click', async function () {
    var filas = await todos('registro').catch(function () { return []; });
    var cab = ['fecha', 'version', 'version_corpus', 'internet', 'caso', 'borrador', 'grado', 'consulta', 'contexto', 'materiales', 'registros', 'registro_usado', 'experiencias',
      'modo', 'modelo', 'segundos', 'adecuacion', 'terminos_curriculares', 'contexto_uso', 'materiales_no_declarados', 'tiempos_ok', 'secciones_faltantes', 'avisos', 'resultado'];
    descargar('TecnoGuIA_registro_generaciones.csv', csv([cab].concat(filas.map(function (f) { return cab.map(function (k) { return f[k]; }); }))), 'text/csv;charset=utf-8');
  });
  $('btn-ficha').addEventListener('click', async function () {
    await comprobarOllama(true);
    var o = estado.ollama, texto = ['FICHA TÉCNICA — TecnoGuIA ' + M.VERSION, 'Fecha: ' + ahora(), 'Navegador: ' + navigator.userAgent,
      'Conexión a Internet según el navegador: ' + (navigator.onLine ? 'conectado' : 'desconectado'), 'Página abierta desde: ' + location.protocol + '//' + location.host + location.pathname,
      'Ollama: ' + (o ? 'versión ' + o.version + ' · modelos: ' + o.modelos.join(', ') : 'no disponible'), 'Modelo seleccionado: ' + $('modelo').value,
      'Corpus: ' + CORPUS.length + ' registros (C01–C13) · Banco: ' + BANCO.length + ' actividades provisorias · Actividades propias: ' + estado.propias.length,
      'Completar a mano: procesador, RAM, sistema operativo (Configuración > Sistema > Información).'].join('\n');
    descargar('TecnoGuIA_ficha_tecnica.txt', texto, 'text/plain;charset=utf-8');
  });

  /* ---------- Objetivo 5: prueba sin Internet (F07) ---------- */
  $('btn-offline').addEventListener('click', async function () {
    var b = this; b.disabled = true; $('resultado-offline').replaceChildren(el('p', { class: 'nota', text: 'Comprobando…' }));
    var filas = [], url = $('url-ollama').value.replace(/\/+$/, '');
    // 1. Estado que informa el navegador.
    filas.push(['Navegador', navigator.onLine ? 'Informa conexión a Internet' : 'Informa que no hay conexión', !navigator.onLine]);
    // 2. Intento de llegar a un sitio externo (no se envía ningún dato): debe fallar si no hay Internet.
    var externo = false, ctrl = new AbortController(), t = setTimeout(function () { ctrl.abort(); }, 4000);
    try { await fetch('https://www.gstatic.com/generate_204', { mode: 'no-cors', cache: 'no-store', signal: ctrl.signal }); externo = true; } catch (e) { } finally { clearTimeout(t); }
    filas.push(['Sitio externo de prueba', externo ? 'Respondió: hay Internet' : 'No respondió: sin Internet', !externo]);
    // 3. Recursos de la página: todos deben ser locales.
    var urls = Array.prototype.map.call(document.querySelectorAll('script[src],link[href],img[src]'), function (x) { return x.src || x.href; })
      .concat(performance.getEntriesByType('resource').map(function (r) { return r.name; }));
    var externos = urls.filter(function (u) { return /^https?:/.test(u) && !/^https?:\/\/(127\.0\.0\.1|localhost)(:|\/)/.test(u) && u.indexOf(location.origin) !== 0 && u.indexOf('gstatic.com/generate_204') < 0; });
    filas.push(['Recursos de la página', externos.length ? 'Usa recursos externos: ' + externos.join(', ') : 'Todos locales (' + urls.length + ' archivos)', !externos.length]);
    // 4. Ollama en la misma computadora.
    var modelos = [];
    try { modelos = ((await (await fetch(url + '/api/tags')).json()).models || []).map(function (m) { return m.name; }); } catch (e) { }
    var elegido = $('modelo').value, okOllama = modelos.indexOf(elegido) >= 0;
    filas.push(['Ollama local (' + url + ')', modelos.length ? 'Responde · modelos: ' + modelos.join(', ') + (okOllama ? '' : ' · falta ' + elegido) : 'No responde', okOllama]);
    var todo = filas.every(function (f) { return f[2]; });
    var t2 = el('table', {}, [el('thead', {}, [el('tr', {}, ['Comprobación', 'Resultado', 'Estado'].map(function (h) { return el('th', { text: h }); }))])]), tb = el('tbody'); t2.append(tb);
    filas.forEach(function (f) { tb.append(el('tr', {}, [el('td', { text: f[0] }), el('td', { text: f[1] }), el('td', { class: f[2] ? 'ok' : 'mal', text: f[2] ? 'Correcto' : 'No cumple' })])); });
    var conclusion = todo ? 'Sin Internet y con recursos locales: listo. Ahora generá un borrador con IA en «Planificar»; quedará registrado como «sin conexión».' :
      (externo || navigator.onLine ? 'Hay conexión a Internet: desconectá el wifi o el cable y repetí la prueba.' : 'Revisá los puntos marcados como «No cumple».');
    $('resultado-offline').replaceChildren(t2, el('div', { class: 'caja ' + (todo ? 'ok' : 'aviso'), text: conclusion }));
    var evidencia = filas.map(function (f) { return f[0] + ': ' + f[1]; }).join(' | ');
    await guardar('funcionales', { id: 'F07', resultado: todo ? 'Cumple parcialmente' : 'Pendiente', observacion: (todo ? 'Entorno sin Internet comprobado; falta registrar una generación sin conexión. ' : '') + evidencia, fecha: ahora(), version: M.VERSION }).catch(function () { });
    pintarFuncionales(); b.disabled = false;
  });

  /* ---------- Objetivo 5: casos de generación G01–G06 ---------- */
  var corridaG = null;
  $('btn-g').addEventListener('click', async function () {
    var casos = window.TG_CASOS_GENERACION, modelo = $('modelo').value, url = $('url-ollama').value.replace(/\/+$/, '');
    corridaG = { filas: [], ctrl: new AbortController() };
    $('btn-g').disabled = true; $('btn-g-parar').disabled = false; $('btn-g-csv').disabled = true;
    var t = el('table', {}, [el('thead', {}, [el('tr', {}, ['Caso', 'Grado', 'Contexto', 'Registro esperado / obtenido', 'Seg.', 'Adecuación', 'Contexto en el borrador', 'Mat. no declarados', 'Tiempos', 'Resultado'].map(function (h) { return el('th', { text: h }); }))])]), tb = el('tbody'); t.append(tb);
    $('tabla-g').replaceChildren(t);
    for (var i = 0; i < casos.length; i++) {
      var c = casos[i];
      if (corridaG.ctrl.signal.aborted) break;
      $('estado-g').textContent = 'Caso ' + c.id + ' (' + (i + 1) + ' de ' + casos.length + ') con ' + modelo + '…';
      var datos = { grado: String(c.grado), duracion: String(c.duracion), estudiantes: String(c.estudiantes), dificultad: c.dificultad, contenido: c.contenido, materiales: c.materiales, contexto: c.contexto };
      var rec = M.recuperar(c.contenido, c.grado, CORPUS), reg = rec.registros.length ? rec.registros[0].registro : null;
      var fila = { fecha: ahora(), internet: navigator.onLine ? 'conectado' : 'sin conexión', caso: c.id, grado: c.grado, contexto: c.contexto || '(sin contexto)', esperado: c.registro, obtenido: reg ? reg.id : 'sin cobertura', segundos: '', adecuacion: '', contexto_uso: '', no_declarados: '', tiempos: '', resultado: '', texto: '' };
      if (reg) {
        var exps = M.experienciasRelevantes(c.contenido, M.experiencias(reg.id, c.grado, BANCO, estado.propias)).slice(0, 1);
        try {
          var r = await generarConIA(datos, reg, exps, modelo, url, corridaG.ctrl.signal);
          var ev = M.evaluarBorrador(r.b, datos, reg);
          var meta = { modo: 'IA local (Ollama)', modelo: modelo, fecha: ahora(), datos: datos, registro: reg, documento: documento(reg), documentos: DOCS, experiencias: exps, avisos: r.avisos, indicadores: ev, id: idBorrador() };
          Object.assign(fila, { segundos: r.segundos, adecuacion: ev.adecuacion.nivel, contexto_uso: ev.contexto.nivel, no_declarados: ev.materiales_no_declarados.join(', ') || 'ninguno',
            tiempos: ev.tiempos_ok ? 'sí' : 'no', resultado: 'generado', texto: M.aTexto(r.b, meta) });
          estado.datos = datos; estado.registro = reg; estado.busqueda = rec;
          registrar(Object.assign({ caso: c.id, borrador: meta.id, modo: meta.modo, modelo: modelo, segundos: r.segundos, avisos: r.avisos.length, resultado: 'generado', experiencias: exps.map(function (a) { return a.id; }).join(', ') }, columnasIndicadores(ev)));
        } catch (e) { fila.resultado = textoError(e, url); }
      } else fila.resultado = 'sin cobertura curricular';
      corridaG.filas.push(fila);
      tb.append(el('tr', {}, [fila.caso, fila.grado + '.º', fila.contexto, fila.esperado + ' / ' + fila.obtenido, fila.segundos, fila.adecuacion, fila.contexto_uso, fila.no_declarados, fila.tiempos, fila.resultado]
        .map(function (x, j) { return el('td', { class: j === 3 ? (fila.esperado === fila.obtenido ? 'ok' : 'mal') : '', text: String(x) }); })));
    }
    $('estado-g').textContent = corridaG.ctrl.signal.aborted ? 'Corrida detenida: ' + corridaG.filas.length + ' caso(s) registrados.' : 'Listo: ' + corridaG.filas.length + ' casos. Revisá los borradores en el CSV y valoralos.';
    $('btn-g').disabled = false; $('btn-g-parar').disabled = true; $('btn-g-csv').disabled = !corridaG.filas.length;
  });
  $('btn-g-parar').addEventListener('click', function () { if (corridaG) corridaG.ctrl.abort(); });
  $('btn-g-csv').addEventListener('click', function () {
    var cab = ['fecha', 'internet', 'caso', 'grado', 'contexto', 'esperado', 'obtenido', 'segundos', 'adecuacion', 'contexto_uso', 'no_declarados', 'tiempos', 'resultado', 'texto'];
    descargar('TecnoGuIA_G01-G06_' + new Date().toISOString().slice(0, 10) + '.csv', csv([cab.concat(['version', 'modelo'])].concat(corridaG.filas.map(function (f) {
      return cab.map(function (k) { return f[k]; }).concat([M.VERSION, $('modelo').value]); }))), 'text/csv;charset=utf-8');
  });

  /* ---------- Objetivo 5: valoración exploratoria docente (Anexo D) ---------- */
  window.TG_VALORACION.forEach(function (v) {
    var s = el('select', { id: 'v-' + v.id, 'aria-label': v.id });
    ['', '1', '2', '3', '4', '5', 'No puedo valorarlo'].forEach(function (o) { s.append(el('option', { value: o, text: o || 'Elegí…' })); });
    $('v-criterios').append(el('label', { for: 'v-' + v.id, style: 'margin:0;font-weight:normal', text: v.id + '. ' + v.criterio }), s);
  });
  window.TG_PREGUNTAS_ABIERTAS.forEach(function (q, i) {
    $('v-abiertas').append(el('label', { for: 'v-q' + i, text: q }), el('textarea', { id: 'v-q' + i, rows: '2', maxlength: '800' }));
  });
  $('btn-valorar').addEventListener('click', function () {
    mostrarPestana('pruebas'); $('t-val').scrollIntoView({ behavior: 'smooth' }); $('v-codigo').focus();
  });
  $('form-val').addEventListener('submit', async function (ev) {
    ev.preventDefault();
    var cod = $('v-codigo').value.trim(), faltan = window.TG_VALORACION.filter(function (v) { return !$('v-' + v.id).value; });
    if (!cod) { mensaje('estado-val', 'Indicá el código del docente (por ejemplo D5). No uses nombres.', 'error'); return; }
    if (!$('v-borrador').value) { mensaje('estado-val', 'Primero generá un borrador en «Planificar» para que el docente lo revise.', 'error'); return; }
    if (faltan.length) { mensaje('estado-val', 'Completá: ' + faltan.map(function (v) { return v.id; }).join(', ') + '.', 'error'); return; }
    var v = { fecha: new Date().toISOString(), version: M.VERSION, codigo: cod, rol: $('v-rol').value, grado: $('v-grado').value, borrador: $('v-borrador').value };
    window.TG_VALORACION.forEach(function (c) { v[c.id] = $('v-' + c.id).value; });
    window.TG_PREGUNTAS_ABIERTAS.forEach(function (q, i) { v['P' + (i + 1)] = $('v-q' + i).value.trim(); });
    try { await guardar('valoraciones', v); mensaje('estado-val', 'Valoración de ' + cod + ' guardada.', 'ok');
      window.TG_VALORACION.forEach(function (c) { $('v-' + c.id).value = ''; }); window.TG_PREGUNTAS_ABIERTAS.forEach(function (q, i) { $('v-q' + i).value = ''; }); $('v-codigo').value = '';
      pintarValoraciones(); } catch (e) { mensaje('estado-val', 'No se pudo guardar: ' + e.message, 'error'); }
  });
  async function pintarValoraciones() {
    var vs = await todos('valoraciones').catch(function () { return []; });
    if (!vs.length) { $('resumen-val').replaceChildren(el('p', { class: 'nota', text: 'Sin valoraciones registradas.' })); return; }
    var t = el('table', {}, [el('thead', {}, [el('tr', {}, ['Ítem', 'Criterio', 'Promedio (1–5)', 'Respuestas', '«No puedo valorarlo»'].map(function (h) { return el('th', { text: h }); }))])]), tb = el('tbody'); t.append(tb);
    window.TG_VALORACION.forEach(function (c) {
      var nums = vs.map(function (v) { return Number(v[c.id]); }).filter(function (n) { return n >= 1 && n <= 5; });
      var npv = vs.filter(function (v) { return v[c.id] === 'No puedo valorarlo'; }).length;
      tb.append(el('tr', {}, [c.id, c.criterio, nums.length ? (nums.reduce(function (a, b) { return a + b; }, 0) / nums.length).toFixed(2).replace('.', ',') : '—', nums.length, npv].map(function (x) { return el('td', { text: String(x) }); })));
    });
    $('resumen-val').replaceChildren(el('p', { class: 'nota', text: vs.length + ' valoración(es) registradas en tu cuenta. Describen solo a quienes respondieron; no son una muestra representativa.' }), t);
  }
  $('btn-val-csv').addEventListener('click', async function () {
    var vs = await todos('valoraciones').catch(function () { return []; });
    var cab = ['fecha', 'version', 'codigo', 'rol', 'grado', 'borrador'].concat(window.TG_VALORACION.map(function (c) { return c.id; })).concat(['P1', 'P2', 'P3', 'P4']);
    descargar('TecnoGuIA_valoraciones_docentes.csv', csv([cab].concat(vs.map(function (v) { return cab.map(function (k) { return v[k]; }); }))), 'text/csv;charset=utf-8');
  });

  /* ---------- Inicio ---------- */
  Promise.resolve().then(function () { return Promise.all([cargarPropias(), pintarFuncionales(), pintarRegistro(), pintarValoraciones()]); })
    .catch(function (e) { mensaje('estado-lista', e.message + ' Las actividades propias no se podrán guardar.', 'error'); });
  comprobarOllama(true);
};
