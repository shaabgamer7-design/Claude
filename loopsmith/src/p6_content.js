
/* ===================== Templates ===================== */
const TEMPLATES = [
  ["Reactions", "OMG", { layers: [{ kind: "background", style: "radial", colors: ["#ff3d77", "#5b0a3c"] }, { kind: "rays", colors: ["rgba(255,255,255,0.14)", "rgba(255,255,255,0)"], count: 16 }, { kind: "rings", colors: ["#ffffff"], count: 4, size: .8, opacity: .5 }, { kind: "particles", motion: "burst", shape: "star", colors: ["#ffe66d", "#ffffff"], count: 34, size: .045, glow: .5 }, { kind: "text", text: "OMG", font: "bold", size: .26, color: "#ffffff", stroke: "#2b0016", motion: "shake", amount: .7 }] }],
  ["Reactions", "LOL", { layers: [{ kind: "background", colors: ["#ffe066", "#ff9f1c"] }, { kind: "pattern", style: "dots", colors: ["rgba(122,46,0,0.12)"], size: .07 }, { kind: "particles", motion: "rise", glyph: "😂", count: 16, size: .09 }, { kind: "text", text: "LOL", font: "bold", size: .28, color: "#ffffff", stroke: "#7a2e00", motion: "bounce", amount: .45, cycles: 2 }] }],
  ["Reactions", "Mind blown", { layers: [{ kind: "background", style: "radial", colors: ["#3a0ca3", "#10002b"] }, { kind: "rings", colors: ["#f72585", "#4cc9f0"], count: 6, size: .9, glow: .6 }, { kind: "particles", motion: "burst", colors: ["#f72585", "#4cc9f0", "#ffffff"], count: 60, size: .03, glow: .8 }, { kind: "shape", glyph: "🤯", size: .44, motion: "heartbeat", amount: 1 }] }],
  ["Reactions", "Thank you", { layers: [{ kind: "background", colors: ["#ffb199", "#ff7a8a"] }, { kind: "particles", motion: "rise", shape: "heart", colors: ["#ffffff", "#ffd6de", "#ff4f6d"], count: 26, size: .05 }, { kind: "text", text: "Thank you!", font: "script", size: .16, color: "#ffffff", shadow: "rgba(120,20,40,0.35)", motion: "wave", amount: .5 }] }],
  ["Reactions", "Nope", { layers: [{ kind: "background", style: "solid", colors: ["#17171a"] }, { kind: "shape", shape: "ring", color: "#ff453a", size: .78, motion: "pulse", amount: .2, opacity: .35 }, { kind: "text", text: "NOPE", font: "impact", size: .3, color: "#ff453a", motion: "shake", amount: 1, cycles: 2 }, { kind: "fx", style: "vignette", amount: .7 }] }],
  ["Reactions", "Mic drop", { layers: [{ kind: "background", style: "radial", colors: ["#2b2d42", "#0b0c10"] }, { kind: "rings", colors: ["#f2c14e"], count: 3, size: .7, y: .8, opacity: .6 }, { kind: "shape", glyph: "🎤", size: .4, y: .58, motion: "drop" }, { kind: "text", text: "MIC DROP", font: "bold", size: .1, y: .16, color: "#f2c14e", motion: "zoom" }] }],
  ["Greetings", "Happy birthday", { layers: [{ kind: "background", colors: ["#2b2d42", "#5c3c92"] }, { kind: "particles", motion: "rise", glyph: "🎈", count: 12, size: .1 }, { kind: "particles", motion: "fall", shape: "confetti", colors: ["#ef476f", "#ffd166", "#06d6a0", "#118ab2", "#ffffff"], count: 70, size: .028 }, { kind: "text", text: "Happy\nBirthday!", font: "round", size: .15, color: "#ffffff", stroke: "#5c3c92", motion: "pop", amount: .6 }] }],
  ["Greetings", "Love pulse", { title: "Love pulse", layers: [{ kind: "background", colors: ["#22072f", "#5a1660", "#a8326d"] }, { kind: "particles", motion: "rise", shape: "heart", count: 34, size: .06, colors: ["#ff6fa8", "#ffb3d1", "#ffffff"], glow: .6, seed: 11 }, { kind: "shape", shape: "heart", color: "#ff3d7f", size: .42, y: .47, motion: "heartbeat", amount: .9, glow: 1 }, { kind: "text", text: "LOVE", font: "bold", size: .12, y: .46, color: "#ffffff", motion: "heartbeat", amount: .6, shadow: "rgba(60,0,30,0.5)" }] }],
  ["Greetings", "Good morning", { layers: [{ kind: "background", colors: ["#7ec8f2", "#ffe3a3"] }, { kind: "rays", colors: ["rgba(255,255,255,0.28)", "rgba(255,255,255,0)"], count: 14, y: .78 }, { kind: "shape", shape: "circle", color: "#ffc93c", size: .42, y: .78, motion: "pulse", amount: .15, glow: 1 }, { kind: "shape", shape: "cloud", color: "#ffffff", size: .26, x: .24, y: .3, motion: "float", amount: .5, opacity: .9 }, { kind: "text", text: "Good morning", font: "script", size: .13, y: .52, color: "#ffffff", shadow: "rgba(30,60,90,0.3)", motion: "float" }] }],
  ["Greetings", "Happy holidays", { layers: [{ kind: "background", style: "radial", colors: ["#2c4a7a", "#0b1730"] }, { kind: "particles", motion: "fall", glyph: "❄️", count: 26, size: .05 }, { kind: "particles", motion: "fall", count: 70, size: .012, colors: ["#ffffff"], seed: 9 }, { kind: "text", text: "Happy Holidays", font: "serif", size: .12, color: "#ffffff", glow: .5, motion: "float" }] }],
  ["Greetings", "Congrats", { layers: [{ kind: "background", colors: ["#1b1f3a", "#3a2e7a"] }, { kind: "particles", motion: "fountain", shape: "confetti", colors: ["#ff5c8a", "#ffd60a", "#3ddc84", "#3a86ff", "#ffffff"], count: 90, size: .03, y: 1.02 }, { kind: "text", text: "Congrats!", font: "bold", size: .15, color: "#ffd60a", stroke: "#1b1f3a", motion: "bounce", amount: .35, cycles: 2 }] }],
  ["Loaders", "Neon loader", { layers: [{ kind: "background", style: "radial", colors: ["#1a0b3b", "#05020f"] }, { kind: "pattern", style: "dots", colors: ["rgba(47,245,255,0.10)"], size: .08 }, { kind: "orbit", colors: ["#2ff5ff", "#ff2fd0"], count: 12, size: .38, glow: 1 }, { kind: "text", text: "LOADING", font: "pixel", size: .045, color: "#e9fbff", motion: "wave", amount: .4 }] }],
  ["Loaders", "Typing dots", { layers: [{ kind: "background", style: "solid", colors: ["#dfe4ee"] }, { kind: "shape", shape: "square", color: "#ffffff", size: .6 }, { kind: "shape", shape: "circle", color: "#8e94a3", size: .1, x: .38, motion: "bounce", amount: .2, cycles: 2 }, { kind: "shape", shape: "circle", color: "#8e94a3", size: .1, x: .5, motion: "bounce", amount: .2, cycles: 2, phase: .15 }, { kind: "shape", shape: "circle", color: "#8e94a3", size: .1, x: .62, motion: "bounce", amount: .2, cycles: 2, phase: .3 }] }],
  ["Loaders", "Equalizer", { layers: [{ kind: "background", colors: ["#06141b", "#0f3443"] }, { kind: "blob", colors: ["#34e89e", "#0f3443"], size: .7, amount: 1, glow: .4, y: .45 }, { kind: "bars", colors: ["#34e89e", "#9ef01a"], count: 16, y: .85, amount: 1, cycles: 2, size: .8 }] }],
  ["Backgrounds", "Synth sunset", { layers: [{ kind: "background", colors: ["#120338", "#6a0d83", "#f2545b"] }, { kind: "particles", motion: "twinkle", shape: "star", count: 40, size: .02, colors: ["#ffffff"], glow: .5, seed: 5 }, { kind: "shape", shape: "circle", color: "#ffbd59", size: .5, y: .56, motion: "pulse", amount: .1, glow: 1.2 }, { kind: "pattern", style: "floor", colors: ["#ff71ce"], y: .64 }, { kind: "fx", style: "scanlines", amount: .5 }] }],
  ["Backgrounds", "Liquid blob", { layers: [{ kind: "background", colors: ["#0f2027", "#2c5364"] }, { kind: "blob", colors: ["#00f5d4", "#9b5de5"], size: .62, amount: 1, glow: .6 }, { kind: "particles", motion: "rise", count: 30, size: .015, colors: ["#ffffff"], glow: .5, opacity: .7 }] }],
  ["Backgrounds", "Warp speed", { layers: [{ kind: "background", style: "solid", colors: ["#02010a"] }, { kind: "particles", motion: "twinkle", shape: "dot", count: 60, size: .01, colors: ["#ffffff"] }, { kind: "particles", motion: "burst", shape: "dot", count: 140, size: .016, colors: ["#ffffff", "#9ad1ff"], glow: .4, cycles: 1 }] }],
  ["Backgrounds", "Ocean waves", { layers: [{ kind: "background", colors: ["#89f7fe", "#66a6ff"] }, { kind: "shape", shape: "cloud", color: "#ffffff", size: .26, x: .26, y: .22, motion: "float", amount: .5 }, { kind: "shape", shape: "cloud", color: "#ffffff", size: .18, x: .74, y: .32, motion: "float", amount: .5, phase: .4, opacity: .85 }, { kind: "waves", colors: ["#3a86ff", "#2559c9", "#143a8a"], y: .58 }] }],
  ["Stickers", "Sparkle star", { layers: [{ kind: "background", style: "solid", colors: ["#1b1f3a"] }, { kind: "particles", motion: "swirl", shape: "star", colors: ["#ffd23f", "#ffffff"], count: 14, size: .05, glow: .4 }, { kind: "shape", shape: "star", color: "#ffd23f", size: .6, motion: "jelly", amount: .8, glow: .4 }] }],
  ["Stickers", "NEW! badge", { layers: [{ kind: "background", style: "solid", colors: ["#ffffff"] }, { kind: "shape", shape: "burst", color: "#ff3b3b", size: .82, motion: "spin", cycles: 1 }, { kind: "text", text: "NEW!", font: "bold", size: .16, color: "#ffffff", motion: "pulse", amount: .5 }] }],
  ["Stickers", "Heartbeat", { layers: [{ kind: "background", style: "solid", colors: ["#fff0f3"] }, { kind: "rings", colors: ["#ff3d7f"], count: 3, size: .7, opacity: .5 }, { kind: "shape", shape: "heart", color: "#ff3d7f", size: .66, motion: "heartbeat", amount: 1 }] }],
  ["Stickers", "Thumbs up", { layers: [{ kind: "background", style: "solid", colors: ["#e8f1ff"] }, { kind: "rings", colors: ["#3a86ff"], count: 3, size: .75, opacity: .6 }, { kind: "shape", glyph: "👍", size: .58, motion: "jelly", amount: .9 }] }]
];
const TPL_CATS = ["All", "Reactions", "Greetings", "Loaders", "Backgrounds", "Stickers"];
const tplSpec = i => normSpec({ title: TEMPLATES[i][1], ...TEMPLATES[i][2] });

const SURPRISES = [
  "A sleepy moon rocking gently on a cloud while tiny stars twinkle, soft pastel night",
  "Retro arcade “GAME OVER” glitching over a scrolling pixel grid",
  "Pizza slices raining down on a sunny yellow background with “FRIDAY” bouncing in bold",
  "A lava-lamp blob morphing in purple and orange with bubbles rising",
  "Vaporwave sunset with a perspective grid floor and “CHILL” in chrome italic serif",
  "Gold coins bursting from the center with “PAYDAY!” popping in",
  "Cherry blossom petals drifting across a calm pink sky with “Spring” in script",
  "A neon lightning bolt flickering with “POWER UP” in pixel type",
  "A coffee cup emoji floating with bubbles rising and “Monday mode” typing out",
  "Rocket emoji orbiting a glowing planet in a starfield with “Launch day”",
  "Hearts orbiting a beating heart with “Miss you” in rounded type",
  "Equalizer bars bouncing to a beat under a “NOW PLAYING” title",
  "Snowflakes falling on a deep blue night with “Let it snow” in elegant serif",
  "A spinning donut emoji on a pink checkerboard with sprinkles of confetti falling",
  "Comic “BOOM!” starburst shaking with halftone dots and speed rays",
  "Ocean waves rolling under a setting sun with a seagull drifting by",
  "Fire emoji flickering with orange sparks rising and “HOT TAKE” in meme font",
  "Minimal loading spinner, cobalt dots on white, very clean",
  "Party popper confetti fountain with “Congrats!” bouncing",
  "A ghost emoji floating in a misty purple vignette with twinkling stars"
];

/* ===================== Built-in director ===================== */
const PALETTES = {
  sunset: ["#2b1055", "#d53369", "#ffb347"], ocean: ["#03256c", "#1768ac", "#06bee1"], forest: ["#0b3d20", "#2f7d4a", "#a7d676"], neon: ["#0b0420", "#ff2fd0", "#2ff5ff"],
  pastel: ["#ffd6e8", "#cfe8ff", "#ff8fc4"], night: ["#05081a", "#16213e", "#ffd166"], fire: ["#1a0500", "#c1121f", "#ffb703"], gold: ["#2a1a00", "#b8860b", "#ffe08a"],
  candy: ["#ff9ecd", "#ffd166", "#3a86ff"], mono: ["#111111", "#2a2a2a", "#f5f5f5"], love: ["#3b0a3f", "#9b1d64", "#ff6fa8"], ice: ["#0b2545", "#8da9c4", "#eef4ed"], sunny: ["#ffd60a", "#ff9f1c", "#e63946"]
};
const COLORWORDS = { red: "#ff3b3b", pink: "#ff6fb5", orange: "#ff9a1f", yellow: "#ffd60a", gold: "#ffcf40", green: "#3ddc84", teal: "#2ec4b6", blue: "#3a86ff", cobalt: "#2f3fe0", cyan: "#2ff5ff", purple: "#9b5de5", violet: "#8f6bff", white: "#ffffff", black: "#111111", silver: "#d9dde6", magenta: "#ff2fd0", lime: "#b8f74b" };
const EMOJI = { cat: "🐱", kitten: "🐱", dog: "🐶", puppy: "🐶", pizza: "🍕", coffee: "☕", rocket: "🚀", fire: "🔥", ghost: "👻", money: "💸", coin: "🪙", donut: "🍩", doughnut: "🍩", balloon: "🎈", gift: "🎁", present: "🎁", cake: "🎂", sun: "☀️", moon: "🌙", music: "🎵", thumbs: "👍", clap: "👏", laugh: "😂", cry: "😭", sunglasses: "😎", party: "🎉", popper: "🎉", crown: "👑", gem: "💎", taco: "🌮", burger: "🍔", unicorn: "🦄", alien: "👽", robot: "🤖", skull: "💀", eyes: "👀", lightning: "⚡", rainbow: "🌈", butterfly: "🦋", bee: "🐝", fish: "🐟", bird: "🐦", seagull: "🕊️", snowman: "⛄", pumpkin: "🎃", tree: "🎄", popcorn: "🍿", kiss: "💋", beer: "🍺", cocktail: "🍸", trophy: "🏆", medal: "🏅", bomb: "💣", plane: "✈️", car: "🚗", brain: "🧠", poop: "💩", banana: "🍌", avocado: "🥑", cookie: "🍪", shark: "🦈", dinosaur: "🦖", dino: "🦖", frog: "🐸", panda: "🐼", fox: "🦊", penguin: "🐧", owl: "🦉", mushroom: "🍄", planet: "🪐", earth: "🌍", key: "🔑", bell: "🔔", phone: "📱", laptop: "💻", camera: "📷", book: "📚", bulb: "💡", idea: "💡", clock: "⏰", leaf: "🍂", leaves: "🍂", flower: "🌸", petal: "🌸", blossom: "🌸", sakura: "🌸", snowflake: "❄️", snow: "❄️", sparkle: "✨", cloud: "☁️" };
const SHAPE_WORDS = { heart: "heart", star: "star", circle: "circle", ball: "circle", square: "square", cube: "square", box: "square", triangle: "triangle", diamond: "diamond", hexagon: "hexagon", ring: "ring", bolt: "bolt", burst: "burst", drop: "drop" };
function findWords(p, dict){ const out = []; for (const w of Object.keys(dict)){ const m = p.match(new RegExp("\\b" + w + "(e?s)?\\b")); if (m) out.push({ w, v: dict[w], plural: !!m[1], idx: m.index }); } return out.sort((a, b) => a.idx - b.idx); }
function shapeMotionFor(p){ const h = (...w) => w.some(x => p.includes(x));
  return h("bounc") ? "bounce" : h("spin", "rotat", "twirl") ? "spin" : h("orbit") ? "orbit" : h("swing", "rock") ? "swing" : h("shake", "vibrat", "angry") ? "shake" : h("jelly", "wobbl", "squish") ? "jelly" : h("flip", "coin") ? "flip" : h("beat", "heartbeat") ? "heartbeat" : h("pop") ? "pop" : h("slide", "zoom past") ? "slide" : h("drop", "fall") ? "drop" : h("pulse", "glow", "breath") ? "pulse" : "float"; }
function textMotionFor(p){ const h = (...w) => w.some(x => p.includes(x));
  return h("glitch", "vhs", "error") ? "glitch" : h("typ", "terminal", "code") ? "typewriter" : h("rainbow") ? "rainbow" : h("flicker", "neon sign") ? "flicker" : h("bounc") ? "bounce" : h("shake", "angry") ? "shake" : h("pop") ? "zoom" : h("beat", "puls") ? "heartbeat" : h("slide") ? "slide" : "wave"; }
function textFontFor(p){ const h = (...w) => w.some(x => p.includes(x));
  return h("pixel", "8-bit", "8 bit", "arcade", "retro game") ? "pixel" : h("script", "cursive", "handwrit") ? "script" : h("meme", "impact") ? "impact" : h("serif", "elegant", "chrome", "luxury", "cinematic") ? "serif" : h("round", "cute", "kawaii", "friendly") ? "round" : h("terminal", "code", "mono") ? "mono" : h("bold", "loud", "poster", "comic", "block") ? "bold" : "display"; }

function localDirect(prompt, seed){
  const p = " " + prompt.toLowerCase() + " ", has = (...w) => w.some(x => p.includes(x)), r = rng(seed);
  const palKey = Object.keys(PALETTES).find(k => p.includes(k)) || (has("love", "heart", "valentine", "miss you") ? "love" : has("snow", "winter", "ice", "frozen") ? "ice" : has("space", "galaxy", "night", "moon", "star") ? "night" : has("party", "confetti", "birthday", "celebrat", "congrat") ? "candy" : has("sea", "water", "wave", "beach") ? "ocean" : has("retro", "synth", "cyber", "glitch", "arcade") ? "neon" : has("flame", "spark", "hot", "fire") ? "fire" : has("money", "coin", "payday", "gold") ? "gold" : has("yellow", "sunny", "friday", "pizza") ? "sunny" : ["night", "sunset", "neon", "ocean", "candy"][Math.floor(r() * 5)]);
  const P = PALETTES[palKey];
  const named = findWords(p, COLORWORDS).map(f => f.v), accent = named[0] || P[2];
  const quoted = (prompt.match(/[“"']([^”"']{1,40})[”"']/) || [])[1];
  const L = [], ids = [...IMAGES.keys()];
  if (ids.length > 1) L.push({ kind: "slides", srcs: ids, trans: has("slide") ? "slide" : has("zoom") ? "zoom" : has("wipe") ? "wipe" : has(" cut", "flash") ? "cut" : "fade" });
  else if (ids.length === 1) L.push({ kind: "image", src: ids[0], frame: has("sticker", "card", "frame", "polaroid") ? "framed" : "full", mask: has("circle", "round") ? "circle" : "rounded", border: has("card", "polaroid", "sticker") ? "#ffffff" : null,
    motion: has("zoom", "punch", "dramatic") ? "zoom" : has("shake", "earthquake", "vibrat") ? "shake" : has("wobble", "jelly", "wavy", "dream") ? "wobble" : has("glitch", "vhs") ? "glitch" : has("float") ? "float" : has("spin") ? "spin" : has("swing") ? "swing" : has("pulse", "beat") ? "pulse" : has(" pan") ? "pan" : "kenburns", amount: .6, size: .72, y: quoted ? .48 : .5 });
  else L.push({ kind: "background", style: has("radial", "glow", "spotlight", "space") ? "radial" : "linear", colors: P.slice(0, 2).concat(has("sunset", "sky", "dawn") ? [P[2]] : []) });
  if (has("vaporwave", "synthwave", "outrun")) L.push({ kind: "pattern", style: "floor", colors: [accent], y: .64 });
  else if (has("grid", "checker", "stripe", "pattern", "polka", "halftone")) L.push({ kind: "pattern", style: has("checker") ? "checker" : has("stripe") ? "stripes" : has("grid") ? "grid" : "dots", colors: ["rgba(255,255,255,0.12)"], size: .1 });
  if (has("sunburst", " rays", "comic", "speed lines", "boom")) L.push({ kind: "rays", colors: [withAlpha(accent, .25), "rgba(255,255,255,0)"], count: 14, y: has("sunset") ? .75 : .5 });
  if (has("space", "galaxy", "night", "starfield", "stars twinkl", "twinkl")) L.push({ kind: "particles", motion: "twinkle", shape: "star", count: 45, size: .022, colors: ["#ffffff", "#ffe9a8"], glow: .6 });
  if (has("sunset", "sunrise", "setting sun")) L.push({ kind: "shape", shape: "circle", color: "#ffcf5c", size: .4, y: .6, motion: "pulse", amount: .2, glow: 1 });
  if (has("wave", "ocean", "sea ", "beach")) L.push({ kind: "waves", colors: has("sunset") ? ["#5b2a86", "#3a1d63", "#22103f"] : ["#3a86ff", "#2559c9", "#143a8a"], y: .66 });
  if (has("ripple", "radar", "sonar", "ring")) L.push({ kind: "rings", colors: [accent], count: 5, size: .65, glow: .6 });
  if (has("blob", "liquid", "lava", "morph", "organic")) L.push({ kind: "blob", colors: [accent, P[1]], size: .55, amount: .9, glow: .6 });
  if (has("equalizer", "audio", "now playing", "beat", "music")) L.push({ kind: "bars", colors: [accent, P[2]], count: 14, y: .82, amount: .9, cycles: 2 });
  if (has("loading", "spinner", "loader", "progress")) L.push({ kind: "orbit", colors: [accent], count: 10, size: .32, glow: .8 });
  if (has("confetti")) L.push({ kind: "particles", motion: has("fountain", "popper", "cannon") ? "fountain" : "fall", shape: "confetti", count: 80, size: .03, y: 1.02, colors: ["#ff5c8a", "#ffd60a", "#3ddc84", "#3a86ff", "#9b5de5"] });
  if (has("rain ", "raining", "rainy")) L.push({ kind: "particles", motion: "fall", shape: "line", count: 90, size: .012, colors: ["rgba(200,220,255,0.7)"] });
  if (has("spark", "ember", "firefl")) L.push({ kind: "particles", motion: "rise", shape: "dot", count: 40, size: .02, colors: ["#ffb703", "#fb8500", "#ffe08a"], glow: .8 });
  if (has("bubble")) L.push({ kind: "particles", motion: "rise", shape: "ring", count: 26, size: .04, colors: ["rgba(255,255,255,0.8)"] });
  const many = /(rain|falling|shower|lots of|many|swarm|everywhere|burst|explod|fountain|flying|floating|drifting|cannon)/.test(p);
  const pMotion = /(rain|fall|drop|shower)/.test(p) ? "fall" : /(burst|explod)/.test(p) ? "burst" : /(swirl|orbit|around|vortex)/.test(p) ? "swirl" : /(fountain|cannon|spray|popper)/.test(p) ? "fountain" : /(drift|fly|across)/.test(p) ? "drift" : "rise";
  let focal = 0;
  findWords(p, EMOJI).slice(0, 2).forEach(f => {
    if (f.plural || many || f.w === "snow" || f.w === "leaves" || f.w === "petal"){ L.push({ kind: "particles", glyph: f.v, motion: pMotion, count: pMotion === "burst" ? 24 : 16, size: .085, x: .5, y: pMotion === "fountain" ? 1 : .5 }); }
    else if (focal++ < 1) L.push({ kind: "shape", glyph: f.v, size: quoted ? .36 : .46, y: quoted ? .4 : .5, motion: shapeMotionFor(p), amount: .7, cycles: has("bounc") ? 2 : 1 });
  });
  const sw = findWords(p, SHAPE_WORDS)[0];
  if (sw){
    if (sw.plural || many) L.push({ kind: "particles", shape: ["heart", "star", "ring", "diamond", "triangle", "square"].includes(sw.v) ? sw.v : "dot", motion: pMotion, count: 30, size: .05, colors: [accent, "#ffffff"], glow: has("glow", "neon") ? .7 : 0 });
    else if (!focal++) L.push({ kind: "shape", shape: sw.v, color: accent, size: quoted ? .3 : .4, y: quoted ? .4 : .52, glow: has("glow", "neon") ? 1 : .3, motion: shapeMotionFor(p), amount: .7, cycles: has("bounc") ? 2 : 1 });
  }
  if (quoted) L.push({ kind: "text", text: quoted, y: focal || ids.length === 1 ? .78 : .5, size: quoted.length > 12 ? .1 : .17, color: "#ffffff", font: textFontFor(p), motion: textMotionFor(p), glow: has("glow", "neon") ? .6 : 0, stroke: has("meme", "comic", "bold") ? "#111111" : null, shadow: "rgba(0,0,0,0.35)", amount: .6 });
  if (has("vignette", "cinematic", "moody", "mist")) L.push({ kind: "fx", style: "vignette", amount: .7 });
  if (has("scanline", "crt", "vhs", "retro")) L.push({ kind: "fx", style: "scanlines", amount: .5 });
  if (L.length < 2 || (L.length === 2 && L[1].kind === "pattern")) L.push({ kind: "blob", colors: [accent, P[1]], size: .5, amount: .9, glow: .5 }, { kind: "particles", motion: "rise", count: 30, size: .02, colors: ["#ffffff"], glow: .5 });
  let sp = normSpec({ title: (quoted || prompt.split(/[,.;]/)[0] || "Photo loop").slice(0, 40), layers: L.map(l => ({ ...l, seed: Math.floor(r() * 1e9) })) });
  if (activeStyle) sp = restyle(sp, activeStyle);
  return sp;
}

/* ===================== Claude prompts ===================== */
function layerGuide(withPhotos){
  return `Layer kinds (fields optional unless noted):
- background {style: linear|radial|conic|solid, colors: [2-4], angle: 0-360, spin: bool}
- pattern {style: dots|checker|stripes|grid|floor, colors: [1 subtle rgba], size: 0.04-0.2, y: horizon for floor}
- shape {shape: ${SH_OPTS.join("|")}, glyph: one emoji that replaces the shape, color, outline: bool, motion: ${SHAPE_MOTIONS.join("|")}, amount, cycles, phase: 0-1 delay, size: 0.05-0.8, x, y, glow}
- text {text: max 40 chars ("\\n" breaks a line), font: display|bold|impact|script|round|serif|pixel|mono, upper: bool, color, stroke: color|null, shadow: color|null, box: color|null, motion: ${TEXT_MOTIONS.join("|")}, amount, cycles, phase, size: 0.05-0.3, x, y, glow}
- particles {shape: ${PT_OPTS.join("|")}, glyph: one emoji, colors: [1-5], motion: rise|fall|drift|burst|swirl|twinkle|fountain, count: 5-150, size: 0.01-0.1, x, y (origin for burst, swirl, fountain), cycles, glow}
- waves {colors: [2-4 back to front], y: water line, amount, cycles}
- rings {colors, count: 2-10, size: 0.3-1.2, x, y, cycles, glow}   (ripples)
- rays {colors: [2], count: 6-20, x, y, cycles, reverse: bool}   (sunburst)
- orbit {colors, count: 6-16, size: 0.2-0.6, x, y, cycles, glow}   (loading spinner)
- blob {colors: [2], size: 0.3-0.8, x, y, amount, cycles, glow}   (liquid blob)
- bars {colors, count: 8-24, size: total width 0.4-0.9, y: baseline, amount, cycles}   (equalizer)
- fx {style: vignette|scanlines|lightleak, amount}   (finishing effect, place it just under the text)${withPhotos ? `
- image {src: photo id, frame: full|framed, fit: cover|contain, motion: ${IMG_MOTIONS.join("|")}, mask: none|rounded|circle, border: color|null, size, x, y, amount, cycles}
- slides {srcs: [photo ids], trans: fade|slide|zoom|wipe|cut, kenburns: bool, amount}` : ""}`;
}
function directorPrompt(brief, c, sentPhotos){
  const st = activeStyle ? STYLES[activeStyle] : null, ids = [...IMAGES.keys()];
  const photoNote = ids.length ? `\nPhotos available: ${ids.map(id => `${id} ("${IMAGES.get(id).name}")`).join(", ")}. ${sentPhotos ? `You can see ${sentPhotos === 1 ? "the first photo" : "the first " + sentPhotos + " photos"} in the attached image${sentPhotos > 1 ? "s" : ""}. ` : "You cannot see them; use their names as hints. "}Build every variant around the photo${ids.length > 1 ? "s" : ""}: an image layer (frame "full" as a backdrop, or "framed" as a card or sticker)${ids.length > 1 ? " or a slides layer with all of them" : ""}, a motion that suits the content, overlays that match its mood, and any text kept clear of faces (top or bottom).` : "";
  return `You are the art director of a motion-graphics studio. Design 4 different seamless-looping animated GIF scenes for the brief below. A vector engine renders your JSON, so every motion loops perfectly and text renders exactly as written.

Reply with only JSON: {"variants":[{"title":"2-5 words","layers":[...]}, ...exactly 4]}
Variant 1 is faithful to the brief, 2 is bolder and more energetic, 3 is minimal and elegant, 4 is an unexpected creative twist. Each has 3-9 layers listed bottom to top, starting with a background${ids.length ? " or a full-frame image/slides" : ""}.

Canvas ${c.W}x${c.H} (${c.aspect}), loop ${c.dur}s. x and y are 0-1 fractions of width and height (0.5,0.5 is the centre); size is a fraction of the shorter side. Keep text and the main subject within 0.1-0.9. cycles is an integer 1-4 (repeats per loop; higher is faster). amount 0-1 is motion strength. glow 0-2. opacity 0-1. Colours are hex or rgba().

${layerGuide(ids.length > 0)}

Craft: one clear focal subject; depth from background to foreground; a cohesive 3-5 colour palette with strong contrast; text only if the brief asks for words (use them exactly), always legible (stroke, shadow or box on busy backgrounds); motion that suits the mood. Use emoji glyphs for concrete objects such as animals, food and props.
Style: ${st ? st.label + ": " + st.cue : "choose what fits the brief"}.${photoNote}
Brief: ${JSON.stringify(brief || "Animate the photo beautifully")}`;
}
function refinePrompt(instr, c, sp){
  return `You edit looping animated GIF scenes that a vector engine renders. Apply the requested change to the scene below and reply with only the complete updated scene as JSON {"title": string, "layers": [...]}. Keep every layer and field the request does not touch, including "id" and "role" fields, and keep the layer order unless asked.

Canvas ${c.W}x${c.H}. x, y and size are 0-1 fractions; cycles is an integer 1-6 (higher is faster); amount 0-1; glow 0-2; opacity 0-1.
${layerGuide(IMAGES.size > 0)}

Scene: ${JSON.stringify(sp)}
Request: ${JSON.stringify(instr)}`;
}

/* local fallback for Refine */
function localRefine(sp, instr){
  const p = " " + instr.toLowerCase() + " ", has = (...w) => w.some(x => p.includes(x)), s = clone(sp), done = [];
  const focal = s.layers.filter(l => !l.role && ["shape", "text", "image"].includes(l.kind));
  if (has("slower", "slow down", "calmer")){ s.layers.forEach(l => { if (l.cycles > 1) l.cycles--; }); done.push("slower"); }
  if (has("faster", "speed up", "quicker", "more energ")){ s.layers.forEach(l => { if ("cycles" in l && l.kind !== "background") l.cycles = Math.min(6, l.cycles + 1); }); done.push("faster"); }
  if (has("bigger", "larger")){ focal.forEach(l => { if ("size" in l) l.size = Math.min(1.2, l.size * 1.25); }); done.push("bigger"); }
  if (has("smaller", "tinier")){ focal.forEach(l => { if ("size" in l) l.size = l.size * .8; }); done.push("smaller"); }
  if (has("more ")){ s.layers.forEach(l => { if (l.kind === "particles") l.count = Math.min(220, Math.round(l.count * 1.6)); }); done.push("more particles"); }
  if (has("fewer", "less ")){ s.layers.forEach(l => { if (l.kind === "particles") l.count = Math.max(3, Math.round(l.count * .6)); }); done.push("fewer particles"); }
  if (has("no glow", "remove glow")){ s.layers.forEach(l => { if ("glow" in l) l.glow = 0; }); done.push("no glow"); }
  else if (has("glow")){ s.layers.forEach(l => { if ("glow" in l && !l.role) l.glow = Math.min(2, (l.glow || 0) + .6); }); done.push("more glow"); }
  const adds = { sparkle: { glyph: "✨", motion: "twinkle", count: 18, size: .05 }, heart: { shape: "heart", motion: "rise", count: 26, size: .05, colors: ["#ff6fa8", "#ffffff"] }, star: { shape: "star", motion: "twinkle", count: 40, size: .025, colors: ["#ffffff", "#ffe9a8"], glow: .5 }, snow: { glyph: "❄️", motion: "fall", count: 24, size: .05 }, confetti: { shape: "confetti", motion: "fall", count: 80, size: .03, colors: ["#ff5c8a", "#ffd60a", "#3ddc84", "#3a86ff"] }, bubble: { shape: "ring", motion: "rise", count: 24, size: .04, colors: ["rgba(255,255,255,0.8)"] }, rain: { shape: "line", motion: "fall", count: 90, size: .012, colors: ["rgba(200,220,255,0.7)"] } };
  if (has("add ")) for (const [w, cfgP] of Object.entries(adds)) if (p.includes(w)){
    const named = findWords(p, COLORWORDS)[0];
    const layer = normLayer({ kind: "particles", ...cfgP, ...(named ? { colors: [named.v, "#ffffff"] } : {}) });
    const ti = s.layers.findIndex(l => l.kind === "text"); if (ti < 0) s.layers.push(layer); else s.layers.splice(ti, 0, layer); done.push("added " + w + "s");
  }
  const q = (instr.match(/[“"']([^”"']{1,40})[”"']/) || [])[1];
  if (q){ const tl = s.layers.find(l => l.kind === "text" && !l.role); if (tl) tl.text = q; else s.layers.push(normLayer({ kind: "text", text: q, size: .15, shadow: "rgba(0,0,0,0.35)" })); done.push("text set"); }
  else if (has("remove text", "no text", "delete text")){ s.layers = s.layers.filter(l => l.kind !== "text" || l.role); done.push("text removed"); }
  const cw = findWords(p, COLORWORDS)[0];
  if (cw && !has("add ")){
    if (has("background")){ const bg = s.layers.find(l => l.kind === "background"); if (bg){ bg.colors = [cw.v, hueShift(cw.v, 30)].map(c => { const q2 = parseColor(c); return toCss([q2[0] * .45, q2[1] * .45, q2[2] * .45, 1]); }); done.push("background recolored"); } }
    else { focal.forEach(l => { if (l.color && l.kind !== "text") l.color = cw.v; }); done.push("recolored"); }
  }
  const sk = Object.keys(STYLES).find(k => p.includes(STYLES[k].label.toLowerCase()));
  if (sk) return { spec: restyle(normSpec(s), sk), note: "Restyled as " + STYLES[sk].label + "." };
  return { spec: normSpec(s), note: done.length ? "Applied: " + done.join(", ") + "." : "" };
}
