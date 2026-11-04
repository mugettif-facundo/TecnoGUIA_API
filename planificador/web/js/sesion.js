/* Planificador integrado a TecnoGUIA: usa la sesión de la API (cookie tecnoguia_sesion). */
(function () {
  'use strict';
  function pedir(metodo, ruta) {
    return fetch(ruta, { method: metodo, credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-TecnoGUIA': '1' } });
  }
  function el(tag, attrs, texto) {
    var e = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    if (texto) e.textContent = texto;
    return e;
  }
  function pintar(u) {
    var c = document.getElementById('sesion'); c.replaceChildren();
    c.append(el('span', {}, 'Sesión: ' + u.nombre + ' (' + u.perfil + ')'));
    c.append(el('a', { href: '/formulario' }, 'Generador con IA (NAP)'));
    if (u.perfil === 'administrador') {
      c.append(el('a', { href: '/administracion' }, 'Administración'));
      c.append(el('a', { href: '/planificador/admin' }, 'Actividades y banco compartido'));
    }
    c.append(el('a', { href: '/ingresar?cambiar=1' }, 'Cambiar contraseña'));
    var salir = el('button', { type: 'button' }, 'Cerrar sesión');
    salir.addEventListener('click', function () { pedir('DELETE', '/sesion').finally(function () { location.href = '/ingresar'; }); });
    c.append(salir);
  }
  pedir('GET', '/sesion').then(function (r) {
    if (r.status === 401 || r.status === 403) { location.href = '/ingresar'; throw new Error('sin sesión'); }
    return r.json();
  }).then(function (d) {
    var u = d.usuario;
    if (u.debe_cambiar_clave) { location.href = '/ingresar'; throw new Error('sin sesión'); }
    window.TG_USUARIO = u;
    return pedir('GET', '/planificador/api/compartidas').then(function (r) { return r.ok ? r.json() : []; }).then(function (lista) {
      var banco = window.TG_BANCO = window.TG_BANCO || [];
      lista.forEach(function (a) { if (!banco.some(function (x) { return x.id === a.id; })) banco.push(a); });
    }).then(function () { return u; });
  }).then(function (u) {
    window.TG_ARRANCAR(); pintar(u);
    var v = document.getElementById('version'); if (v) v.textContent += ' · planificador integrado a TecnoGUIA API';
  }).catch(function (e) {
    if (/sin sesión/.test(e.message)) return;
    var m = document.querySelector('main'); if (m) m.prepend(el('p', { class: 'caja error' }, 'No se pudo iniciar el planificador: ' + e.message));
  });
})();
