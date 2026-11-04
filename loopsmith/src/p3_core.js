"use strict";
/* ===================== Utilities ===================== */
const TAU = Math.PI * 2;
const $ = id => document.getElementById(id);
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const num = (v, d, a, b) => { v = Number(v); return Number.isFinite(v) ? clamp(v, a, b) : d; };
const wrap01 = v => ((v % 1) + 1) % 1;
const sleep0 = () => new Promise(r => setTimeout(r, 0));
const clone = o => JSON.parse(JSON.stringify(o));
const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const even = v => Math.max(2, Math.round(v / 2) * 2);
let uidSeq = 0;
const nid = () => "L" + (++uidSeq).toString(36) + Math.random().toString(36).slice(2, 6);
function rng(seed){ let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const easeOutBack = k => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(k - 1, 3) + c1 * Math.pow(k - 1, 2); };
const easeOutCubic = k => 1 - Math.pow(1 - k, 3);
const easeInCubic = k => k * k * k;
const easeInOut = k => k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
const lsGet = k => { try { return localStorage.getItem(k); } catch { return null; } };
const lsSet = (k, v) => { try { localStorage.setItem(k, v); } catch {} };

/* ===================== Color ===================== */
const cctx = document.createElement("canvas").getContext("2d");
function parseColor(c){
  if (typeof c !== "string" || !c.trim()) return null;
  cctx.fillStyle = "#010203"; cctx.fillStyle = c.trim();
  const v = cctx.fillStyle;
  if (v === "#010203" && c.trim().toLowerCase() !== "#010203") return null;
  if (v[0] === "#") return [parseInt(v.slice(1, 3), 16), parseInt(v.slice(3, 5), 16), parseInt(v.slice(5, 7), 16), 1];
  const m = v.match(/rgba?\(([^)]+)\)/); if (!m) return null;
  const p = m[1].split(",").map(s => parseFloat(s));
  return [p[0], p[1], p[2], p[3] ?? 1];
}
const hex2 = n => Math.round(clamp(n, 0, 255)).toString(16).padStart(2, "0");
const toHex = p => "#" + hex2(p[0]) + hex2(p[1]) + hex2(p[2]);
const toCss = p => (p[3] ?? 1) >= 1 ? toHex(p) : `rgba(${Math.round(p[0])},${Math.round(p[1])},${Math.round(p[2])},${+(+p[3]).toFixed(3)})`;
const lum = p => (0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2]) / 255;
const withAlpha = (c, a) => { const p = parseColor(c) || [255, 255, 255, 1]; return toCss([p[0], p[1], p[2], a]); };
function col(v, d){ const p = parseColor(typeof v === "string" ? v : null); return p ? toCss(p) : d; }
function cols(v, d, max = 6){ const a = (Array.isArray(v) ? v : v != null ? [v] : []).map(x => col(x, null)).filter(Boolean).slice(0, max); return a.length ? a : d.slice(); }
function rgb2hsl([r, g, b]){ r /= 255; g /= 255; b /= 255; const mx = Math.max(r, g, b), mn = Math.min(r, g, b); let h = 0, s = 0; const l = (mx + mn) / 2;
  if (mx !== mn){ const d = mx - mn; s = l > .5 ? d / (2 - mx - mn) : d / (mx + mn);
    h = mx === r ? (g - b) / d + (g < b ? 6 : 0) : mx === g ? (b - r) / d + 2 : (r - g) / d + 4; h *= 60; }
  return [h, s, l]; }
function hsl2rgb(h, s, l){ h = ((h % 360) + 360) % 360 / 360; const f = (p, q, t) => { t = wrap01(t); if (t < 1 / 6) return p + (q - p) * 6 * t; if (t < .5) return q; if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6; return p; };
  if (s === 0) return [l * 255, l * 255, l * 255]; const q = l < .5 ? l * (1 + s) : l + s - l * s, p = 2 * l - q;
  return [f(p, q, h + 1 / 3) * 255, f(p, q, h) * 255, f(p, q, h - 1 / 3) * 255]; }
function hueShift(c, deg){ const p = parseColor(c); if (!p) return c; const [h, s, l] = rgb2hsl(p); const q = hsl2rgb(h + deg, s, l); return toCss([q[0], q[1], q[2], p[3]]); }

/* ===================== Fonts ===================== */
const FONTS = {
  display: { css: '800 {s}px "Bricolage Grotesque", system-ui, sans-serif', label: "Grotesk" },
  bold:    { css: '{s}px Bungee, Impact, sans-serif', label: "Block" },
  impact:  { css: '{s}px Anton, Impact, "Arial Narrow", sans-serif', label: "Meme (Anton)" },
  script:  { css: '{s}px Pacifico, "Brush Script MT", cursive', label: "Script" },
  round:   { css: '600 {s}px Fredoka, "Arial Rounded MT Bold", sans-serif', label: "Rounded" },
  serif:   { css: 'italic 800 {s}px "Playfair Display", Georgia, serif', label: "Serif" },
  pixel:   { css: '{s}px "Press Start 2P", monospace', label: "Pixel" },
  mono:    { css: '600 {s}px "JetBrains Mono", monospace', label: "Mono" }
};
const FONT_LOADS = ['800 32px "Bricolage Grotesque"', "32px Bungee", "32px Anton", "32px Pacifico", "600 32px Fredoka", 'italic 800 32px "Playfair Display"', '32px "Press Start 2P"', '600 32px "JetBrains Mono"'];
const EMOJI_FONT = '"Apple Color Emoji","Segoe UI Emoji","Noto Color Emoji",sans-serif';

/* ===================== Shapes ===================== */
const SH_OPTS = ["circle", "square", "triangle", "diamond", "hexagon", "star", "heart", "ring", "burst", "bolt", "cloud", "moon", "drop", "plus"];
const PT_OPTS = ["dot", "star", "heart", "confetti", "line", "ring", "square", "triangle", "diamond"];
function rrect(ctx, x, y, w, h, r){ if (ctx.roundRect) ctx.roundRect(x, y, w, h, r); else ctx.rect(x, y, w, h); }
function shapePath(ctx, kind, r){
  ctx.beginPath();
  switch (kind){
    case "square": { const s = r * .88; rrect(ctx, -s, -s, 2 * s, 2 * s, r * .2); break; }
    case "triangle": for (let i = 0; i < 3; i++){ const a = -Math.PI / 2 + i * TAU / 3; ctx.lineTo(Math.cos(a) * r, Math.sin(a) * r + r * .15); } ctx.closePath(); break;
    case "diamond": ctx.moveTo(0, -r); ctx.lineTo(r * .72, 0); ctx.lineTo(0, r); ctx.lineTo(-r * .72, 0); ctx.closePath(); break;
    case "hexagon": for (let i = 0; i < 6; i++){ const a = i * TAU / 6 + Math.PI / 6; ctx.lineTo(Math.cos(a) * r, Math.sin(a) * r); } ctx.closePath(); break;
    case "star": for (let i = 0; i < 10; i++){ const a = -Math.PI / 2 + i * Math.PI / 5, q = i % 2 ? r * .45 : r; ctx.lineTo(Math.cos(a) * q, Math.sin(a) * q); } ctx.closePath(); break;
    case "burst": for (let i = 0; i < 28; i++){ const a = -Math.PI / 2 + i * TAU / 28, q = i % 2 ? r * .74 : r; ctx.lineTo(Math.cos(a) * q, Math.sin(a) * q); } ctx.closePath(); break;
    case "heart": { const s = r / 16; for (let i = 0; i <= 48; i++){ const t = i / 48 * TAU; ctx.lineTo(16 * Math.pow(Math.sin(t), 3) * s * .95, -(13 * Math.cos(t) - 5 * Math.cos(2 * t) - 2 * Math.cos(3 * t) - Math.cos(4 * t)) * s * .95 - s * 2.4); } ctx.closePath(); break; }
    case "ring": ctx.arc(0, 0, r, 0, TAU); ctx.moveTo(r * .62, 0); ctx.arc(0, 0, r * .62, 0, TAU, true); break;
    case "bolt": [[.12, -1], [-.48, .14], [-.02, .14], [-.22, 1], [.52, -.24], [.06, -.24], [.36, -1]].forEach(([x, y]) => ctx.lineTo(x * r, y * r)); ctx.closePath(); break;
    case "cloud": ctx.moveTo(-.4 * r + .36 * r, .12 * r); ctx.arc(-.4 * r, .12 * r, .36 * r, 0, TAU); ctx.moveTo(.5 * r, -.1 * r); ctx.arc(0, -.1 * r, .5 * r, 0, TAU);
      ctx.moveTo(.82 * r, .14 * r); ctx.arc(.44 * r, .14 * r, .38 * r, 0, TAU); ctx.moveTo(-.8 * r, .1 * r); rrect(ctx, -.8 * r, .1 * r, 1.62 * r, .42 * r, .2 * r); break;
    case "moon": { ctx.rotate(-.5); ctx.arc(0, 0, r, 1.0157, TAU - 1.0157); ctx.arc(.5 * r, 0, .85 * r, -1.5378, 1.5378, true); ctx.closePath(); ctx.rotate(.5); break; }
    case "drop": ctx.moveTo(0, -r); ctx.bezierCurveTo(r * .2, -.5 * r, r * .78, -.05 * r, r * .72, .38 * r); ctx.arc(0, .36 * r, .72 * r, 0, Math.PI); ctx.bezierCurveTo(-r * .78, -.05 * r, -r * .2, -.5 * r, 0, -r); break;
    case "plus": rrect(ctx, -.3 * r, -r, .6 * r, 2 * r, .14 * r); rrect(ctx, -r, -.3 * r, 2 * r, .6 * r, .14 * r); break;
    default: ctx.arc(0, 0, r, 0, TAU);
  }
}
function drawGlyph(ctx, glyph, r, color){
  ctx.font = `${Math.max(4, r * 2).toFixed(1)}px ${EMOJI_FONT}`;
  ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillStyle = color || "#fff"; ctx.fillText(glyph, 0, r * .08);
}
function drawMark(ctx, kind, glyph, r, color){
  if (glyph){ drawGlyph(ctx, glyph, r, color); return; }
  if (kind === "line"){ ctx.strokeStyle = color; ctx.lineWidth = Math.max(1, r * .28); ctx.lineCap = "round"; ctx.beginPath(); ctx.moveTo(0, -r * 2); ctx.lineTo(0, r * 2); ctx.stroke(); return; }
  if (kind === "confetti"){ ctx.fillStyle = color; ctx.fillRect(-r, -r * .45, 2 * r, r * .9); return; }
  ctx.fillStyle = color; shapePath(ctx, kind === "dot" ? "circle" : kind, r); ctx.fill(kind === "ring" ? "evenodd" : "nonzero");
}

/* ===================== Motion (all periodic in t, so every loop is seamless) ===================== */
function motionOf(m, t, c, a, W, H, S){
  const o = { dx: 0, dy: 0, rot: 0, sx: 1, sy: 1 }, ph = TAU * c * t, p = wrap01(c * t);
  switch (m){
    case "bounce": { const k = Math.abs(Math.sin(Math.PI * c * t)); o.dy = -k * a * H * .3; const sq = Math.pow(1 - k, 8) * .3 * a; o.sx = 1 + sq; o.sy = 1 - sq; break; }
    case "spin": o.rot = ph; break;
    case "pulse": o.sx = o.sy = 1 + a * .25 * Math.sin(ph); break;
    case "float": o.dy = Math.sin(ph) * a * S * .06; o.rot = Math.sin(ph + .8) * .08 * a; break;
    case "orbit": o.dx = Math.cos(ph) * a * S * .28; o.dy = Math.sin(ph) * a * S * .28; break;
    case "swing": o.rot = Math.sin(ph) * a * .6; break;
    case "heartbeat": { const b = Math.exp(-(((p - .12) / .05) ** 2)) + .7 * Math.exp(-(((p - .3) / .05) ** 2)); o.sx = o.sy = 1 + a * .28 * b; break; }
    case "jelly": { const w = Math.sin(ph * 2) * .14 * a; o.sx = 1 + w; o.sy = 1 - w; o.rot = Math.sin(ph) * .05 * a; break; }
    case "flip": { const v = Math.cos(ph); o.sx = Math.abs(v) < .02 ? .02 * (v < 0 ? -1 : 1) : v; break; }
    case "shake": o.dx = (Math.sin(TAU * 7 * c * t) + .5 * Math.sin(TAU * 13 * c * t)) * S * .018 * a; o.dy = (Math.cos(TAU * 9 * c * t) + .5 * Math.sin(TAU * 11 * c * t)) * S * .018 * a; o.rot = Math.sin(TAU * 5 * c * t) * .04 * a; break;
    case "wiggle": o.rot = Math.sin(TAU * 4 * c * t) * .18 * a * Math.max(0, Math.sin(ph)); break;
    case "pop": { let s; if (p < .18) s = easeOutBack(p / .18); else if (p < .82) s = 1; else s = 1 - easeInCubic((p - .82) / .18); o.sx = o.sy = Math.max(.0001, s); break; }
    case "slide": { let k; if (p < .22) k = -1 + easeOutCubic(p / .22); else if (p < .78) k = 0; else k = easeInCubic((p - .78) / .22); o.dx = k * W * 1.15; break; }
    case "drop": { let k; if (p < .22) k = -1 + easeOutBack(p / .22); else if (p < .78) k = 0; else k = easeInCubic((p - .78) / .22); o.dy = k * H * 1.15; break; }
  }
  return o;
}

/* ===================== Photos ===================== */
const IMAGES = new Map(); // id -> {el, w, h, name, url}
let imgSeq = 0;
async function addImageFile(file){
  const url = URL.createObjectURL(file);
  const img = new Image(); img.src = url; await img.decode();
  const sc = Math.min(1, 1600 / Math.max(img.naturalWidth, img.naturalHeight));
  const c = document.createElement("canvas"); c.width = Math.max(1, Math.round(img.naturalWidth * sc)); c.height = Math.max(1, Math.round(img.naturalHeight * sc));
  c.getContext("2d").drawImage(img, 0, 0, c.width, c.height);
  const id = "img" + (++imgSeq);
  IMAGES.set(id, { el: c, w: c.width, h: c.height, name: (file.name || id).slice(0, 40), url });
  return id;
}
function drawPlaceholder(ctx, w, h, label){
  ctx.save(); ctx.fillStyle = "#2a3040"; ctx.fillRect(-w / 2, -h / 2, w, h);
  ctx.strokeStyle = "rgba(255,255,255,.35)"; ctx.setLineDash([6, 6]); ctx.lineWidth = 2; ctx.strokeRect(-w / 2 + 4, -h / 2 + 4, w - 8, h - 8);
  ctx.fillStyle = "rgba(255,255,255,.7)"; ctx.font = `600 ${Math.max(10, Math.min(w, h) * .07).toFixed(0)}px system-ui, sans-serif`; ctx.textAlign = "center"; ctx.textBaseline = "middle";
  ctx.fillText(label, 0, 0); ctx.restore();
}
/* draw an image covering (or contained in) a box centred on 0,0; optional horizontal warp per strip */
function drawImageBox(ctx, rec, bw, bh, fit, warp){
  const s = fit === "contain" ? Math.min(bw / rec.w, bh / rec.h) : Math.max(bw / rec.w, bh / rec.h);
  const dw = rec.w * s, dh = rec.h * s;
  if (!warp){ ctx.drawImage(rec.el, -dw / 2, -dh / 2, dw, dh); return; }
  const n = 36;
  for (let i = 0; i < n; i++){
    const sy = rec.h * i / n, sh = rec.h / n, dy = -dh / 2 + dh * i / n;
    ctx.drawImage(rec.el, 0, sy, rec.w, sh, -dw / 2 + warp(i / n), dy, dw, dh / n + .6);
  }
}
function maskPath(ctx, mask, bw, bh){
  ctx.beginPath();
  if (mask === "circle") ctx.ellipse(0, 0, bw / 2, bh / 2, 0, 0, TAU);
  else if (mask === "rounded") rrect(ctx, -bw / 2, -bh / 2, bw, bh, Math.min(bw, bh) * .12);
  else ctx.rect(-bw / 2, -bh / 2, bw, bh);
}

/* ===================== Text layout ===================== */
function wrapText(ctx, str, maxW){
  const out = [];
  for (const para of str.split("\n")){
    const words = para.split(/\s+/).filter(Boolean);
    if (!words.length){ out.push(""); continue; }
    let line = words[0];
    for (let i = 1; i < words.length; i++){ const tryL = line + " " + words[i]; if (ctx.measureText(tryL).width <= maxW) line = tryL; else { out.push(line); line = words[i]; } }
    out.push(line);
  }
  return out;
}
const TEXT_GLOBAL = { bounce: "bounce", shake: "shake", slide: "slide", zoom: "pop", float: "float", swing: "swing", heartbeat: "heartbeat", pulse: "pulse", jelly: "jelly" };
