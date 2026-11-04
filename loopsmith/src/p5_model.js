
/* ===================== Scene model ===================== */
const SHAPE_MOTIONS = ["bounce", "spin", "pulse", "float", "orbit", "swing", "heartbeat", "jelly", "flip", "shake", "wiggle", "pop", "slide", "drop", "none"];
const TEXT_MOTIONS = ["wave", "pop", "glitch", "typewriter", "pulse", "rainbow", "bounce", "shake", "slide", "zoom", "flicker", "float", "swing", "heartbeat", "jelly", "none"];
const IMG_MOTIONS = ["kenburns", "zoom", "pan", "float", "shake", "pulse", "wobble", "glitch", "swing", "spin", "none"];
const D = {
  x: { t: "range", label: "Horizontal", min: -.2, max: 1.2, step: .01, d: .5 },
  y: { t: "range", label: "Vertical", min: -.2, max: 1.2, step: .01, d: .5 },
  amount: { t: "range", label: "Strength", min: 0, max: 1, step: .05, d: .6 },
  cycles: { t: "int", label: "Speed", min: 1, max: 6, step: 1, d: 1, fmt: v => v + "× per loop" },
  phase: { t: "range", label: "Delay", min: 0, max: 1, step: .05, d: 0 },
  glow: { t: "range", label: "Glow", min: 0, max: 2, step: .05, d: 0 },
  opacity: { t: "range", label: "Opacity", min: 0, max: 1, step: .05, d: 1 },
  seed: { t: "seed", label: "Randomness" }
};
const KINDS = {
  background: { label: "Background", props: { style: { t: "select", label: "Fill", opts: ["linear", "radial", "conic", "solid"], d: "linear" }, colors: { t: "colors", label: "Colors", d: ["#151a33", "#3b1f5c"], max: 4 }, angle: { t: "range", label: "Angle", min: 0, max: 360, step: 1, d: 90, fmt: v => Math.round(v) + "°" }, spin: { t: "check", label: "Animate the gradient", d: false }, cycles: D.cycles, opacity: D.opacity } },
  pattern: { label: "Pattern", props: { style: { t: "select", label: "Pattern", opts: ["dots", "checker", "stripes", "grid", "floor"], d: "dots" }, colors: { t: "colors", label: "Color", d: ["rgba(255,255,255,0.12)"], max: 1 }, size: { t: "range", label: "Cell size", min: .03, max: .4, step: .01, d: .1 }, y: { ...D.y, label: "Horizon (floor)", d: .62 }, cycles: D.cycles, opacity: D.opacity } },
  shape: { label: "Shape", props: { shape: { t: "select", label: "Shape", opts: SH_OPTS, d: "circle" }, glyph: { t: "text", label: "Emoji (replaces shape)", d: "", max: 8 }, color: { t: "color", label: "Color", d: "#ffd23f" }, outline: { t: "check", label: "Outline only", d: false }, motion: { t: "select", label: "Motion", opts: SHAPE_MOTIONS, d: "pulse" }, amount: D.amount, cycles: D.cycles, phase: D.phase, size: { t: "range", label: "Size", min: .02, max: 1.2, step: .01, d: .3 }, x: D.x, y: D.y, glow: D.glow, opacity: D.opacity } },
  text: { label: "Text", props: { text: { t: "text", label: "Text", d: "Your text", max: 80, area: true }, font: { t: "select", label: "Font", opts: Object.keys(FONTS), d: "display" }, upper: { t: "check", label: "All caps", d: false }, color: { t: "color", label: "Color", d: "#ffffff" }, stroke: { t: "colorOpt", label: "Outline", on: "#000000" }, shadow: { t: "colorOpt", label: "Shadow", on: "rgba(0,0,0,0.4)" }, box: { t: "colorOpt", label: "Box behind", on: "rgba(0,0,0,0.6)" }, motion: { t: "select", label: "Motion", opts: TEXT_MOTIONS, d: "wave" }, amount: D.amount, cycles: D.cycles, phase: D.phase, size: { t: "range", label: "Size", min: .03, max: .4, step: .005, d: .14 }, x: D.x, y: D.y, glow: D.glow, opacity: D.opacity } },
  particles: { label: "Particles", props: { shape: { t: "select", label: "Particle", opts: PT_OPTS, d: "dot" }, glyph: { t: "text", label: "Emoji (replaces particle)", d: "", max: 8 }, colors: { t: "colors", label: "Colors", d: ["#ffffff"], max: 6 }, motion: { t: "select", label: "Motion", opts: ["rise", "fall", "drift", "burst", "swirl", "twinkle", "fountain"], d: "rise" }, count: { t: "int", label: "Count", min: 1, max: 220, step: 1, d: 40 }, size: { t: "range", label: "Size", min: .005, max: .25, step: .005, d: .04 }, cycles: D.cycles, x: { ...D.x, label: "Origin X" }, y: { ...D.y, label: "Origin Y" }, glow: D.glow, opacity: D.opacity, seed: D.seed } },
  waves: { label: "Waves", props: { colors: { t: "colors", label: "Colors (back to front)", d: ["#3a86ff", "#2559c9", "#143a8a"], max: 5 }, y: { ...D.y, label: "Water line", d: .6 }, amount: D.amount, cycles: D.cycles, opacity: D.opacity } },
  rings: { label: "Ripples", props: { colors: { t: "colors", label: "Colors", d: ["#ffffff"], max: 4 }, count: { t: "int", label: "Rings", min: 1, max: 20, step: 1, d: 5 }, size: { t: "range", label: "Reach", min: .05, max: 1.5, step: .01, d: .6 }, x: D.x, y: D.y, cycles: D.cycles, glow: D.glow, opacity: D.opacity } },
  rays: { label: "Sunburst", props: { colors: { t: "colors", label: "Colors", d: ["#ffcf3f", "#ffb000"], max: 4 }, count: { t: "int", label: "Rays", min: 3, max: 40, step: 1, d: 12 }, x: D.x, y: D.y, cycles: D.cycles, reverse: { t: "check", label: "Turn the other way", d: false }, opacity: D.opacity } },
  orbit: { label: "Spinner", props: { colors: { t: "colors", label: "Colors", d: ["#ffffff"], max: 4 }, count: { t: "int", label: "Dots", min: 2, max: 24, step: 1, d: 10 }, size: { t: "range", label: "Size", min: .05, max: 1, step: .01, d: .4 }, x: D.x, y: D.y, cycles: D.cycles, glow: D.glow, opacity: D.opacity } },
  blob: { label: "Liquid blob", props: { colors: { t: "colors", label: "Colors", d: ["#ff5f9e", "#7b5cff"], max: 3 }, size: { t: "range", label: "Size", min: .05, max: 1.2, step: .01, d: .5 }, x: D.x, y: D.y, amount: D.amount, cycles: D.cycles, glow: D.glow, opacity: D.opacity, seed: D.seed } },
  bars: { label: "Equalizer", props: { colors: { t: "colors", label: "Colors", d: ["#5ef2c2", "#3a86ff"], max: 4 }, count: { t: "int", label: "Bars", min: 2, max: 48, step: 1, d: 14 }, size: { t: "range", label: "Width", min: .1, max: 1, step: .01, d: .7 }, x: D.x, y: { ...D.y, label: "Baseline", d: .8 }, amount: D.amount, cycles: D.cycles, opacity: D.opacity, seed: D.seed } },
  image: { label: "Photo", props: { src: { t: "image", label: "Photo", d: "" }, frame: { t: "select", label: "Layout", opts: ["full", "framed"], d: "full" }, motion: { t: "select", label: "Effect", opts: IMG_MOTIONS, d: "kenburns" }, amount: D.amount, cycles: D.cycles, fit: { t: "select", label: "Fit", opts: ["cover", "contain"], d: "cover" }, mask: { t: "select", label: "Frame shape", opts: ["none", "rounded", "circle"], d: "rounded" }, border: { t: "colorOpt", label: "Border", on: "#ffffff" }, size: { t: "range", label: "Size (framed)", min: .1, max: 1.2, step: .01, d: .7 }, x: D.x, y: D.y, opacity: D.opacity } },
  slides: { label: "Slideshow", props: { srcs: { t: "images", label: "Photos", d: [] }, trans: { t: "select", label: "Transition", opts: ["fade", "slide", "zoom", "wipe", "cut"], d: "fade" }, kenburns: { t: "check", label: "Slow zoom on each photo", d: true }, fit: { t: "select", label: "Fit", opts: ["cover", "contain"], d: "cover" }, amount: { ...D.amount, label: "Transition length", d: .5 }, opacity: D.opacity } },
  fx: { label: "Finish", props: { style: { t: "select", label: "Effect", opts: ["vignette", "scanlines", "lightleak"], d: "vignette" }, amount: { ...D.amount, d: .6 }, cycles: D.cycles, opacity: D.opacity } }
};
const PRETTY = { kenburns: "Ken Burns", lightleak: "Light leak", typewriter: "Typewriter", heartbeat: "Heartbeat", radial: "Radial", conic: "Conic", full: "Full frame", framed: "Framed card", none: "None", fountain: "Fountain", zoom: "Zoom", pop: "Pop", display: "Grotesk", bold: "Block", impact: "Meme (Anton)", script: "Script", round: "Rounded", serif: "Serif", pixel: "Pixel", mono: "Mono", floor: "Retro floor" };
const pretty = v => PRETTY[v] || (String(v).charAt(0).toUpperCase() + String(v).slice(1));
const KIND_ALIAS = { caption: "text", title: "text", emoji: "shape", sticker: "shape", photo: "image", slideshow: "slides", gradient: "background", spinner: "orbit", loader: "orbit", equalizer: "bars", ripples: "rings", sunburst: "rays", effect: "fx", overlay: "fx" };

function coerce(def, v){
  switch (def.t){
    case "range": return num(v, def.d, def.min, def.max);
    case "int": return Math.round(num(v, def.d, def.min, def.max));
    case "color": return col(v, def.d);
    case "colorOpt": return (v == null || v === "" || v === false) ? null : v === true ? def.on : col(v, null);
    case "colors": return cols(v, def.d, def.max || 6);
    case "select": return def.opts.includes(v) ? v : def.d;
    case "text": return v == null ? def.d : String(v).slice(0, def.max || 80);
    case "check": return v == null ? def.d : !!v;
    case "image": return typeof v === "string" ? v : def.d;
    case "images": return Array.isArray(v) ? v.filter(s => typeof s === "string").slice(0, 12) : def.d.slice();
    case "seed": return Number.isFinite(+v) && v !== null && v !== "" ? Math.floor(clamp(+v, 0, 1e9)) : Math.floor(Math.random() * 1e9);
  }
  return v;
}
function normLayer(L){
  if (!L || typeof L !== "object") return null;
  const kind = KINDS[L.kind] ? L.kind : KIND_ALIAS[L.kind];
  if (!kind) return null;
  const src = { ...L };
  if ((kind === "shape" || kind === "particles") && typeof src.shape === "string" && !(kind === "shape" ? SH_OPTS : PT_OPTS).includes(src.shape)){
    if (!src.glyph && src.shape.trim() && [...src.shape.trim()].length <= 4) src.glyph = src.shape.trim();
    src.shape = undefined;
  }
  if (kind === "shape" && L.kind === "emoji" && typeof L.emoji === "string") src.glyph = L.emoji;
  if (kind === "particles" && src.colors == null && src.color) src.colors = [src.color];
  if (kind === "text" && src.uppercase != null && src.upper == null) src.upper = src.uppercase;
  if (kind === "image" && src.motion === "ken burns") src.motion = "kenburns";
  const o = { kind, id: typeof L.id === "string" && L.id ? L.id.slice(0, 24) : nid(), hidden: !!L.hidden };
  if (typeof L.role === "string") o.role = L.role.slice(0, 20);
  for (const [k, def] of Object.entries(KINDS[kind].props)) o[k] = coerce(def, src[k]);
  if (o.glyph != null) o.glyph = String(o.glyph).trim();
  return o;
}
function normSpec(s){
  s = s && typeof s === "object" ? s : {};
  const seen = new Set();
  const layers = (Array.isArray(s.layers) ? s.layers : []).slice(0, 18).map(normLayer).filter(Boolean)
    .map(l => { if (seen.has(l.id)) l.id = nid(); seen.add(l.id); return l; });
  if (!layers.some(l => l.kind === "background" || l.kind === "slides" || (l.kind === "image" && l.frame === "full")))
    layers.unshift(normLayer({ kind: "background", colors: ["#151a33", "#3b1f5c"] }));
  return { title: String(s.title || "Untitled loop").slice(0, 48), layers };
}
function summary(L){
  switch (L.kind){
    case "text": return "“" + L.text.replace(/\n/g, " ").slice(0, 22) + "” · " + L.motion;
    case "shape": return (L.glyph || L.shape) + " · " + L.motion;
    case "particles": return L.count + " " + (L.glyph || L.shape) + " · " + L.motion;
    case "image": return (IMAGES.get(L.src)?.name || "no photo") + " · " + pretty(L.motion);
    case "slides": return L.srcs.length + " photos · " + L.trans;
    case "background": case "pattern": case "fx": return pretty(L.style);
    default: return (L.colors || []).length + " colors";
  }
}

/* ===================== Styles ===================== */
const STYLES = {
  neon:      { label: "Neon", bg: ["#07021a", "#1a0640"], pal: ["#ff2fd0", "#2ff5ff", "#b6ff3b", "#ffffff"], font: "display", glow: 1.1, cue: "glowing neon tubes on near-black, saturated magenta, cyan and lime, heavy glow" },
  pastel:    { label: "Pastel", bg: ["#ffd6e8", "#cfe8ff"], pal: ["#ff8fc4", "#7cc6ff", "#9fe8b8", "#fff0a0", "#ffffff"], font: "round", glow: 0, cue: "soft pastel, rounded friendly shapes, airy light background, gentle motion" },
  retro:     { label: "8-bit", bg: ["#1d2b53", "#1d2b53"], pal: ["#ff004d", "#ffa300", "#ffec27", "#00e436", "#29adff", "#fff1e8"], font: "pixel", glow: 0, fx: "scanlines", pattern: { style: "grid", colors: ["rgba(255,255,255,0.06)"], size: .08 }, cue: "retro 8-bit arcade, chunky pixel type, PICO-8 style palette, hard edges, no glow" },
  vapor:     { label: "Vaporwave", bg: ["#2d0b5a", "#ff6ec7"], pal: ["#ff71ce", "#01cdfe", "#05ffa1", "#b967ff", "#fffb96"], font: "serif", glow: .6, fx: "scanlines", pattern: { style: "floor", colors: ["#ff71ce"], y: .64 }, cue: "80s and 90s vaporwave, pink-to-purple sunset, perspective grid floor, sun, chrome italic type" },
  minimal:   { label: "Minimal", bg: ["#f4f4f0", "#f4f4f0"], pal: ["#111111", "#e63946", "#8d99ae"], font: "display", glow: 0, cue: "minimalist, off-white background, one accent color, few elements, generous negative space, precise motion" },
  comic:     { label: "Comic pop", bg: ["#ffd60a", "#ff9f1c"], pal: ["#e63946", "#1d3557", "#ffffff", "#111111"], font: "bold", glow: 0, stroke: "#111111", pattern: { style: "dots", colors: ["rgba(0,0,0,0.12)"], size: .06 }, cue: "pop-art comic book, halftone dots, bold black outlines, starbursts, punchy primaries" },
  cinematic: { label: "Cinematic", bg: ["#0b0f19", "#1c2541"], pal: ["#f2c14e", "#f78154", "#e0e1dd", "#4d9de0"], font: "serif", glow: .5, fx: "vignette", cue: "cinematic film look, moody teal and orange, vignette, slow elegant motion, serif titles" },
  kawaii:    { label: "Kawaii", bg: ["#ffe5f1", "#e0f4ff"], pal: ["#ff6fae", "#ffb3d9", "#8fd3ff", "#fff4a3", "#ffffff"], font: "round", glow: .2, cue: "cute kawaii, hearts and sparkles, bouncy jelly motion, candy colors, rounded type" },
  ink:       { label: "Ink", bg: ["#0e0e0e", "#1d1d1d"], pal: ["#f5f5f5", "#bdbdbd", "#777777"], font: "impact", glow: 0, cue: "stark black and white, high-contrast monochrome, graphic" },
  golden:    { label: "Golden hour", bg: ["#2b1055", "#d53369", "#ffb347"], pal: ["#ffcf5c", "#ff7e5f", "#feb47b", "#ffffff"], font: "script", glow: .8, fx: "lightleak", cue: "warm golden-hour sunset gradient, glowing sun, soft light leaks, dreamy" },
  holo:      { label: "Holographic", bg: ["#a1c4fd", "#c2e9fb", "#fbc2eb"], pal: ["#ffffff", "#e0c3fc", "#8ec5fc", "#f9f586"], font: "display", glow: .7, cue: "iridescent holographic chrome, pearly gradients, shimmering sparkles" },
  anime:     { label: "Anime", bg: ["#89c2ff", "#ffe0f0"], pal: ["#ff5fa2", "#ffffff", "#ffd166", "#3a86ff"], font: "bold", glow: .4, cue: "anime opening energy, speed rays, sparkles, sakura petals, dramatic zooms" }
};
function colorSlots(L){ // [{get,set}] for recolorable fields
  const out = [];
  if (L.color) out.push({ get: () => L.color, set: v => L.color = v });
  if (Array.isArray(L.colors)) L.colors.forEach((_, i) => out.push({ get: () => L.colors[i], set: v => L.colors[i] = v }));
  return out;
}
function restyle(sp, key){
  const st = STYLES[key]; if (!st) return sp;
  const s = clone(sp), bgDark = lum(parseColor(st.bg[0])) < .5;
  const palSorted = st.pal.slice().sort((a, b) => lum(parseColor(a)) - lum(parseColor(b)));
  const slots = [];
  s.layers.forEach(L => {
    if (L.role) return;
    if (L.kind === "background"){ L.colors = st.bg.slice(0, Math.max(2, st.bg.length)); if (st.bg[0] === st.bg[1]) L.style = "solid"; return; }
    if (L.kind === "image" || L.kind === "slides" || L.kind === "fx") return;
    if (L.kind === "text"){ L.font = st.font; L.color = bgDark ? palSorted[palSorted.length - 1] : palSorted[0]; if (st.stroke !== undefined) L.stroke = st.stroke; L.glow = st.glow > .5 ? st.glow * .6 : 0; return; }
    if (L.kind === "pattern"){ L.colors = [withAlpha(bgDark ? "#ffffff" : "#000000", (parseColor(L.colors[0]) || [0, 0, 0, .12])[3])]; return; }
    colorSlots(L).forEach(sl => slots.push(sl));
    if (L.glow > 0 || st.glow > .9) L.glow = st.glow;
  });
  const uniq = [...new Set(slots.map(sl => sl.get()))].sort((a, b) => lum(parseColor(a) || [0, 0, 0]) - lum(parseColor(b) || [0, 0, 0]));
  const map = new Map(uniq.map((c, i) => [c, palSorted[Math.min(palSorted.length - 1, Math.floor(i * palSorted.length / Math.max(1, uniq.length)))]]));
  slots.forEach(sl => { const old = parseColor(sl.get()) || [0, 0, 0, 1], nw = parseColor(map.get(sl.get())) || old; sl.set(toCss([nw[0], nw[1], nw[2], old[3]])); });
  s.layers = s.layers.filter(L => L.kind !== "fx" || L.role);
  if (st.pattern && !s.layers.some(L => L.kind === "pattern")){
    const bi = s.layers.findIndex(L => L.kind === "background");
    s.layers.splice(bi + 1, 0, normLayer({ kind: "pattern", ...st.pattern }));
  }
  if (st.fx){ const ci = s.layers.findIndex(L => L.kind === "text"); const fx = normLayer({ kind: "fx", style: st.fx, amount: .6 }); if (ci < 0) s.layers.push(fx); else s.layers.splice(ci, 0, fx); }
  return normSpec(s);
}

/* ===================== Captions ===================== */
const CAP_STYLES = {
  meme:     { font: "impact", color: "#ffffff", stroke: "#000000", shadow: null, box: null, upper: true, glow: 0 },
  subtitle: { font: "display", color: "#ffffff", stroke: null, shadow: null, box: "rgba(0,0,0,0.62)", upper: false, glow: 0 },
  neon:     { font: "script", color: "#fff0fb", stroke: null, shadow: null, box: null, upper: false, glow: 1.1 },
  bubble:   { font: "round", color: "#1b1b1f", stroke: null, shadow: null, box: "#ffffff", upper: false, glow: 0 },
  pixel:    { font: "pixel", color: "#ffffff", stroke: "#000000", shadow: null, box: null, upper: true, glow: 0 }
};
function captionLayers(top, bot, style, motion){
  const st = CAP_STYLES[style] || CAP_STYLES.meme, out = [];
  if (top) out.push(normLayer({ kind: "text", role: "cap-top", text: top, ...st, motion, size: .1, y: .13, amount: .5 }));
  if (bot) out.push(normLayer({ kind: "text", role: "cap-bot", text: bot, ...st, motion, size: .1, y: .87, amount: .5, phase: motion === "none" ? 0 : .15 }));
  return out;
}
function withCaptions(sp, caps){
  const s = { ...sp, layers: sp.layers.filter(l => !(l.role === "cap-top" || l.role === "cap-bot")) };
  s.layers = s.layers.concat(caps.map(c => ({ ...c, id: nid() })));
  return s;
}

/* ===================== Variations ===================== */
const MOTION_TWIST = { pulse: "jelly", bounce: "pop", float: "swing", spin: "flip", heartbeat: "jelly", wave: "rainbow", pop: "wave", rise: "swirl", fall: "drift", twinkle: "burst", none: "float", kenburns: "zoom", zoom: "wobble", shake: "glitch" };
function remix(sp, mode, seed){
  const r = rng(seed), s = clone(sp);
  s.layers.forEach(l => { l.id = nid(); if ("seed" in l) l.seed = Math.floor(r() * 1e9); });
  const accent = (s.layers.find(l => l.kind === "shape" || l.kind === "particles" || l.kind === "blob") || {}).color
    || ((s.layers.find(l => l.colors && l.kind !== "background") || {}).colors || ["#ffd23f"])[0];
  if (mode === "bold"){
    s.layers.forEach(l => {
      if (l.role) return;
      if ("glow" in l) l.glow = Math.min(2, (l.glow || 0) + .5);
      if (l.kind === "particles") l.count = Math.min(220, Math.round(l.count * 1.7));
      if ("amount" in l && l.kind !== "background") l.amount = Math.min(1, l.amount + .25);
      if (l.kind === "text"){ l.size = Math.min(.4, l.size * 1.15); if (!l.stroke && !l.box) l.shadow = "rgba(0,0,0,0.45)"; }
    });
    const bi = s.layers.findIndex(l => l.kind === "background" || l.kind === "slides" || l.kind === "image");
    if (!s.layers.some(l => l.kind === "rays")) s.layers.splice(bi + 1, 0, { kind: "rays", colors: [withAlpha(accent, .22), "rgba(255,255,255,0)"], count: 14, cycles: 1 });
    s.layers.splice(bi + 2, 0, { kind: "rings", colors: [accent], count: 4, size: .75, glow: .8, cycles: 1, opacity: .7 });
    s.title = s.title + " · bold";
  } else if (mode === "minimal"){
    let kept = 0;
    s.layers = s.layers.filter(l => {
      if (l.role || ["background", "shape", "text", "image", "slides", "orbit", "blob"].includes(l.kind)) return true;
      if (l.kind === "particles" && kept++ === 0){ l.count = Math.max(6, Math.round(l.count * .4)); return true; }
      return false;
    });
    s.layers.forEach(l => {
      if (l.kind === "background"){ l.style = "solid"; l.colors = [l.colors[0]]; }
      if ("glow" in l && !l.role) l.glow = 0;
      if (l.kind === "text" && !l.role){ l.font = l.font === "script" ? "serif" : "display"; if (l.motion === "rainbow" || l.motion === "glitch") l.motion = "wave"; }
      if ("amount" in l && !l.role && l.kind !== "image") l.amount = Math.max(.25, l.amount * .6);
    });
    s.title = s.title + " · minimal";
  } else {
    const deg = 120 + Math.floor(r() * 120);
    s.layers.forEach(l => {
      if (l.role) return;
      if (l.color) l.color = hueShift(l.color, deg);
      if (Array.isArray(l.colors)) l.colors = l.colors.map(c => hueShift(c, deg));
      if (l.motion && MOTION_TWIST[l.motion]) l.motion = MOTION_TWIST[l.motion];
    });
    s.title = s.title + " · twist";
  }
  return normSpec(s);
}
function remixSet(sp, seed){ return [sp, remix(sp, "bold", seed + 1), remix(sp, "minimal", seed + 2), remix(sp, "twist", seed + 3)]; }
