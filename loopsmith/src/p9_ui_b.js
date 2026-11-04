
/* ===================== Takes (variations) ===================== */
function setVariants(vs, labels, active = 0){ variants = vs; varLabels = labels; activeVar = active; renderVarTiles(); }
function renderVarTiles(){
  const host = $("vars"); host.textContent = ""; const c = cfg();
  variants.forEach((v, i) => {
    const b = document.createElement("button"); b.type = "button"; b.className = "var" + (i === activeVar ? " on" : ""); b.setAttribute("aria-label", `Use take ${i + 1}: ${varLabels[i] || v.title}`);
    const cv = document.createElement("canvas"), tw = 150, th = Math.round(tw * c.H / c.W); cv.width = tw * 2; cv.height = th * 2;
    const lab = document.createElement("span"); lab.className = "vl"; lab.textContent = varLabels[i] || ("Take " + (i + 1));
    b.append(cv, lab); b.onclick = () => { activeVar = i; [...host.children].forEach((x, j) => x.classList.toggle("on", j === i)); setSpec(clone(v)); };
    host.appendChild(b); renderFrame(cv.getContext("2d"), v, .3, cv.width, cv.height);
  });
}
function renderVariations(t){ const tiles = $("vars").querySelectorAll("canvas"); tiles.forEach((cv, i) => { if (variants[i]) renderFrame(cv.getContext("2d"), variants[i], t, cv.width, cv.height); }); }

/* ===================== History (recent takes) ===================== */
function loadTakes(){ try { const a = JSON.parse(lsGet(K_TAKES) || "[]"); return Array.isArray(a) ? a : []; } catch { return []; } }
function addTake(label, sp){ const a = loadTakes(); a.unshift({ label: String(label || sp.title).slice(0, 60), spec: sp, ts: Date.now() }); lsSet(K_TAKES, JSON.stringify(a.slice(0, 12))); renderTakes(); }
function renderTakes(){
  const host = $("takes"), a = loadTakes(); host.textContent = "";
  if (!a.length){ const p = document.createElement("p"); p.className = "empty"; p.textContent = "Scenes you generate appear here, so you can return to them."; host.appendChild(p); return; }
  a.forEach(tk => {
    let sp; try { sp = normSpec(tk.spec); } catch { return; }
    const b = document.createElement("button"); b.type = "button"; b.className = "take"; b.title = tk.label;
    const cv = document.createElement("canvas"); cv.width = 192; cv.height = 192;
    const s = document.createElement("span"); s.textContent = tk.label;
    b.append(cv, s); b.onclick = () => { setSpec(sp); status("Restored “" + tk.label + "”.", "ok"); };
    host.appendChild(b); renderFrame(cv.getContext("2d"), sp, .3, 192, 192);
  });
}

/* ===================== Templates ===================== */
let tplCat = "All";
function renderTplCats(){
  const host = $("tplCats"); host.textContent = "";
  TPL_CATS.forEach(cat => { const b = document.createElement("button"); b.type = "button"; b.className = "chip"; b.textContent = cat; b.setAttribute("aria-pressed", String(cat === tplCat)); b.onclick = () => { tplCat = cat; renderTplCats(); renderTpls(); }; host.appendChild(b); });
}
function renderTpls(){
  const host = $("tpls"); host.textContent = ""; hoverTpl = null; let count = 0;
  TEMPLATES.forEach((tp, i) => {
    if (tplCat !== "All" && tp[0] !== tplCat) return; count++;
    const sp = tplSpec(i), b = document.createElement("button"); b.type = "button"; b.className = "tpl"; b.setAttribute("aria-label", "Use template " + tp[1]);
    const cv = document.createElement("canvas"); cv.width = 176; cv.height = 176; const ctx = cv.getContext("2d");
    const s = document.createElement("span"); s.textContent = tp[1];
    b.append(cv, s); host.appendChild(b); renderFrame(ctx, sp, .3, 176, 176);
    const enter = () => { hoverTpl = { canvas: cv, ctx, spec: sp }; };
    const leave = () => { if (hoverTpl && hoverTpl.canvas === cv){ hoverTpl = null; renderFrame(ctx, sp, .3, 176, 176); } };
    b.addEventListener("pointerenter", enter); b.addEventListener("focus", enter); b.addEventListener("pointerleave", leave); b.addEventListener("blur", leave);
    b.onclick = () => {
      const base = withCaptions(sp, captionLayers($("capTop").value.trim(), $("capBot").value.trim(), $("capStyle").value, $("capMotion").value));
      const styled = activeStyle ? restyle(normSpec(base), activeStyle) : normSpec(base);
      setSpec(styled); setVariants(remixSet(spec, Date.now() & 0xffff), ["Template", "Bolder", "Minimal", "Twist"]);
      status(`Template “${tp[1]}” loaded. Edit any layer, or generate your own.`, "ok");
    };
  });
  $("tplCount").textContent = count + " ready to edit";
}

/* ===================== Styles ===================== */
function renderStyles(){
  const host = $("styles"); host.textContent = "";
  Object.entries(STYLES).forEach(([k, st]) => {
    const b = document.createElement("button"); b.type = "button"; b.className = "chip"; b.textContent = st.label; b.setAttribute("aria-pressed", String(activeStyle === k)); b.title = st.cue;
    b.onclick = () => {
      if (activeStyle === k){ activeStyle = null; renderStyles(); status("Style cleared. New takes will choose their own look."); return; }
      activeStyle = k; renderStyles(); setSpec(restyle(spec, k), { keepSel: true });
      status(`Restyled as ${st.label}. New takes will use this style too. Undo restores the previous look.`, "ok");
    };
    host.appendChild(b);
  });
}

/* ===================== Captions ===================== */
let capTimer = 0;
function applyCaptions(final){
  const caps = captionLayers($("capTop").value.trim(), $("capBot").value.trim(), $("capStyle").value, $("capMotion").value);
  const old = spec.layers.filter(l => l.role === "cap-top" || l.role === "cap-bot");
  spec.layers = spec.layers.filter(l => !old.includes(l));
  caps.forEach(c => { const prev = old.find(o => o.role === c.role); if (prev) c.id = prev.id; spec.layers.push(c); });
  dirty = true; renderLayerList(); if (sel() == null || (sel() && sel().role)) renderInspector(); scheduleStrip(); scheduleSeam();
  clearTimeout(capTimer); if (final) commit(); else capTimer = setTimeout(commit, 700);
}
function readCaptions(){
  const top = spec.layers.find(l => l.role === "cap-top"), bot = spec.layers.find(l => l.role === "cap-bot");
  if (document.activeElement !== $("capTop")) $("capTop").value = top ? top.text : "";
  if (document.activeElement !== $("capBot")) $("capBot").value = bot ? bot.text : "";
}

/* ===================== Photos ===================== */
const PHOTO_FX = [["kenburns", "Ken Burns"], ["zoom", "Zoom punch"], ["pan", "Pan"], ["float", "Float"], ["shake", "Shake"], ["pulse", "Beat"], ["wobble", "Wobble"], ["glitch", "Glitch"], ["swing", "Swing"], ["spin", "Spin"]];
const SLIDE_FX = [["fade", "Crossfade"], ["slide", "Slide"], ["zoom", "Zoom"], ["wipe", "Wipe"], ["cut", "Hard cut"]];
function renderThumbs(){
  const host = $("thumbs"); host.textContent = "";
  for (const [id, rec] of IMAGES){
    const d = document.createElement("div"); d.className = "thumb"; const im = document.createElement("img"); im.src = rec.url; im.alt = rec.name;
    const x = document.createElement("button"); x.type = "button"; x.textContent = "✕"; x.setAttribute("aria-label", "Remove " + rec.name);
    x.onclick = () => { IMAGES.delete(id); URL.revokeObjectURL(rec.url); renderThumbs(); dirty = true; renderInspector(); renderLayerList(); refreshPhotoFx(); scheduleStrip(); };
    d.append(im, x); host.appendChild(d);
  }
}
function refreshPhotoFx(){
  const host = $("photoFx"), img = spec && spec.layers.find(l => l.kind === "image" && !l.hidden), sl = spec && spec.layers.find(l => l.kind === "slides" && !l.hidden);
  host.hidden = !(img || sl); if (host.hidden) return;
  const list = sl ? SLIDE_FX : PHOTO_FX, key = sl ? "trans" : "motion", target = sl || img;
  host.textContent = "";
  const lab = document.createElement("span"); lab.className = "hint"; lab.style.alignSelf = "center"; lab.textContent = sl ? "Transition:" : "Photo effect:"; host.appendChild(lab);
  list.forEach(([v, name]) => { const b = document.createElement("button"); b.type = "button"; b.className = "chip"; b.textContent = name; b.setAttribute("aria-pressed", String(target[key] === v));
    b.onclick = () => { target[key] = v; commit(); refreshPhotoFx(); if (selId === target.id) renderInspector(); }; host.appendChild(b); });
}
async function addPhotos(files){
  const list = [...files].filter(f => /^image\//.test(f.type)).slice(0, 12 - IMAGES.size);
  if (!list.length){ $("photoNote").textContent = "That file isn't an image. Try a JPG, PNG, WebP or GIF."; $("photoNote").className = "note warn"; return; }
  const ids = [];
  for (const f of list){ try { ids.push(await addImageFile(f)); } catch { $("photoNote").textContent = `Couldn't open ${f.name}. Try a different image.`; $("photoNote").className = "note warn"; } }
  if (!ids.length) return;
  renderThumbs();
  $("xDither").value = "diffuse";
  const all = [...IMAGES.keys()];
  const hasPhotoLayer = spec.layers.some(l => l.kind === "image" || l.kind === "slides");
  if (!hasPhotoLayer){
    const keep = spec.layers.filter(l => l.role || l.kind === "text" || l.kind === "particles" || l.kind === "fx");
    const base = all.length > 1 ? { kind: "slides", srcs: all, trans: "fade" } : { kind: "image", src: all[0], frame: "full", motion: "kenburns" };
    setSpec({ title: "Photo loop", layers: [base, ...keep] });
  } else {
    const sl = spec.layers.find(l => l.kind === "slides"), im = spec.layers.find(l => l.kind === "image");
    if (sl) sl.srcs = all; else if (im && all.length > 1){ spec.layers[spec.layers.indexOf(im)] = normLayer({ kind: "slides", srcs: all, trans: "fade", id: im.id }); }
    commit(); renderInspector();
  }
  $("photoNote").className = "note ok";
  $("photoNote").textContent = `${IMAGES.size} photo${IMAGES.size > 1 ? "s" : ""} ready. Pick an effect, or describe the vibe and press Generate. Photos stay on this device${sample && sampleImages ? "; Claude sees up to " + Math.min(3, sampleImages.maxCount || 1) + " of them to design the takes" : ""}.`;
}

/* ===================== Claude + generation ===================== */
let sample = null, sampleImages = null, downloads = null, genCtl = null, refCtl = null;
function setBadge(){ const useC = sample && $("director").value === "claude"; $("engineBadge").innerHTML = useC ? "Director: <b>Claude</b>" : "Director: <b>built-in</b>"; $("director").disabled = !sample; if (!sample) $("director").value = "local"; }
function status(msg, kind){ const el = $("status"); el.textContent = msg; el.className = "note" + (kind ? " " + kind : ""); }
async function photoBlobs(k){
  const out = [];
  for (const [, rec] of [...IMAGES].slice(0, k)){
    const sc = Math.min(1, 1024 / Math.max(rec.w, rec.h)), c = document.createElement("canvas"); c.width = Math.round(rec.w * sc); c.height = Math.round(rec.h * sc);
    c.getContext("2d").drawImage(rec.el, 0, 0, c.width, c.height);
    const b = await new Promise(r => c.toBlob(r, "image/jpeg", .85)); if (b) out.push(b);
  }
  return out;
}
function setGenBusy(b){ $("goBtn").disabled = b; $("surpriseBtn").disabled = b; $("stopBtn").hidden = !b; }
async function generate(fresh){
  const prompt = $("prompt").value.trim();
  if (!prompt && !IMAGES.size){ status("Describe your GIF or add a photo first. Example: a gold star spinning on a navy background.", "warn"); $("prompt").focus(); return; }
  const c = cfg(), caps = captionLayers($("capTop").value.trim(), $("capBot").value.trim(), $("capStyle").value, $("capMotion").value);
  const finish = (vs, labels, how) => {
    vs = vs.map(v => normSpec(withCaptions(v, caps)));
    setVariants(vs, labels, 0); setSpec(clone(vs[0])); addTake(prompt || "Photo loop", vs[0]);
    status(`${vs.length} takes ready, ${how}. Click a take to switch, then refine it in Edit.`, "ok");
  };
  const local = note => { const seed = (Date.now() & 0xfffff) + 1, base = localDirect(prompt, seed); finish(remixSet(base, seed), ["Faithful", "Bolder", "Minimal", "Twist"], note || "built instantly from your prompt's keywords"); };
  if (!sample || $("director").value !== "claude"){ local(); return; }
  setGenBusy(true); genCtl = new AbortController(); status("Claude is reading your brief…");
  try {
    let imgs = null;
    if (sampleImages && IMAGES.size) imgs = await photoBlobs(Math.min(3, sampleImages.maxCount || 1));
    const opts = { signal: genCtl.signal, onText: ({ text }) => { const k = (text.match(/"title"/g) || []).length; status(`Claude is designing take ${clamp(k, 1, 4)} of 4…`); } };
    if (fresh) opts.cache = false;
    if (imgs && imgs.length) opts.images = imgs;
    const out = await sample.json(directorPrompt(prompt, c, imgs ? imgs.length : 0), opts);
    let vs = (Array.isArray(out?.variants) ? out.variants : Array.isArray(out) ? out : [out]).map(normSpec).filter(v => v.layers.length > 1).slice(0, 4);
    if (!vs.length) throw { code: "invalid_json" };
    const labels = ["Faithful", "Bolder", "Minimal", "Twist"].slice(0, vs.length);
    let k = 1; while (vs.length < 4){ vs.push(remix(vs[0], ["bold", "minimal", "twist"][k - 1], Date.now() + k)); labels.push(["Bolder", "Minimal", "Twist"][k - 1]); k++; }
    finish(vs, labels, "directed by Claude");
  } catch (e){
    const code = e && e.code;
    if (code === "cancelled"){ status("Stopped. Your current scene is unchanged."); }
    else if (["not_granted", "sampling_disabled", "not_declared", "capability_disabled", "capability_removed"].includes(code)){ sample = null; setBadge(); local("with the built-in director, because Claude isn't available in this view"); }
    else if (code === "images_unavailable"){ sampleImages = null; local("with the built-in director; this view can't send photos to Claude, so try again to direct without them"); }
    else if (code === "image_rejected") local("with the built-in director, because Claude couldn't read that photo");
    else if (code === "rate_limited") local("with the built-in director, because Claude is busy right now");
    else if (code === "session_expired") local("with the built-in director; sign in to Claude again to use it");
    else local("with the built-in director, because Claude's answer couldn't be used");
  } finally { setGenBusy(false); genCtl = null; }
}
async function refine(){
  const instr = $("refineIn").value.trim(), note = $("refineNote");
  if (!instr){ note.textContent = "Write what to change first, for example: slower, add gold sparkles."; note.className = "note warn"; return; }
  const c = cfg();
  const applyLocal = prefix => { const r = localRefine(spec, instr); if (!r.note){ note.className = "note warn"; note.textContent = (prefix || "") + "The built-in editor understands: slower, faster, bigger, smaller, more, fewer, glow, add sparkles/hearts/stars/snow/confetti/bubbles/rain, a quoted new text, a color word, or a style name."; return; } setSpec(r.spec, { keepSel: true }); note.className = "note ok"; note.textContent = (prefix || "") + r.note; };
  if (!sample || $("director").value !== "claude"){ applyLocal(); return; }
  $("refineBtn").disabled = true; $("refineStop").hidden = false; refCtl = new AbortController(); note.className = "note"; note.textContent = "Claude is editing the scene…";
  try {
    const out = await sample.json(refinePrompt(instr, c, spec), { signal: refCtl.signal, cache: false });
    const ns = normSpec(out && out.layers ? out : out && out.scene ? out.scene : out && Array.isArray(out.variants) ? out.variants[0] : out);
    if (ns.layers.length < 1) throw { code: "invalid_json" };
    setSpec(ns, { keepSel: true }); note.className = "note ok"; note.textContent = "Done. Undo brings back the previous version.";
  } catch (e){
    if (e && e.code === "cancelled"){ note.className = "note"; note.textContent = "Stopped. Nothing changed."; }
    else applyLocal("Claude couldn't make that edit here, so the built-in editor tried. ");
  } finally { $("refineBtn").disabled = false; $("refineStop").hidden = true; refCtl = null; }
}
const QUICK = ["Slower", "Faster", "Bigger", "Add sparkles", "More glow", "Add confetti", "Make it minimal"];

/* ===================== Export ===================== */
let fmt = "gif", exporting = false, exportCancel = false, lastOut = null;
const VIDEO_TYPES = [["mp4", "video/mp4;codecs=avc1.42E01E", "MP4 (H.264)"], ["mp4", "video/mp4", "MP4"], ["webm", "video/webm;codecs=vp9", "WebM (VP9)"], ["webm", "video/webm;codecs=vp8", "WebM (VP8)"], ["webm", "video/webm", "WebM"]];
let VIDEO_SUPPORT = [];
function detectVideo(){
  VIDEO_SUPPORT = [];
  if (typeof MediaRecorder === "undefined" || !HTMLCanvasElement.prototype.captureStream) return;
  const seen = {};
  for (const v of VIDEO_TYPES){ if (seen[v[0]]) continue; try { if (MediaRecorder.isTypeSupported(v[1])){ seen[v[0]] = 1; VIDEO_SUPPORT.push(v); } } catch {} }
  const s = $("vFormat"); s.textContent = "";
  VIDEO_SUPPORT.forEach(v => { const o = document.createElement("option"); o.value = v[0]; o.textContent = v[2]; s.appendChild(o); });
}
const slug = () => (spec.title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "loop").slice(0, 40);
function setFmt(f){
  fmt = f;
  $("fmtSeg").querySelectorAll("button").forEach(b => b.setAttribute("aria-checked", String(b.dataset.fmt === f)));
  document.querySelectorAll("#pane-export [data-for]").forEach(el => { el.hidden = !el.dataset.for.split(" ").includes(f); });
  $("matteRow").hidden = !(f === "gif" && $("xTransparent").checked);
  $("renderBtn").textContent = { gif: "Render GIF", video: "Record video", sprite: "Render sprite sheet", frames: "Render PNG frames", still: "Render still PNG" }[f];
  updateFmtNote();
}
function updateFmtNote(){
  const c = cfg(), n = Math.max(2, Math.round(c.fps * c.dur)), t = $("xTransparent").checked, el = $("fmtNote"); let msg = "";
  if (fmt === "gif"){ const frames = $("xBoomerang").checked ? n * 2 - 2 : n; msg = `${c.W}×${c.H}, ${frames} frames.` + (t ? " Transparent GIFs store full frames, so frame diffing and motion blur are off." : "") + (c.W * c.H > 400000 ? " Large GIFs take longer to encode." : ""); }
  else if (fmt === "video") msg = VIDEO_SUPPORT.length ? `Records in real time at ${c.W}×${c.H}, ${c.fps} fps. Keep this tab visible while it records.` : "This browser can't record video from a canvas. Try GIF or PNG frames instead.";
  else if (fmt === "sprite") msg = `${n} frames in one PNG grid, for game engines and CSS steps() animation.`;
  else if (fmt === "frames") msg = `${n} numbered PNG files in a .zip, ready for After Effects, Premiere or ffmpeg.`;
  else msg = "The frame showing in the preview, as a PNG.";
  el.textContent = msg; $("renderBtn").disabled = fmt === "video" && !VIDEO_SUPPORT.length;
}
function prog(p, msg){ $("meter").style.width = (clamp(p, 0, 1) * 100).toFixed(1) + "%"; if (msg) $("exportNote").textContent = msg; }
const kb = n => n > 1048576 ? (n / 1048576).toFixed(2) + " MB" : Math.max(1, Math.round(n / 1024)) + " KB";
function showResult(blob, name, kind, statsHtml){
  lastOut = { blob, name };
  const pv = $("rprev"); pv.textContent = "";
  const url = URL.createObjectURL(blob);
  if (kind === "video"){ const v = document.createElement("video"); v.src = url; v.muted = true; v.loop = true; v.autoplay = true; v.playsInline = true; v.controls = true; pv.appendChild(v); }
  else if (kind === "image"){ const im = document.createElement("img"); im.src = url; im.alt = "Rendered " + name; pv.appendChild(im); }
  else { const p = document.createElement("p"); p.className = "note"; p.style.padding = "12px"; p.textContent = "ZIP archive"; pv.appendChild(p); }
  $("rstats").innerHTML = statsHtml; $("result").hidden = false;
}
async function doExport(){
  if (exporting) return; exporting = true; exportCancel = false;
  $("renderBtn").disabled = true; $("cancelBtn").hidden = false; $("result").hidden = true; $("exportNote").className = "note"; prog(0, "Starting…");
  const c = cfg(), t0 = performance.now(), o = { sp: normSpec(clone(spec)), W: c.W, H: c.H, fps: c.fps, n: Math.max(2, Math.round(c.fps * c.dur)), transparent: $("xTransparent").checked };
  const cancelled = () => exportCancel;
  try {
    if (fmt === "gif"){
      Object.assign(o, { colors: +$("xColors").value, dither: $("xDither").value, optimize: $("xOptimize").checked, boomerang: $("xBoomerang").checked, blur: $("xBlur").checked, once: $("xRepeat").value === "once", matte: $("xMatte").value });
      const cap = +$("xCap").value * 1048576; let res = await encodeGif(o, prog, cancelled); const notes = [];
      for (let a = 0; cap && res.bytes.length > cap && a < 6; a++){
        const ratio = cap / res.bytes.length;
        if (o.colors > 64 && ratio > .55){ o.colors = o.colors > 128 ? 128 : 64; notes.push(o.colors + " colors"); }
        else if (o.W > 160){ const s = clamp(Math.sqrt(ratio) * .93, .5, .92); o.W = even(o.W * s); o.H = even(o.H * s); notes.push(o.W + "×" + o.H); }
        else if (o.fps > 10){ o.fps = o.fps > 15 ? 15 : 10; o.n = Math.max(2, Math.round(o.fps * c.dur)); notes.push(o.fps + " fps"); }
        else break;
        prog(0, `Over ${kb(cap)}, re-encoding smaller (${notes[notes.length - 1]})…`);
        res = await encodeGif(o, prog, cancelled);
      }
      const blob = new Blob([res.bytes], { type: "image/gif" }), name = slug() + ".gif";
      const fit = cap ? (res.bytes.length <= cap ? `<span>Fits under ${kb(cap)}${notes.length ? ": " + [...new Set(notes)].slice(-2).join(", ") : ""}</span>` : `<span>Still over ${kb(cap)} at the smallest settings</span>`) : "";
      showResult(blob, name, "image", `<span><b>${kb(res.bytes.length)}</b> · ${res.frames} frames</span><span>${res.W}×${res.H} · ${res.colors} colors · ${Math.round(1000 / o.fps)} ms/frame</span>${o.optimize && !o.transparent ? `<span>${Math.round(res.changedRatio * 100)}% of pixels stored; the rest reuse the previous frame</span>` : ""}<span>${$("seam").textContent} · ${o.once ? "plays once" : "loops forever"}</span>${fit}<span>Encoded in ${((performance.now() - t0) / 1000).toFixed(1)} s</span>`);
      $("exportNote").className = "note ok"; $("exportNote").textContent = "GIF ready.";
    } else if (fmt === "video"){
      const sel2 = VIDEO_SUPPORT.find(v => v[0] === $("vFormat").value) || VIDEO_SUPPORT[0];
      if (!sel2) throw new Error("This browser can't record video from a canvas.");
      const want = +$("vLength").value, loops = want === 1 ? 1 : Math.max(1, Math.ceil(want / c.dur)), seconds = loops * c.dur;
      const cv = document.createElement("canvas"); cv.width = o.W; cv.height = o.H; const ctx = cv.getContext("2d");
      renderFrame(ctx, o.sp, 0, o.W, o.H);
      const stream = cv.captureStream(o.fps), rec = new MediaRecorder(stream, { mimeType: sel2[1], videoBitsPerSecond: Math.round(clamp(o.W * o.H * o.fps * .6, 2e6, 12e6)) });
      const chunks = []; rec.ondataavailable = e => { if (e.data && e.data.size) chunks.push(e.data); };
      const stopped = new Promise(r => { rec.onstop = r; });
      rec.start(500); const st = performance.now(), total = seconds * 1000; let lf = -1;
      await new Promise(res => { const step = () => { const el = performance.now() - st; if (el >= total || exportCancel){ res(); return; } const fi = Math.floor(el / 1000 * o.fps); if (fi !== lf){ lf = fi; renderFrame(ctx, o.sp, (fi % o.n) / o.n, o.W, o.H); } prog(el / total, `Recording ${(el / 1000).toFixed(1)} of ${seconds.toFixed(1)} s…`); requestAnimationFrame(step); }; requestAnimationFrame(step); });
      rec.stop(); await stopped; stream.getTracks().forEach(tr => tr.stop());
      if (exportCancel) throw { code: "cancelled" };
      const blob = new Blob(chunks, { type: sel2[1].split(";")[0] }), name = slug() + "." + sel2[0];
      showResult(blob, name, "video", `<span><b>${kb(blob.size)}</b> · ${sel2[2]}</span><span>${o.W}×${o.H} · ${o.fps} fps · ${seconds.toFixed(1)} s (${loops} loop${loops > 1 ? "s" : ""})</span>`);
      $("exportNote").className = "note ok"; $("exportNote").textContent = "Video ready.";
    } else if (fmt === "sprite"){
      const n = o.n, cols = Math.ceil(Math.sqrt(n)), rows = Math.ceil(n / cols);
      const sc = Math.min(1, Math.sqrt(16e6 / (n * o.W * o.H)), 8192 / (cols * o.W), 8192 / (rows * o.H)), cw = Math.max(8, Math.floor(o.W * sc)), ch = Math.max(8, Math.floor(o.H * sc));
      const sheet = document.createElement("canvas"); sheet.width = cols * cw; sheet.height = rows * ch; const sctx = sheet.getContext("2d");
      const cv = document.createElement("canvas"); cv.width = cw; cv.height = ch; const ctx = cv.getContext("2d");
      for (let i = 0; i < n; i++){ if (exportCancel) throw { code: "cancelled" }; renderFrame(ctx, o.sp, i / n, cw, ch, { transparent: o.transparent }); sctx.drawImage(cv, (i % cols) * cw, Math.floor(i / cols) * ch); prog((i + 1) / n, `Drawing frame ${i + 1} of ${n}…`); if (i % 6 === 5) await sleep0(); }
      const blob = await new Promise(r => sheet.toBlob(r, "image/png")), name = `${slug()}-sprite-${cols}x${rows}-${cw}x${ch}.png`;
      showResult(blob, name, "image", `<span><b>${kb(blob.size)}</b> · ${n} frames</span><span>${cols}×${rows} grid of ${cw}×${ch} cells</span><span>${o.fps} fps → ${Math.round(1000 / o.fps)} ms per cell</span>`);
      $("exportNote").className = "note ok"; $("exportNote").textContent = "Sprite sheet ready.";
    } else if (fmt === "frames"){
      const files = [], cv = document.createElement("canvas"); cv.width = o.W; cv.height = o.H; const ctx = cv.getContext("2d");
      for (let i = 0; i < o.n; i++){ if (exportCancel) throw { code: "cancelled" }; renderFrame(ctx, o.sp, i / o.n, o.W, o.H, { transparent: o.transparent }); const b = await new Promise(r => cv.toBlob(r, "image/png")); files.push({ name: `${slug()}_${String(i + 1).padStart(4, "0")}.png`, data: new Uint8Array(await b.arrayBuffer()) }); prog((i + 1) / o.n, `Saving frame ${i + 1} of ${o.n}…`); }
      const blob = zipStore(files), name = slug() + "-frames.zip";
      showResult(blob, name, "zip", `<span><b>${kb(blob.size)}</b> · ${o.n} PNG files</span><span>${o.W}×${o.H} · ${o.fps} fps${o.transparent ? " · transparent" : ""}</span>`);
      $("exportNote").className = "note ok"; $("exportNote").textContent = "Frames ready.";
    } else {
      const cv = document.createElement("canvas"); cv.width = o.W; cv.height = o.H; const n = o.n, t = Math.floor(curT() * n) / n;
      renderFrame(cv.getContext("2d"), o.sp, t, o.W, o.H, { transparent: o.transparent });
      const blob = await new Promise(r => cv.toBlob(r, "image/png")), name = `${slug()}-frame-${Math.round(t * n) + 1}.png`;
      showResult(blob, name, "image", `<span><b>${kb(blob.size)}</b></span><span>${o.W}×${o.H} · frame ${Math.round(t * n) + 1} of ${n}</span>`);
      $("exportNote").className = "note ok"; $("exportNote").textContent = "Still ready.";
    }
    prog(1);
  } catch (e){
    if (e && e.code === "cancelled"){ $("exportNote").className = "note"; $("exportNote").textContent = "Cancelled."; prog(0); }
    else { console.error(e); $("exportNote").className = "note warn"; $("exportNote").textContent = "Export failed" + (e && e.message ? ": " + e.message : "") + ". Try a smaller size or a shorter loop."; }
  } finally { exporting = false; $("renderBtn").disabled = false; $("cancelBtn").hidden = true; updateFmtNote(); }
}
async function saveOut(blob, name, noteEl){
  noteEl = noteEl || $("exportNote");
  if (!downloads){ noteEl.className = "note"; noteEl.textContent = /\.(gif|png)$/.test(name) ? "Saving isn't available in this view. Right-click or long-press the preview and choose Save image." : "Saving files isn't available in this view."; return; }
  try { await downloads.save({ filename: name, data: blob }); noteEl.className = "note ok"; noteEl.textContent = "Saved " + name + "."; }
  catch (e){ const c2 = e && e.code; noteEl.className = "note" + (c2 === "declined" ? "" : " warn");
    noteEl.textContent = c2 === "declined" ? "Save cancelled." : c2 === "rate_limited" ? "A save prompt is already open. Finish that one first." : c2 === "extension_not_enabled" ? "This file type can't be saved in this view." : c2 === "too_large" ? "That file is too large to save here. Try a smaller size." : "Saving isn't available in this view."; }
}
