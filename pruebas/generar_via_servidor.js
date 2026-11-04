/* Prueba de generación con Ollama A TRAVÉS DEL SERVIDOR de TecnoGUIA (versión integrada 0.10.0).
   Genera los casos elegidos de P01–P36 / G01–G06 con el mismo motor de la página, pasando por
   /planificador/api/ollama/..., y guarda cada resultado también en la base (registro de generaciones del usuario).

   Uso (PowerShell, dentro de TecnoGUIA_API, con el servidor y Ollama abiertos):
     node pruebas/generar_via_servidor.js                       (los 6 casos mínimos: P01 P05 P09 G01 G03 G06)
     node pruebas/generar_via_servidor.js P01,P12,G02            (casos a elección)
     node pruebas/generar_via_servidor.js todos                  (las 36 generaciones, ~70 min)
   Pide usuario y contraseña (usá un docente de prueba; la contraseña no se muestra al escribirla).
   Variables opcionales: TG_URL (por defecto http://127.0.0.1:8000), TG_MODELO (por defecto qwen3:1.7b),
   TG_USUARIO y TG_CLAVE (para no escribirlos). */
var fs = require('fs'), path = require('path'), readline = require('readline');
var WEB = path.join(__dirname, '..', 'planificador', 'web');
var M = require(path.join(WEB, 'js', 'motor.js')), C = require(path.join(WEB, 'datos', 'corpus.js')), B = require(path.join(WEB, 'datos', 'banco.js')), P = require(path.join(WEB, 'datos', 'pruebas.js'));

var URL = (process.env.TG_URL || 'http://127.0.0.1:8000').replace(/\/+$/, ''), modelo = process.env.TG_MODELO || 'qwen3:1.7b';
var MINIMO = ['P01', 'P05', 'P09', 'G01', 'G03', 'G06'];
var pedidos = (process.argv[2] || '').trim();
var CONDICIONES = { duracion: '80', estudiantes: '25', dificultad: 'Intermedia', contexto: '', materiales: 'hojas de papel, cartón, cinta de papel, tijeras, lápices, reglas' };

function preguntar(texto, oculto) {
  return new Promise(function (ok) {
    var rl = readline.createInterface({ input: process.stdin, output: process.stdout, terminal: true });
    if (oculto) { rl._writeToOutput = function (s) { if (s.indexOf(texto) === 0) rl.output.write(s); else rl.output.write(''); }; }
    rl.question(texto, function (r) { rl.close(); if (oculto) process.stdout.write('\n'); ok(r); });
  });
}
function todosLosCasos() {
  return P.TG_PRUEBAS.filter(function (p) { return p.esperado.length; }).map(function (p) {
    return { id: p.id, tipo: p.tipo, grado: p.grado, consulta: p.consulta, esperado: p.esperado, datos: Object.assign({ grado: String(p.grado), contenido: p.consulta }, CONDICIONES) };
  }).concat(P.TG_CASOS_GENERACION.map(function (g) {
    return { id: g.id, tipo: g.contexto ? 'generación con contexto' : 'generación sin contexto', grado: g.grado, consulta: g.contenido, esperado: [g.registro],
      datos: { grado: String(g.grado), contenido: g.contenido, duracion: String(g.duracion), estudiantes: String(g.estudiantes), dificultad: g.dificultad, materiales: g.materiales, contexto: g.contexto } };
  }));
}

async function main() {
  var usuario = process.env.TG_USUARIO || await preguntar('Usuario: '), clave = process.env.TG_CLAVE || await preguntar('Contraseña: ', true);
  var cab = { 'Content-Type': 'application/json', 'X-TecnoGUIA': '1' };
  var r = await fetch(URL + '/sesion', { method: 'POST', headers: cab, body: JSON.stringify({ usuario: usuario, clave: clave }) });
  if (!r.ok) throw new Error('No se pudo ingresar (' + r.status + '): ' + ((await r.json().catch(function () { return {}; })).detail || ''));
  var u = (await r.json()).usuario;
  if (u.debe_cambiar_clave) throw new Error('Ese usuario tiene contraseña temporal: ingresá una vez desde el navegador y cambiala.');
  var cookie = (r.headers.getSetCookie ? r.headers.getSetCookie() : []).map(function (c) { return c.split(';')[0]; }).join('; ');
  if (!cookie) throw new Error('El servidor no devolvió la cookie de sesión.');
  var h = Object.assign({ Cookie: cookie }, cab);
  console.log('Ingresó ' + u.nombre + ' (' + u.perfil + ').');

  var ver = await (await fetch(URL + '/planificador/api/ollama/api/version', { headers: h })).json().catch(function () { return {}; });
  if (!ver.version) throw new Error('Ollama no responde a través del servidor. Abrí Ollama y volvé a intentar.');
  var etiquetas = await (await fetch(URL + '/planificador/api/ollama/api/tags', { headers: h })).json();
  if (!(etiquetas.models || []).some(function (m) { return m.name === modelo; })) throw new Error('El modelo ' + modelo + ' no está descargado (ollama pull ' + modelo + ').');

  var casos = todosLosCasos(), ids = pedidos === 'todos' ? casos.map(function (c) { return c.id; }) : (pedidos ? pedidos.split(',') : MINIMO).map(function (s) { return s.trim().toUpperCase(); });
  casos = ids.map(function (id) { var c = casos.filter(function (x) { return x.id === id; })[0]; if (!c) throw new Error('No existe el caso ' + id + ' (o es un caso sin cobertura).'); return c; });
  var ahora = new Date(), p2 = function (n) { return String(n).padStart(2, '0'); };
  var carpeta = path.join(__dirname, '..', 'evaluaciones', 'integrada_' + ahora.getFullYear() + p2(ahora.getMonth() + 1) + p2(ahora.getDate()) + '_' + p2(ahora.getHours()) + p2(ahora.getMinutes()));
  fs.mkdirSync(carpeta, { recursive: true });
  console.log('Generando ' + casos.length + ' borradores con ' + modelo + ' (Ollama ' + ver.version + ') por ' + URL + ' → ' + carpeta + '\n');

  var resumen = [];
  for (var i = 0; i < casos.length; i++) {
    var p = casos[i], datos = p.datos;
    var rec = M.recuperar(p.consulta, p.grado, C.TG_CORPUS), reg = rec.registros[0].registro;
    var exps = M.experienciasRelevantes(p.consulta, M.experiencias(reg.id, p.grado, B, [])).slice(0, 1);
    var fila = { id: p.id, tipo: p.tipo, grado: p.grado, consulta: p.consulta, esperado: p.esperado.join(', '), obtenido: reg.id,
      recuperacion: p.esperado.indexOf(reg.id) >= 0 ? 'pertinente' : 'no pertinente', experiencias: exps.map(function (a) { return a.id; }).join(', '),
      fecha: new Date().toISOString(), version: M.VERSION, modelo: modelo, ollama: ver.version, via: URL + '/planificador/api/ollama', usuario: u.usuario, condiciones: datos };
    var inicio = Date.now();
    process.stdout.write(p.id + ' (' + (i + 1) + '/' + casos.length + ') ' + reg.id + '… ');
    try {
      var resp = await fetch(URL + '/planificador/api/ollama/api/chat', { method: 'POST', headers: h, body: JSON.stringify(M.pedidoOllama(datos, reg, exps, modelo)), signal: AbortSignal.timeout(600000) });
      if (!resp.ok) throw new Error('el servidor respondió ' + resp.status);
      var json = await resp.json(), b = JSON.parse(json.message.content);
      var avisos = M.controlar(b, datos), ev = M.evaluarBorrador(b, datos, reg);
      var meta = { modo: 'IA local (Ollama)', modelo: modelo, fecha: new Date().toISOString().slice(0, 16).replace('T', ' ') + ' UTC', datos: datos, registro: reg,
        documento: C.TG_DOCUMENTOS[reg.documento], documentos: C.TG_DOCUMENTOS, experiencias: exps, avisos: avisos, indicadores: ev, id: p.id };
      Object.assign(fila, { resultado: 'generado', segundos: Math.round((Date.now() - inicio) / 1000), corte_por_longitud: json.done_reason === 'length', avisos: avisos, indicadores: ev, borrador: b, texto: M.aTexto(b, meta) });
      console.log('generado en ' + fila.segundos + ' s · adecuación ' + ev.adecuacion.nivel + ' · avisos ' + avisos.length);
    } catch (e) {
      Object.assign(fila, { resultado: 'error: ' + e.message, segundos: Math.round((Date.now() - inicio) / 1000) });
      console.log('ERROR: ' + e.message);
    }
    fs.writeFileSync(path.join(carpeta, p.id + '.json'), JSON.stringify(fila, null, 1), 'utf8');
    // queda también en la base, en el registro de generaciones del usuario (se ve en la pestaña Evaluación)
    var guardado = await fetch(URL + '/planificador/api/almacen/registro', { method: 'PUT', headers: h, body: JSON.stringify({
      fecha: fila.fecha, version: M.VERSION, caso: p.id, borrador: p.id, grado: p.grado, consulta: p.consulta, registro_usado: reg.id, experiencias: fila.experiencias,
      modo: 'IA local (Ollama) vía servidor', modelo: modelo, segundos: fila.segundos, adecuacion: fila.indicadores ? fila.indicadores.adecuacion.nivel : '', avisos: fila.avisos ? fila.avisos.length : '', resultado: fila.resultado === 'generado' ? 'generado' : fila.resultado }) });
    fila.guardado_en_base = guardado.ok;
    resumen.push(fila);
  }
  var enBase = await (await fetch(URL + '/planificador/api/almacen/registro', { headers: h })).json();
  var ok = resumen.filter(function (f) { return f.resultado === 'generado'; });
  var seg = ok.map(function (f) { return f.segundos; });
  var lineas = ['Prueba de generación vía servidor — TecnoGUIA integrada', 'Fecha: ' + new Date().toISOString(), 'Servidor: ' + URL + ' · usuario: ' + u.usuario + ' (' + u.perfil + ')',
    'Modelo: ' + modelo + ' · Ollama ' + ver.version + ' · motor ' + M.VERSION, '',
    'Casos pedidos: ' + resumen.length + ' · generados: ' + ok.length + ' · con error: ' + (resumen.length - ok.length),
    'Recuperación pertinente: ' + resumen.filter(function (f) { return f.recuperacion === 'pertinente'; }).length + '/' + resumen.length,
    'Guardados en la base: ' + resumen.filter(function (f) { return f.guardado_en_base; }).length + '/' + resumen.length + ' (filas del registro del usuario ahora: ' + enBase.length + ')',
    seg.length ? 'Tiempo por borrador: ' + Math.min.apply(null, seg) + '–' + Math.max.apply(null, seg) + ' s, promedio ' + (seg.reduce(function (a, b) { return a + b; }, 0) / seg.length).toFixed(1) + ' s' : '',
    'Con ficha del banco: ' + ok.filter(function (f) { return f.experiencias; }).length + ' · con avisos: ' + ok.filter(function (f) { return f.avisos.length; }).length, '',
    'Caso | Esperado | Obtenido | Recuperación | Resultado | Seg | Adecuación | Avisos | En base'].concat(resumen.map(function (f) {
      return [f.id, f.esperado, f.obtenido, f.recuperacion, f.resultado, f.segundos, f.indicadores ? f.indicadores.adecuacion.nivel : '-', f.avisos ? f.avisos.length : '-', f.guardado_en_base ? 'sí' : 'no'].join(' | '); }));
  fs.writeFileSync(path.join(carpeta, 'RESUMEN.txt'), lineas.join('\n') + '\n', 'utf8');
  console.log('\n' + lineas.join('\n') + '\n\nResultados en ' + carpeta);
}
main().catch(function (e) { console.error('\nNo se pudo ejecutar: ' + e.message); process.exitCode = 1; });
