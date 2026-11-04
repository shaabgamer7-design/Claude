
/* ===================== GIF encoder: median-cut palette, ordered or diffusion dither, frame diffing, LZW ===================== */
class ByteWriter {
  constructor(n){ this.buf = new Uint8Array(n || 65536); this.len = 0; }
  ensure(k){ if (this.len + k > this.buf.length){ let n = this.buf.length * 2; while (n < this.len + k) n *= 2; const b = new Uint8Array(n); b.set(this.buf.subarray(0, this.len)); this.buf = b; } }
  byte(v){ this.ensure(1); this.buf[this.len++] = v; }
  bytes(a){ this.ensure(a.length); this.buf.set(a, this.len); this.len += a.length; }
  u16(v){ this.byte(v & 255); this.byte((v >> 8) & 255); }
  str(s){ for (const ch of s) this.byte(ch.charCodeAt(0)); }
  result(){ return this.buf.slice(0, this.len); }
}
const LZW_CODES = new Int16Array(1 << 20), LZW_STAMP = new Int32Array(1 << 20); let lzwGen = 0;
function lzwEncode(idx, len, out){
  let gen = ++lzwGen, size = 9, next = 258, cur = 0, bits = 0;
  const emit = code => { cur |= code << bits; bits += size; while (bits >= 8){ out.byte(cur & 255); cur >>>= 8; bits -= 8; } };
  emit(256);
  let prefix = idx[0];
  for (let i = 1; i < len; i++){
    const k = idx[i], key = (prefix << 8) | k;
    if (LZW_STAMP[key] === gen){ prefix = LZW_CODES[key]; continue; }
    emit(prefix);
    if (next === 4096){ emit(256); gen = ++lzwGen; size = 9; next = 258; }
    else { if (next >= (1 << size)) size++; LZW_STAMP[key] = gen; LZW_CODES[key] = next++; }
    prefix = k;
  }
  emit(prefix); emit(257);
  if (bits > 0) out.byte(cur & 255);
}
function boxStat(items){
  const mn = [255, 255, 255], mx = [0, 0, 0]; let n = 0;
  for (const it of items){ for (let j = 0; j < 3; j++){ if (it[j] < mn[j]) mn[j] = it[j]; if (it[j] > mx[j]) mx[j] = it[j]; } n += it[3]; }
  const rg = [(mx[0] - mn[0]) * 1.1, (mx[1] - mn[1]) * 1.25, mx[2] - mn[2]], ch = rg.indexOf(Math.max(...rg));
  return { items, ch, score: items.length < 2 ? -1 : rg[ch] * Math.sqrt(n) };
}
function medianCut(hist, maxColors){
  const items = [];
  for (let k = 0; k < 32768; k++){ const n = hist[k * 4 + 3]; if (n) items.push([hist[k * 4] / n, hist[k * 4 + 1] / n, hist[k * 4 + 2] / n, n]); }
  if (!items.length) return [[0, 0, 0]];
  if (items.length <= maxColors) return items.map(it => [Math.round(it[0]), Math.round(it[1]), Math.round(it[2])]);
  const boxes = [boxStat(items)];
  while (boxes.length < maxColors){
    let bi = -1, best = 0;
    boxes.forEach((b, i) => { if (b.score > best){ best = b.score; bi = i; } });
    if (bi < 0) break;
    const b = boxes[bi], ch = b.ch, arr = b.items.sort((x, y) => x[ch] - y[ch]);
    let tot = 0; for (const it of arr) tot += it[3];
    let acc = 0, cut = 1;
    for (let i = 0; i < arr.length; i++){ acc += arr[i][3]; if (acc >= tot / 2){ cut = clamp(i + 1, 1, arr.length - 1); break; } }
    boxes.splice(bi, 1, boxStat(arr.slice(0, cut)), boxStat(arr.slice(cut)));
  }
  return boxes.map(b => { let r = 0, g = 0, bl = 0, n = 0; for (const it of b.items){ r += it[0] * it[3]; g += it[1] * it[3]; bl += it[2] * it[3]; n += it[3]; } return [Math.round(r / n), Math.round(g / n), Math.round(bl / n)]; });
}
const BAYER = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5];
function quantizeFrame(d, out, W, H, mode, transp, matte, cache, nearest, pal, T, amp, e0, e1){
  if (mode === "diffuse"){
    e0.fill(0); e1.fill(0); let a = e0, b = e1;
    for (let y = 0; y < H; y++){
      for (let x = 0; x < W; x++){
        const i = y * W + x, p = i << 2; let r = d[p], g = d[p + 1], bl = d[p + 2];
        if (transp){ const al = d[p + 3]; if (al < 128){ out[i] = T; continue; } if (al < 255){ r = (r * al + matte[0] * (255 - al)) / 255; g = (g * al + matte[1] * (255 - al)) / 255; bl = (bl * al + matte[2] * (255 - al)) / 255; } }
        const ei = (x + 1) * 3;
        r += a[ei]; g += a[ei + 1]; bl += a[ei + 2];
        r = r < 0 ? 0 : r > 255 ? 255 : r; g = g < 0 ? 0 : g > 255 ? 255 : g; bl = bl < 0 ? 0 : bl > 255 ? 255 : bl;
        const key = ((r >> 3) << 10) | ((g >> 3) << 5) | (bl >> 3); let k = cache[key]; if (k < 0) k = nearest(key); out[i] = k;
        const c = pal[k], er = r - c[0], eg = g - c[1], eb = bl - c[2];
        a[ei + 3] += er * .4375; a[ei + 4] += eg * .4375; a[ei + 5] += eb * .4375;
        b[ei - 3] += er * .1875; b[ei - 2] += eg * .1875; b[ei - 1] += eb * .1875;
        b[ei] += er * .3125; b[ei + 1] += eg * .3125; b[ei + 2] += eb * .3125;
        b[ei + 3] += er * .0625; b[ei + 4] += eg * .0625; b[ei + 5] += eb * .0625;
      }
      const tmp = a; a = b; b = tmp; b.fill(0);
    }
    return;
  }
  const ord = mode === "ordered";
  for (let y = 0; y < H; y++){
    const by = (y & 3) * 4;
    for (let x = 0; x < W; x++){
      const i = y * W + x, p = i << 2; let r = d[p], g = d[p + 1], bl = d[p + 2];
      if (transp){ const al = d[p + 3]; if (al < 128){ out[i] = T; continue; } if (al < 255){ r = (r * al + matte[0] * (255 - al)) / 255; g = (g * al + matte[1] * (255 - al)) / 255; bl = (bl * al + matte[2] * (255 - al)) / 255; } }
      if (ord){ const th = (BAYER[by + (x & 3)] - 7.5) / 7.5 * amp; r += th; g += th; bl += th; r = r < 0 ? 0 : r > 255 ? 255 : r; g = g < 0 ? 0 : g > 255 ? 255 : g; bl = bl < 0 ? 0 : bl > 255 ? 255 : bl; }
      const key = ((r >> 3) << 10) | ((g >> 3) << 5) | (bl >> 3); let k = cache[key]; if (k < 0) k = nearest(key); out[i] = k;
    }
  }
}
function frameTimes(n, boom){ const a = []; for (let i = 0; i < n; i++) a.push(i / n); if (boom) for (let i = n - 2; i >= 1; i--) a.push(i / n); return a; }
function frameDelays(count, fps){ const a = []; for (let i = 0; i < count; i++) a.push(Math.max(2, Math.round((i + 1) * 100 / fps) - Math.round(i * 100 / fps))); return a; }
function renderForExport(ctx, sp, t, W, H, transparent, acc, n){
  if (!acc){ renderFrame(ctx, sp, t, W, H, { transparent }); return ctx.getImageData(0, 0, W, H); }
  acc.fill(0); const K = 4;
  for (let j = 0; j < K; j++){ renderFrame(ctx, sp, wrap01(t + ((j + .5) / K - .5) * .8 / n), W, H, { transparent }); const d = ctx.getImageData(0, 0, W, H).data; for (let i = 0; i < d.length; i++) acc[i] += d[i]; }
  const img = ctx.createImageData(W, H), d = img.data; for (let i = 0; i < d.length; i++) d[i] = acc[i] / K; return img;
}
async function encodeGif(o, prog, isCancelled){
  const { W, H } = o, n = o.n;
  const cv = document.createElement("canvas"); cv.width = W; cv.height = H;
  const ctx = cv.getContext("2d", { willReadFrequently: true });
  const times = frameTimes(n, o.boomerang), delays = frameDelays(times.length, o.fps);
  const acc = o.blur && !o.transparent ? new Float32Array(W * H * 4) : null;
  const matte = parseColor(o.matte) || [255, 255, 255, 1];
  const grab = t => renderForExport(ctx, o.sp, t, W, H, o.transparent, acc, n);
  const cancelCheck = () => { if (isCancelled()) throw { code: "cancelled" }; };
  /* 1. palette from evenly spaced sample frames */
  const hist = new Float64Array(32768 * 4), samples = Math.min(n, 16), step = Math.max(1, Math.floor(W * H / 50000));
  for (let s = 0; s < samples; s++){
    cancelCheck();
    const d = grab(s / samples).data;
    for (let p = 0; p < d.length; p += 4 * step){
      let r = d[p], g = d[p + 1], b = d[p + 2];
      if (o.transparent){ const a = d[p + 3]; if (a < 128) continue; if (a < 255){ r = (r * a + matte[0] * (255 - a)) / 255; g = (g * a + matte[1] * (255 - a)) / 255; b = (b * a + matte[2] * (255 - a)) / 255; } }
      const q = (((r >> 3) << 10) | ((g >> 3) << 5) | (b >> 3)) * 4; hist[q] += r; hist[q + 1] += g; hist[q + 2] += b; hist[q + 3]++;
    }
    prog(.1 * (s + 1) / samples, "Building the palette…");
    if ((s & 3) === 3) await sleep0();
  }
  const reserve = o.transparent || o.optimize;
  const pal = medianCut(hist, Math.min(o.colors, reserve ? 255 : 256)), P = pal.length, T = reserve ? P : 0;
  const table = new Uint8Array(768);
  for (let i = 0; i < P; i++){ table[i * 3] = pal[i][0]; table[i * 3 + 1] = pal[i][1]; table[i * 3 + 2] = pal[i][2]; }
  const cache = new Int16Array(32768).fill(-1);
  const nearest = key => { const r = ((key >> 10) & 31) * 8 + 4, g = ((key >> 5) & 31) * 8 + 4, b = (key & 31) * 8 + 4; let best = 0, bd = 1e12;
    for (let i = 0; i < P; i++){ const pp = pal[i], dr = pp[0] - r, dg = pp[1] - g, db = pp[2] - b, dd = dr * dr * 3 + dg * dg * 4 + db * db * 2; if (dd < bd){ bd = dd; best = i; } }
    cache[key] = best; return best; };
  /* 2. stream frames */
  const out = new ByteWriter(1 << 20), lz = new ByteWriter(1 << 18);
  out.str("GIF89a"); out.u16(W); out.u16(H); out.byte(0xF7); out.byte(0); out.byte(0); out.bytes(table);
  if (!o.once){ out.byte(0x21); out.byte(0xFF); out.byte(11); out.str("NETSCAPE2.0"); out.byte(3); out.byte(1); out.u16(0); out.byte(0); }
  const N = W * H, cur = new Uint8Array(N), prev = o.optimize && !o.transparent ? new Uint8Array(N) : null, sub = prev ? new Uint8Array(N) : null;
  const amp = clamp(64 / Math.cbrt(P), 6, 24), e0 = new Float32Array((W + 2) * 3), e1 = new Float32Array((W + 2) * 3);
  let changed = 0;
  for (let f = 0; f < times.length; f++){
    cancelCheck();
    const d = grab(times[f]).data;
    quantizeFrame(d, cur, W, H, o.dither, o.transparent, matte, cache, nearest, pal, T, amp, e0, e1);
    let x0 = 0, y0 = 0, w = W, h = H, useT = o.transparent, data = cur;
    if (prev && f > 0){
      let minX = W, minY = H, maxX = -1, maxY = -1;
      for (let y = 0; y < H; y++){ const row = y * W; let hit = false;
        for (let x = 0; x < W; x++) if (cur[row + x] !== prev[row + x]){ if (x < minX) minX = x; if (x > maxX) maxX = x; hit = true; }
        if (hit){ if (y < minY) minY = y; maxY = y; } }
      if (maxX < 0){ minX = minY = maxX = maxY = 0; }
      x0 = minX; y0 = minY; w = maxX - minX + 1; h = maxY - minY + 1; useT = true;
      for (let y = 0; y < h; y++){ const row = (y0 + y) * W + x0, so = y * w; for (let x = 0; x < w; x++){ const i = row + x; if (cur[i] === prev[i]) sub[so + x] = T; else { sub[so + x] = cur[i]; changed++; } } }
      data = sub;
    } else changed += N;
    if (prev) prev.set(cur);
    out.byte(0x21); out.byte(0xF9); out.byte(4); out.byte(((o.transparent ? 2 : 1) << 2) | (useT ? 1 : 0)); out.u16(delays[f]); out.byte(useT ? T : 0); out.byte(0);
    out.byte(0x2C); out.u16(x0); out.u16(y0); out.u16(w); out.u16(h); out.byte(0);
    out.byte(8); lz.len = 0; lzwEncode(data, w * h, lz);
    for (let i = 0; i < lz.len; i += 255){ const k = Math.min(255, lz.len - i); out.byte(k); out.bytes(lz.buf.subarray(i, i + k)); }
    out.byte(0);
    prog(.1 + .9 * (f + 1) / times.length, `Encoding frame ${f + 1} of ${times.length}…`);
    await sleep0();
  }
  out.byte(0x3B);
  return { bytes: out.result(), colors: P, frames: times.length, W, H, changedRatio: changed / (N * times.length) };
}

/* ===================== ZIP (stored) for PNG frame sequences ===================== */
const CRC_T = (() => { const t = new Uint32Array(256); for (let n = 0; n < 256; n++){ let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
function crc32(u8){ let c = 0xFFFFFFFF; for (let i = 0; i < u8.length; i++) c = CRC_T[(c ^ u8[i]) & 255] ^ (c >>> 8); return (c ^ 0xFFFFFFFF) >>> 0; }
function zipStore(files){
  const enc = new TextEncoder(), parts = [], central = []; let off = 0;
  for (const f of files){
    const nm = enc.encode(f.name), crc = crc32(f.data), sz = f.data.length;
    const h = new DataView(new ArrayBuffer(30));
    h.setUint32(0, 0x04034b50, true); h.setUint16(4, 20, true); h.setUint16(12, 0x21, true); h.setUint32(14, crc, true); h.setUint32(18, sz, true); h.setUint32(22, sz, true); h.setUint16(26, nm.length, true);
    parts.push(new Uint8Array(h.buffer), nm, f.data);
    const c = new DataView(new ArrayBuffer(46));
    c.setUint32(0, 0x02014b50, true); c.setUint16(4, 20, true); c.setUint16(6, 20, true); c.setUint16(14, 0x21, true); c.setUint32(16, crc, true); c.setUint32(20, sz, true); c.setUint32(24, sz, true); c.setUint16(28, nm.length, true); c.setUint32(42, off, true);
    central.push(new Uint8Array(c.buffer), nm);
    off += 30 + nm.length + sz;
  }
  const cdSize = central.reduce((s, a) => s + a.length, 0), e = new DataView(new ArrayBuffer(22));
  e.setUint32(0, 0x06054b50, true); e.setUint16(8, files.length, true); e.setUint16(10, files.length, true); e.setUint32(12, cdSize, true); e.setUint32(16, off, true);
  return new Blob([...parts, ...central, new Uint8Array(e.buffer)], { type: "application/zip" });
}
