/* Folklore mini runtime.
   Renders the canvas template (sc-for, sc-if, {{bindings}}, onClick/onChange) in any browser.
   Re-renders by patching the DOM in place, so CSS animations and transitions keep working. */
(function () {
  class DCLogic {
    constructor(props) { this.props = props || {}; this.state = {}; }
    setState(o) { Object.assign(this.state, typeof o === 'function' ? o(this.state) : o); DC._schedule(); }
  }

  const get = (o, path) => path.split('.').reduce((a, k) => (a == null ? undefined : a[k]), o);
  const look = (scope, path) => { for (let i = scope.length - 1; i >= 0; i--) { const r = get(scope[i], path); if (r !== undefined) return r; } return undefined; };
  const esc = v => String(v).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

  function findClose(s, tag, from) {
    let depth = 0; const re = new RegExp('<' + tag + '[\\s>]|</' + tag + '>', 'g'); re.lastIndex = from; let m;
    while ((m = re.exec(s))) { if (m[0][1] === '/') { if (--depth === 0) return m.index; } else depth++; }
    throw new Error('unclosed ' + tag);
  }

  let handlers = [];
  function interp(s, scope) {
    s = s.replace(/\s(on[A-Z]\w*)="\{\{([^}]+)\}\}"/g, (_, ev, p) => {
      const fn = look(scope, p.trim());
      if (typeof fn !== 'function') return '';
      handlers.push(fn);
      return ' data-dc-' + ev.slice(2).toLowerCase() + '="' + (handlers.length - 1) + '"';
    });
    return s.replace(/\{\{([^}]+)\}\}/g, (_, p) => { const v = look(scope, p.trim()); return typeof v === 'function' || v == null ? '' : esc(v); });
  }
  function render(s, scope) {
    let out = '';
    for (;;) {
      const m = /<(sc-for|sc-if)\b([^>]*)>/.exec(s);
      if (!m) return out + interp(s, scope);
      out += interp(s.slice(0, m.index), scope);
      const close = findClose(s, m[1], m.index);
      const inner = s.slice(m.index + m[0].length, close), attrs = m[2];
      if (m[1] === 'sc-for') {
        const list = look(scope, attrs.match(/list="\{\{([^}]+)\}\}"/)[1].trim()) || [];
        const as = attrs.match(/as="(\w+)"/)[1];
        for (const it of list) out += render(inner, scope.concat([{ [as]: it }]));
      } else if (look(scope, attrs.match(/value="\{\{([^}]+)\}\}"/)[1].trim())) out += render(inner, scope);
      s = s.slice(close + m[1].length + 3);
    }
  }

  function morph(a, b) {
    if (a.nodeType !== b.nodeType || a.nodeName !== b.nodeName) { a.replaceWith(b.cloneNode(true)); return; }
    if (a.nodeType !== 1) { if (a.nodeValue !== b.nodeValue) a.nodeValue = b.nodeValue; return; }
    for (const at of [...a.attributes]) if (!b.hasAttribute(at.name) && !(a.nodeName === 'DETAILS' && at.name === 'open')) a.removeAttribute(at.name);
    for (const at of [...b.attributes]) if (a.getAttribute(at.name) !== at.value) a.setAttribute(at.name, at.value);
    if (a.nodeName === 'INPUT' && a.type === 'range' && b.hasAttribute('value')) a.value = b.getAttribute('value');
    const ac = [...a.childNodes], bc = [...b.childNodes];
    for (let i = 0; i < bc.length; i++) { if (i < ac.length) morph(ac[i], bc[i]); else a.appendChild(bc[i].cloneNode(true)); }
    for (let i = bc.length; i < ac.length; i++) ac[i].remove();
  }

  const DC = {
    _c: null, _root: null, _tpl: '', _queued: false,
    _draw() {
      DC._queued = false; handlers = [];
      const html = render(DC._tpl, [DC._c.renderVals()]);
      const t = document.createElement('template'); t.innerHTML = html;
      const box = document.createElement('div'); box.appendChild(t.content);
      const ac = [...DC._root.childNodes], bc = [...box.childNodes];
      for (let i = 0; i < bc.length; i++) { if (i < ac.length) morph(ac[i], bc[i]); else DC._root.appendChild(bc[i].cloneNode(true)); }
      for (let i = bc.length; i < ac.length; i++) ac[i].remove();
      DC._handlers = handlers;
    },
    _schedule() { if (!DC._queued) { DC._queued = true; requestAnimationFrame(DC._draw); } },
    mount(Comp, root, tpl) {
      DC._c = new Comp({}); DC._root = root; DC._tpl = tpl;
      const fire = (type) => (e) => {
        const el = e.target.closest('[data-dc-' + type + ']'); if (!el || !DC._root.contains(el)) return;
        const fn = DC._handlers[+el.getAttribute('data-dc-' + type)]; if (fn) fn(e);
      };
      root.addEventListener('click', fire('click'));
      root.addEventListener('input', fire('change'));
      DC._draw();
    }
  };
  window.DC = DC; window.DCLogic = DCLogic;
})();
