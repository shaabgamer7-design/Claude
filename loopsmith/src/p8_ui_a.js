
/* ===================== State ===================== */
const K_CUR = "loopsmith.v2.current", K_TAKES = "loopsmith.v2.takes", K_TAB = "loopsmith.v2.tab";
let spec = null, selId = null, activeStyle = null, curTab = "create";
let playing = !matchMedia("(prefers-reduced-motion: reduce)").matches, startTime = performance.now(), pausedT = .3, dirty = true, lastFi = -1;
let variants = [], varLabels = [], activeVar = 0;
const hist = []; let hi = -1;
const view = $("view"), vctx = view.getContext("2d");

function cfg(){
  const size = +$("xSize").value, [aw, ah] = $("aspect").value.split(":").map(Number);
  const W = aw >= ah ? even(size) : even(size * aw / ah), H = aw >= ah ? even(size * ah / aw) : even(size);
  return { W, H, fps: +$("fps").value, dur: +$("dur").value, aspect: $("aspect").value };
}
const frameCount = () => { const c = cfg(); return Math.max(2, Math.round(c.fps * c.dur)); };
const sel = () => spec.layers.find(l => l.id === selId) || null;

/* ===================== History ===================== */
function pushHist(){ hist.splice(hi + 1); hist.push(JSON.stringify(spec)); if (hist.length > 80) hist.shift(); hi = hist.length - 1; updateUndo(); }
function updateUndo(){ $("undoBtn").disabled = hi <= 0; $("redoBtn").disabled = hi >= hist.length - 1; }
function undo(){ if (hi <= 0) return; hi--; spec = normSpec(JSON.parse(hist[hi])); afterSpec(true); updateUndo(); }
function redo(){ if (hi >= hist.length - 1) return; hi++; spec = normSpec(JSON.parse(hist[hi])); afterSpec(true); updateUndo(); }

/* ===================== Spec lifecycle ===================== */
function setSpec(s, opt = {}){
  spec = normSpec(s);
  if (!opt.keepSel || !sel()) selId = defaultSel();
  if (opt.push !== false) pushHist();
  afterSpec(true);
}
function defaultSel(){ const pref = ["text", "shape", "image", "slides", "particles"]; for (const k of pref){ const l = [...spec.layers].reverse().find(x => x.kind === k && !x.role); if (l) return l.id; } return spec.layers[spec.layers.length - 1]?.id || null; }
let saveTimer = 0, jsonTimer = 0;
function afterSpec(full){
  dirty = true;
  renderLayerList(); if (full) renderInspector();
  scheduleStrip(); scheduleSeam();
  clearTimeout(jsonTimer); jsonTimer = setTimeout(() => { $("json").textContent = JSON.stringify(spec, null, 2); }, 250);
  clearTimeout(saveTimer); saveTimer = setTimeout(() => lsSet(K_CUR, JSON.stringify({ spec, prompt: $("prompt").value })), 600);
  $("cornerTitle").textContent = spec.title.toUpperCase();
  if (full) readCaptions();
  refreshPhotoFx();
}
function commit(){ pushHist(); afterSpec(false); }
function soft(){ dirty = true; updateSelRow(); scheduleStrip(); scheduleSeam(); }

/* ===================== Preview ===================== */
function layoutView(){
  const st = $("stage"), cs = getComputedStyle(st);
  const availW = st.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
  const availH = Math.min(window.innerHeight * .62, 640), c = cfg(), ar = c.W / c.H;
  let w = Math.max(80, availW), h = w / ar; if (h > availH){ h = availH; w = h * ar; }
  view.style.width = Math.floor(w) + "px"; view.style.height = Math.floor(h) + "px";
  const dpr = Math.min(2, window.devicePixelRatio || 1); let bw = Math.round(w * dpr), bh = Math.round(h * dpr);
  const cap = 960 / Math.max(bw, bh); if (cap < 1){ bw = Math.round(bw * cap); bh = Math.round(bh * cap); }
  if (view.width !== bw || view.height !== bh){ view.width = bw; view.height = bh; }
  $("cornerSpec").textContent = `${c.W}×${c.H} · ${c.fps} fps · ${c.dur}s`;
  dirty = true;
}
function drawSelMarker(){
  const L = sel(); if (curTab !== "edit" || !L || L.hidden || !("x" in KINDS[L.kind].props) || (L.kind === "image" && L.frame === "full")) return;
  const W = view.width, H = view.height, S = Math.min(W, H), x = L.x * W, y = L.y * H, r = Math.max(S * .05, (L.size || .1) * S * (L.kind === "text" ? .9 : .5));
  vctx.save(); vctx.setTransform(1, 0, 0, 1, 0, 0); vctx.globalAlpha = 1; vctx.shadowBlur = 0; vctx.lineWidth = Math.max(1, S / 320);
  vctx.setLineDash([S / 70, S / 70]); vctx.strokeStyle = "rgba(255,255,255,.9)"; vctx.beginPath(); vctx.arc(x, y, r, 0, TAU); vctx.stroke();
  vctx.lineDashOffset = S / 70; vctx.strokeStyle = "rgba(0,0,0,.6)"; vctx.stroke(); vctx.restore();
}
let varTick = 0, hoverTpl = null;
function tick(now){
  const c = cfg(), n = Math.max(2, Math.round(c.fps * c.dur));
  const t = playing ? wrap01((now - startTime) / 1000 / c.dur) : pausedT;
  const fi = Math.floor(t * n) % n, tq = fi / n;
  if (dirty || fi !== lastFi){
    renderFrame(vctx, spec, tq, view.width, view.height); drawSelMarker();
    if (fi !== lastFi){
      lastFi = fi;
      $("scrub").value = Math.floor(t * 1000);
      const sec = tq * c.dur; $("tc").textContent = `${String(Math.floor(sec / 60)).padStart(2, "0")}:${(sec % 60).toFixed(2).padStart(5, "0")} · ${fi + 1}/${n}`;
      const strip = $("strip").children, si = Math.min(strip.length - 1, Math.floor(tq * strip.length));
      for (let i = 0; i < strip.length; i++) strip[i].classList.toggle("on", i === si);
      if ((varTick++ & 1) === 0) renderVariations(tq);
      if (hoverTpl) renderFrame(hoverTpl.ctx, hoverTpl.spec, tq, hoverTpl.canvas.width, hoverTpl.canvas.height);
    }
    dirty = false;
  }
  requestAnimationFrame(tick);
}
function seek(t){ playing = false; pausedT = wrap01(t); setPlayBtn(); dirty = true; lastFi = -1; }
function setPlayBtn(){ $("playBtn").textContent = playing ? "❚❚" : "▶"; $("playBtn").setAttribute("aria-label", playing ? "Pause" : "Play"); }
function togglePlay(){ const c = cfg(); if (playing){ pausedT = wrap01((performance.now() - startTime) / 1000 / c.dur); playing = false; } else { startTime = performance.now() - pausedT * c.dur * 1000; playing = true; } setPlayBtn(); dirty = true; }
function stepFrame(d){ const n = frameCount(); const c = cfg(); const cur = playing ? wrap01((performance.now() - startTime) / 1000 / c.dur) : pausedT; const fi = (Math.floor(cur * n) + d + n) % n; seek(fi / n + .0001); }
const curT = () => { const c = cfg(); return playing ? wrap01((performance.now() - startTime) / 1000 / c.dur) : pausedT; };

/* frame strip */
let stripTimer = 0;
function scheduleStrip(){ clearTimeout(stripTimer); stripTimer = setTimeout(buildStrip, 220); }
function buildStrip(){
  const c = cfg(), n = Math.max(2, Math.round(c.fps * c.dur)), count = Math.min(12, n), host = $("strip"); host.textContent = "";
  for (let i = 0; i < count; i++){
    const cv = document.createElement("canvas"), h = 54, w = Math.max(24, Math.round(h * c.W / c.H)), t = Math.floor(i / count * n) / n;
    cv.width = w * 2; cv.height = h * 2; cv.style.width = w + "px"; cv.style.height = h + "px";
    renderFrame(cv.getContext("2d"), spec, t, cv.width, cv.height);
    cv.tabIndex = 0; cv.setAttribute("role", "button"); cv.setAttribute("aria-label", `Jump to frame ${Math.round(t * n) + 1} of ${n}`); cv.title = `Frame ${Math.round(t * n) + 1} of ${n}`;
    cv.onclick = () => seek(t + .0001); cv.onkeydown = e => { if (e.key === "Enter" || e.key === " "){ e.preventDefault(); seek(t + .0001); } };
    host.appendChild(cv);
  }
  $("frameHint").textContent = `${n} frames · ${c.dur}s at ${c.fps} fps · click to jump`;
  lastFi = -1;
}

/* loop seam check: compares last→first frame change with ordinary frame-to-frame change */
let seamTimer = 0; const seamCv = document.createElement("canvas"), seamCtx = seamCv.getContext("2d", { willReadFrequently: true });
function scheduleSeam(){ clearTimeout(seamTimer); seamTimer = setTimeout(runSeam, 450); }
function imgDiff(a, b){ let s = 0; for (let i = 0; i < a.length; i += 4) s += Math.abs(a[i] - b[i]) + Math.abs(a[i + 1] - b[i + 1]) + Math.abs(a[i + 2] - b[i + 2]); return s / (a.length / 4 * 3); }
function runSeam(){
  const c = cfg(), n = Math.min(150, frameCount()), w = 64, h = Math.max(16, Math.round(64 * c.H / c.W));
  seamCv.width = w; seamCv.height = h;
  let first = null, prev = null, sum = 0, mx = 0;
  for (let i = 0; i < n; i++){ renderFrame(seamCtx, spec, i / n, w, h); const d = seamCtx.getImageData(0, 0, w, h).data; if (prev){ const df = imgDiff(prev, d); sum += df; if (df > mx) mx = df; } else first = d; prev = d; }
  const seam = imgDiff(prev, first), avg = sum / (n - 1), ok = seam <= Math.max(avg * 1.8, mx * 1.05, .6), el = $("seam");
  el.className = "seam " + (ok ? "ok" : "warn"); el.textContent = ok ? "✓ Seamless loop" : "Loop jumps at the seam";
  el.title = `Change across the loop point ${seam.toFixed(2)}; average frame step ${avg.toFixed(2)}; largest ${mx.toFixed(2)}.` + (ok ? "" : " A typewriter, cut transition or very fast motion can cause this.");
}

/* ===================== Tabs ===================== */
function setTab(name){
  for (const n of ["create", "edit", "export"]){ $("tab-" + n).setAttribute("aria-selected", String(n === name)); $("pane-" + n).hidden = n !== name; }
  curTab = name; dirty = true; lsSet(K_TAB, name);
}

/* ===================== Layers panel ===================== */
function miniBtn(label, title, fn){ const b = document.createElement("button"); b.className = "mini"; b.type = "button"; b.textContent = label; b.title = title; b.setAttribute("aria-label", title); b.onclick = e => { e.stopPropagation(); fn(); }; return b; }
function renderLayerList(){
  const host = $("layerList"); host.textContent = "";
  for (let idx = spec.layers.length - 1; idx >= 0; idx--){
    const L = spec.layers[idx], row = document.createElement("div");
    row.className = "lrow" + (L.id === selId ? " sel" : "") + (L.hidden ? " off" : ""); row.dataset.id = L.id;
    row.setAttribute("role", "option"); row.setAttribute("aria-selected", String(L.id === selId)); row.tabIndex = 0;
    const eye = miniBtn(L.hidden ? "◌" : "◉", L.hidden ? "Show layer" : "Hide layer", () => { L.hidden = !L.hidden; commit(); });
    const nm = document.createElement("div"); nm.className = "nm";
    const b = document.createElement("b"); b.textContent = (L.role ? "Caption" : KINDS[L.kind].label) + " "; const sm = document.createElement("small"); sm.textContent = summary(L); nm.append(b, sm);
    const btns = document.createElement("div"); btns.className = "lbtns";
    btns.append(miniBtn("↑", "Move up", () => moveLayer(L, 1)), miniBtn("↓", "Move down", () => moveLayer(L, -1)), miniBtn("⧉", "Duplicate", () => dupLayer(L)), miniBtn("✕", "Delete", () => delLayer(L)));
    row.append(eye, nm, btns);
    row.onclick = () => selectLayer(L.id);
    row.onkeydown = e => { if (e.target !== row) return; if (e.key === "Enter" || e.key === " "){ e.preventDefault(); selectLayer(L.id); } if (e.key === "Delete" || e.key === "Backspace"){ e.preventDefault(); delLayer(L); } };
    host.appendChild(row);
  }
  $("layerCount").textContent = spec.layers.length + " layers";
}
function updateSelRow(){ const L = sel(); if (!L) return; const row = $("layerList").querySelector(`[data-id="${L.id}"] small`); if (row) row.textContent = summary(L); }
function selectLayer(id){ selId = id; renderLayerList(); renderInspector(); dirty = true; }
function moveLayer(L, d){ const a = spec.layers, i = a.indexOf(L), j = i + d; if (j < 0 || j >= a.length) return; a.splice(i, 1); a.splice(j, 0, L); commit(); }
function dupLayer(L){ const c = normLayer({ ...clone(L), id: nid(), role: undefined }); if ("x" in c) c.x = clamp(c.x + .05, -.2, 1.2); if ("y" in c) c.y = clamp(c.y + .05, -.2, 1.2); spec.layers.splice(spec.layers.indexOf(L) + 1, 0, c); selId = c.id; commit(); renderInspector(); }
function delLayer(L){ spec.layers = spec.layers.filter(l => l !== L); if (L.role === "cap-top") $("capTop").value = ""; if (L.role === "cap-bot") $("capBot").value = ""; if (selId === L.id) selId = defaultSel(); commit(); renderInspector(); }
const ADD_DEFAULTS = {
  text: { text: "Your text", size: .14, shadow: "rgba(0,0,0,0.35)" }, shape: { shape: "star", color: "#ffd23f", glow: .4 }, particles: { shape: "star", colors: ["#ffffff", "#ffe08a"], motion: "twinkle", count: 30, size: .03, glow: .5 },
  image: { motion: "kenburns" }, slides: {}, background: {}, pattern: {}, waves: {}, rings: { colors: ["#ffffff"] }, rays: { colors: ["rgba(255,255,255,0.2)", "rgba(255,255,255,0)"] }, orbit: { glow: .6 }, blob: { glow: .4 }, bars: {}, fx: {}
};
function addLayer(kind){
  const extra = { ...ADD_DEFAULTS[kind] };
  const ids = [...IMAGES.keys()];
  if (kind === "image") extra.src = ids[0] || "";
  if (kind === "slides") extra.srcs = ids;
  const L = normLayer({ kind, ...extra });
  const ci = spec.layers.findIndex(l => l.role);
  if (kind === "background") spec.layers.unshift(L); else if (ci < 0) spec.layers.push(L); else spec.layers.splice(ci, 0, L);
  selId = L.id; commit(); renderInspector();
}

/* ===================== Inspector ===================== */
function fmtVal(def, v){ return def.fmt ? def.fmt(v) : def.t === "int" ? String(v) : (+v).toFixed(def.step && def.step < .01 ? 3 : 2); }
function colorInput(css, onInput, onChange, label){
  const p = parseColor(css) || [255, 255, 255, 1], i = document.createElement("input"); i.type = "color"; i.value = toHex(p); i.dataset.css = css || toHex(p); i.setAttribute("aria-label", label || "Color");
  const alpha = p[3];
  i.oninput = () => { const q = parseColor(i.value); q[3] = alpha; const v = toCss(q); i.dataset.css = v; onInput(v); };
  i.onchange = () => onChange && onChange();
  return i;
}
function renderInspector(){
  const box = $("insp"); box.textContent = "";
  const L = sel();
  if (!L){ $("inspTitle").textContent = "Layer settings"; const p = document.createElement("p"); p.className = "note fld wide"; p.textContent = "Select a layer to edit it, or click an object on the preview."; box.appendChild(p); return; }
  $("inspTitle").textContent = (L.role ? "Caption" : KINDS[L.kind].label) + " settings";
  for (const [k, def] of Object.entries(KINDS[L.kind].props)) box.appendChild(field(L, k, def));
}
function field(L, k, def){
  const wrap = document.createElement("div"), head = document.createElement("span"), fid = "fld-" + k;
  wrap.className = "fld" + (["colors", "images"].includes(def.t) || def.area ? " wide" : "");
  head.textContent = def.label; wrap.appendChild(head);
  const set = (v, final) => { L[k] = coerce(def, v); if (final) commit(); else soft(); };
  switch (def.t){
    case "range": case "int": {
      const out = document.createElement("output"); out.textContent = fmtVal(def, L[k]); head.appendChild(out);
      const r = document.createElement("input"); r.type = "range"; r.id = fid; r.min = def.min; r.max = def.max; r.step = def.step || (def.t === "int" ? 1 : .01); r.value = L[k]; r.dataset.key = k; r.setAttribute("aria-label", def.label);
      r.oninput = () => { set(+r.value); out.textContent = fmtVal(def, L[k]); }; r.onchange = () => commit();
      wrap.appendChild(r); break; }
    case "color": wrap.appendChild(colorInput(L[k], v => set(v), () => commit(), def.label)); break;
    case "colorOpt": {
      const row = document.createElement("div"); row.className = "swatches";
      const cb = document.createElement("input"); cb.type = "checkbox"; cb.checked = L[k] != null; cb.setAttribute("aria-label", def.label + " on");
      const ci = colorInput(L[k] || def.on, v => set(v), () => commit(), def.label); ci.disabled = L[k] == null;
      cb.onchange = () => { ci.disabled = !cb.checked; set(cb.checked ? ci.dataset.css : null, true); };
      const lb = document.createElement("label"); lb.className = "check"; lb.append(cb, document.createTextNode("On"));
      row.append(lb, ci); wrap.appendChild(row); break; }
    case "colors": {
      const row = document.createElement("div"); row.className = "swatches";
      const redraw = () => { row.textContent = "";
        L[k].forEach((c, i) => { const sw = document.createElement("span"); sw.className = "sw";
          sw.appendChild(colorInput(c, v => { L[k][i] = v; soft(); }, () => commit(), `${def.label} ${i + 1}`));
          if (L[k].length > 1) sw.appendChild(miniBtn("✕", "Remove color", () => { L[k].splice(i, 1); commit(); redraw(); }));
          row.appendChild(sw); });
        if (L[k].length < (def.max || 6)) row.appendChild(miniBtn("＋", "Add color", () => { L[k].push(hueShift(L[k][L[k].length - 1], 40)); commit(); redraw(); })); };
      redraw(); wrap.appendChild(row); break; }
    case "select": {
      const s = document.createElement("select"); s.id = fid; s.setAttribute("aria-label", def.label);
      def.opts.forEach(o => { const op = document.createElement("option"); op.value = o; op.textContent = k === "font" ? FONTS[o].label : pretty(o); s.appendChild(op); });
      s.value = L[k]; s.onchange = () => set(s.value, true); wrap.appendChild(s); break; }
    case "text": {
      const inp = document.createElement(def.area ? "textarea" : "input"); if (!def.area) inp.type = "text"; else { inp.rows = 2; inp.style.minHeight = "56px"; }
      inp.id = fid; inp.value = L[k]; inp.maxLength = def.max || 80; inp.setAttribute("aria-label", def.label);
      if (k === "glyph") inp.placeholder = "e.g. 🍕 🚀 ✨";
      inp.oninput = () => { set(inp.value); if (L.role === "cap-top") $("capTop").value = inp.value; if (L.role === "cap-bot") $("capBot").value = inp.value; };
      inp.onchange = () => commit(); wrap.appendChild(inp); break; }
    case "check": {
      const lb = document.createElement("label"); lb.className = "check"; const cb = document.createElement("input"); cb.type = "checkbox"; cb.checked = !!L[k];
      cb.onchange = () => set(cb.checked, true); lb.append(cb, document.createTextNode(def.label)); head.remove(); wrap.appendChild(lb); break; }
    case "image": {
      if (!IMAGES.size){ const p = document.createElement("p"); p.className = "note"; p.textContent = "Add a photo in the Create tab first."; wrap.appendChild(p); break; }
      const s = document.createElement("select"); s.setAttribute("aria-label", def.label);
      for (const [id, rec] of IMAGES){ const op = document.createElement("option"); op.value = id; op.textContent = rec.name; s.appendChild(op); }
      if (!IMAGES.has(L[k])){ const op = document.createElement("option"); op.value = L[k]; op.textContent = "Missing photo"; s.appendChild(op); }
      s.value = L[k]; s.onchange = () => set(s.value, true); wrap.appendChild(s); break; }
    case "images": {
      if (!IMAGES.size){ const p = document.createElement("p"); p.className = "note"; p.textContent = "Add photos in the Create tab first."; wrap.appendChild(p); break; }
      const list = document.createElement("div"); list.className = "checks";
      for (const [id, rec] of IMAGES){ const lb = document.createElement("label"); lb.className = "check"; const cb = document.createElement("input"); cb.type = "checkbox"; cb.checked = L[k].includes(id);
        cb.onchange = () => { const s2 = new Set(L[k]); if (cb.checked) s2.add(id); else s2.delete(id); set([...IMAGES.keys()].filter(x => s2.has(x)), true); };
        lb.append(cb, document.createTextNode(rec.name)); list.appendChild(lb); }
      wrap.appendChild(list); break; }
    case "seed": { const b = document.createElement("button"); b.type = "button"; b.className = "small"; b.textContent = "Reshuffle"; b.onclick = () => set(Math.floor(Math.random() * 1e9), true); wrap.appendChild(b); break; }
  }
  return wrap;
}

/* ===================== Stage interaction ===================== */
let drag = null;
function stagePoint(e){ const r = view.getBoundingClientRect(); return [(e.clientX - r.left) / r.width, (e.clientY - r.top) / r.height]; }
function hitTest(px, py){
  const W = view.width, H = view.height, S = Math.min(W, H);
  for (let i = spec.layers.length - 1; i >= 0; i--){
    const L = spec.layers[i]; if (L.hidden || !("x" in KINDS[L.kind].props) || (L.kind === "image" && L.frame === "full") || L.kind === "particles" && !["burst", "swirl", "fountain"].includes(L.motion)) continue;
    const dx = (px - L.x) * W / S, dy = (py - L.y) * H / S;
    if (L.kind === "text"){ const half = Math.min(.48 * W / S, L.size * Math.max(2, L.text.length) * .32); if (Math.abs(dx) < half && Math.abs(dy) < L.size * .8) return L; continue; }
    if (Math.hypot(dx, dy) < Math.max(.06, (L.size || .2) / 2)) return L;
  }
  return null;
}
view.addEventListener("pointerdown", e => {
  const [px, py] = stagePoint(e), hit = hitTest(px, py);
  if (hit && hit.id !== selId) selectLayer(hit.id);
  const L = hit || null; if (!L) return;
  drag = { id: L.id, ox: L.x - px, oy: L.y - py, moved: false };
  view.setPointerCapture(e.pointerId); e.preventDefault();
});
view.addEventListener("pointermove", e => {
  if (!drag) return; const L = spec.layers.find(l => l.id === drag.id); if (!L) return;
  const [px, py] = stagePoint(e); L.x = +clamp(px + drag.ox, -.2, 1.2).toFixed(3); L.y = +clamp(py + drag.oy, -.2, 1.2).toFixed(3); drag.moved = true; dirty = true;
  for (const k of ["x", "y"]){ const r = $("fld-" + k); if (r){ r.value = L[k]; const out = r.parentElement.querySelector("output"); if (out) out.textContent = (+L[k]).toFixed(2); } }
});
const endDrag = () => { if (drag && drag.moved){ commit(); } else if (drag && curTab !== "edit") setTab("edit"); drag = null; };
view.addEventListener("pointerup", endDrag); view.addEventListener("pointercancel", () => { drag = null; });
