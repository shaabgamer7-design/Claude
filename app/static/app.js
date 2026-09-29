/* Avatar Studio front end (no build step, no dependencies). */
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const WPS = 2.4; // spoken words per second

const state = {
  status: null,
  avatars: [],
  voices: [],
  selected: null,
  voiceMode: "tts",
  aspect: "9:16",
  captions: "pop",
  quality: "studio",
  recordedAudio: null,
  renderJob: null,
  editing: null,
  amVoiceBlob: null,
};

// ---------------------------------------------------------------- utilities
async function api(path, opts = {}) {
  const res = await fetch(path, opts);
  if (!res.ok) {
    let msg = res.statusText;
    try { msg = (await res.json()).detail || msg; } catch (_) {}
    throw new Error(msg);
  }
  const ct = res.headers.get("content-type") || "";
  return ct.includes("json") ? res.json() : res;
}
const postJSON = (path, body) => api(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });

let toastTimer;
function toast(msg, bad = false) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.toggle("bad", bad);
  t.classList.remove("hidden");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.add("hidden"), bad ? 7000 : 3200);
}
const fmtTime = (s) => {
  if (s == null) return "";
  s = Math.max(0, Math.round(s));
  return s >= 60 ? `${Math.floor(s / 60)}m ${String(s % 60).padStart(2, "0")}s` : `${s}s`;
};
function segmented(el, onChange) {
  el.addEventListener("click", (e) => {
    const b = e.target.closest("button[data-v]");
    if (!b || b.disabled) return;
    $$("button", el).forEach((x) => x.classList.toggle("on", x === b));
    onChange(b.dataset.v);
  });
}
function setSeg(el, v) { $$("button", el).forEach((x) => x.classList.toggle("on", x.dataset.v === v)); }
function wordsOf(text) { return text.trim().split(/\s+/).filter(Boolean); }
function safeStore(key, val) { try { localStorage.setItem(key, val); } catch (_) {} }
function safeGet(key) { try { return localStorage.getItem(key); } catch (_) { return null; } }

// ---------------------------------------------------------------- navigation
function show(view) {
  $$(".nav-item").forEach((b) => b.classList.toggle("active", b.dataset.view === view));
  $$(".view").forEach((v) => v.classList.toggle("active", v.id === `view-${view}`));
  if (view === "library") loadVideos();
  if (view === "settings") loadStatus();
  if (view === "avatars") loadAvatars();
  window.scrollTo({ top: 0 });
}
$$(".nav-item").forEach((b) => b.addEventListener("click", () => show(b.dataset.view)));

// ---------------------------------------------------------------- status
async function loadStatus() {
  const st = await api("/api/status");
  state.status = st;
  const missing = !st.models.wav2lip.ready;
  $("#settings-dot").classList.toggle("hidden", !missing);
  const banner = $("#setup-banner");
  if (missing) {
    banner.innerHTML = `<svg viewBox="0 0 24 24"><path d="M12 9v4M12 17h.01M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/></svg>
      <div><b>One-time setup: download the AI models</b><span class="muted small">About 480 MB. After that, everything runs offline on this computer.</span></div>
      <button class="btn primary" id="banner-dl">Download now</button>`;
    banner.classList.remove("hidden");
    $("#banner-dl").onclick = () => { show("settings"); downloadModels(); };
  } else banner.classList.add("hidden");

  // models
  $("#model-list").innerHTML = Object.values(st.models).map((m) => `
    <div class="li"><div><div class="t">${esc(m.title)}</div><div class="s">${esc(m.file)} · ~${m.size_mb} MB${m.required ? "" : " · optional"}</div></div>
    <span class="st ${m.ready ? "ok" : m.required ? "bad" : "warn"}">${m.ready ? "Ready" : "Missing"}</span></div>`).join("");
  $("#btn-download-models").classList.toggle("hidden", Object.values(st.models).every((m) => m.ready));

  // engines
  const ol = st.ollama;
  $("#engine-list").innerHTML = `
    <div class="li"><div><div class="t">FFmpeg</div><div class="s">${st.ffmpeg.ok ? (st.ffmpeg.subtitles ? "Video encoding + captions" : "Captions unavailable in this build") : esc(st.ffmpeg.error)}</div></div>
      <span class="st ${st.ffmpeg.ok ? (st.ffmpeg.subtitles ? "ok" : "warn") : "bad"}">${st.ffmpeg.ok ? "Ready" : "Missing"}</span></div>
    <div class="li"><div><div class="t">Neural voices (edge-tts)</div><div class="s">Free, needs internet while generating</div></div><span class="st ok">Ready</span></div>
    <div class="li"><div><div class="t">Voice cloning (Chatterbox)</div><div class="s">${st.voice_clone ? "Offline cloning + voice conversion" : "Optional add-on: run <code>install_voice_clone</code>"}</div></div>
      <span class="st ${st.voice_clone ? "ok" : "warn"}">${st.voice_clone ? "Installed" : "Not installed"}</span></div>
    <div class="li"><div><div class="t">Local AI scripts (Ollama)</div><div class="s">${ol.running ? (ol.model_installed ? `Using ${esc(ol.model)}` : `Run <code>ollama pull ${esc(ol.model)}</code>`) : "Optional: install from ollama.com"}</div></div>
      <span class="st ${ol.running && ol.model_installed ? "ok" : "warn"}">${ol.running ? (ol.model_installed ? "Ready" : "Model missing") : "Not running"}</span></div>`;

  const s = st.settings;
  $("#set-max").value = s.max_video_seconds;
  $("#set-threads").value = s.cpu_threads;
  $("#set-ollama-model").value = s.ollama_model;
  $("#set-ollama-url").value = s.ollama_url;

  // feature gates on the create page
  $('#voice-mode [data-v="clone"]').disabled = !st.voice_clone;
  $("#convert-voice").disabled = !st.voice_clone;
  $("#clone-hint").textContent = st.voice_clone
    ? "Speaks the script in the avatar's own voice sample. Runs fully offline with Chatterbox (MIT licence). Slow on CPU: about 1-3 minutes."
    : "Voice cloning is an optional add-on. Run install_voice_clone once (see README) to enable it.";
  $("#btn-ai-write").title = ol.running ? "" : "Install Ollama (free) to write scripts offline";
  if (!st.models.gfpgan.ready) {
    $('#quality [data-v="studio"] small').textContent = "needs GFPGAN model";
  }
  updateScriptStats();
  updateEstimate();
  if (state.avatars.length) renderAvatarStrip();
  return st;
}

$("#btn-save-settings").onclick = async () => {
  const s = await postJSON("/api/settings", {
    max_video_seconds: +$("#set-max").value, cpu_threads: +$("#set-threads").value,
    ollama_model: $("#set-ollama-model").value.trim() || "qwen2.5:3b",
    ollama_url: $("#set-ollama-url").value.trim() || "http://localhost:11434",
  });
  state.status.settings = s;
  toast("Settings saved");
  loadStatus();
};

async function downloadModels() {
  const job = await api("/api/models/download", { method: "POST" });
  $("#btn-download-models").disabled = true;
  $("#dl-progress").classList.remove("hidden");
  const done = await pollJob(job.id, (j) => {
    $("#dl-stage").textContent = j.stage;
    $("#dl-pct").textContent = Math.round(j.progress * 100) + "%";
    $("#dl-bar").style.width = j.progress * 100 + "%";
  });
  $("#btn-download-models").disabled = false;
  $("#dl-progress").classList.add("hidden");
  if (done.status === "error") toast(done.error, true);
  else toast(done.result?.failures?.length ? "Done, but some optional models failed. See Settings." : "Models ready. You're all set!");
  loadStatus();
}
$("#btn-download-models").onclick = downloadModels;

// ---------------------------------------------------------------- jobs
async function pollJob(id, onUpdate) {
  for (;;) {
    let j;
    try { j = await api(`/api/jobs/${id}`); } catch (e) { await new Promise((r) => setTimeout(r, 1500)); continue; }
    onUpdate && onUpdate(j);
    if (j.status === "done" || j.status === "error") return j;
    await new Promise((r) => setTimeout(r, 1000));
  }
}

async function refreshQueue() {
  try {
    const jobs = await api("/api/jobs");
    const active = jobs.filter((j) => j.status === "running" || j.status === "queued");
    $("#queue").innerHTML = active.map((j) => `
      <div class="q-item"><div class="q-title">${esc(j.title)}</div>
      <div class="muted">${j.status === "queued" ? "Queued" : esc(j.stage)} · ${Math.round(j.progress * 100)}%</div>
      <div class="bar"><span style="width:${j.progress * 100}%"></span></div></div>`).join("");
  } catch (_) {}
  setTimeout(refreshQueue, 2000);
}

// ---------------------------------------------------------------- avatars
async function loadAvatars() {
  state.avatars = await api("/api/avatars");
  const last = safeGet("as.avatar");
  if (!state.selected || !state.avatars.find((a) => a.id === state.selected)) {
    const pick = state.avatars.find((a) => a.id === last && a.status === "ready") || state.avatars.find((a) => a.status === "ready");
    state.selected = pick ? pick.id : null;
  }
  renderAvatarStrip();
  renderAvatarGrid();
  applyAvatarDefaults();
  // keep refreshing while any avatar is preparing
  if (state.avatars.some((a) => a.status === "preparing")) setTimeout(loadAvatars, 2500);
}

const thumbUrl = (a) => `/api/avatars/${a.id}/thumb?v=${encodeURIComponent(a.base?.frames || 0)}-${a.status}`;

function renderAvatarStrip() {
  const strip = $("#avatar-strip");
  strip.innerHTML = state.avatars.map((a) => `
    <button class="av-pick ${a.id === state.selected ? "on" : ""} ${a.status !== "ready" ? "disabled" : ""}" data-id="${a.id}" title="${esc(a.tagline || a.name)}">
      ${a.status === "ready" ? `<img src="${thumbUrl(a)}" alt="">` : `<div class="ph"></div>`}
      <div class="nm">${esc(a.name)}</div>
      <div class="sub">${a.status === "ready" ? esc(a.niche || (a.base?.kind === "video" ? "Video avatar" : "Photo avatar")) : a.status === "error" ? "Failed" : "Preparing…"}</div>
    </button>`).join("") +
    `<button class="av-pick add" id="strip-add"><svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>New avatar</button>`;
  $$(".av-pick[data-id]", strip).forEach((b) => b.onclick = () => {
    const a = state.avatars.find((x) => x.id === b.dataset.id);
    if (a.status !== "ready") return toast(a.status === "error" ? `This avatar failed: ${a.error}` : "Still preparing this avatar…", a.status === "error");
    state.selected = a.id;
    safeStore("as.avatar", a.id);
    renderAvatarStrip();
    applyAvatarDefaults();
  });
  $("#strip-add").onclick = () => openEditor();
  const a = current();
  const empty = $("#preview-empty");
  if (a && !state.renderJob && $("#result-video").classList.contains("hidden")) {
    // The avatar's own base clip, looping silently: a live preview of the "body".
    if (empty.dataset.avatar !== a.id) {
      empty.dataset.avatar = a.id;
      empty.innerHTML = `<video src="/api/avatars/${a.id}/base" muted loop autoplay playsinline></video>`;
    }
  } else if (!a) { empty.dataset.avatar = ""; empty.textContent = "Your video appears here"; }
  $("#btn-render").disabled = !a || !state.status?.models.wav2lip.ready || !!state.renderJob;
}

const current = () => state.avatars.find((a) => a.id === state.selected && a.status === "ready");

function applyAvatarDefaults() {
  const a = current();
  if (!a) { updateEstimate(); return; }
  if (a.tts_voice) $("#tts-voice").value = a.tts_voice;
  $("#tts-rate").value = a.tts_rate || 0; $("#tts-pitch").value = a.tts_pitch || 0;
  $("#tts-rate").dispatchEvent(new Event("input")); $("#tts-pitch").dispatchEvent(new Event("input"));
  if (a.clone_language) $("#clone-lang").value = a.clone_language;
  updateEstimate();
}

function renderAvatarGrid() {
  const grid = $("#avatar-grid");
  if (!state.avatars.length) {
    grid.innerHTML = `<div class="empty"><b>No avatars yet</b>Create one from a short selfie video or a portrait photo.<br><button class="btn primary" onclick="openEditor()">Create your first avatar</button></div>`;
    return;
  }
  grid.innerHTML = state.avatars.map((a) => {
    const badge = a.status === "ready" ? `<span class="badge ok">${a.base?.kind === "video" ? "Video" : "Photo"} · Ready</span>`
      : a.status === "error" ? `<span class="badge bad">Failed</span>` : `<span class="badge">Preparing…</span>`;
    const tags = [a.language, a.tone, a.has_voice_sample ? "Voice sample" : ""].filter(Boolean)
      .map((t) => `<span class="tag">${esc(t.length > 26 ? t.slice(0, 24) + "…" : t)}</span>`).join("");
    return `<div class="card av-card">
      <div class="thumb">${a.status === "ready" ? `<img src="${thumbUrl(a)}" alt="">` : ""}${badge}</div>
      <div class="body"><div class="nm">${esc(a.name)}</div>
        <div class="meta">${esc(a.tagline || a.niche || "")}</div>
        ${a.status === "error" ? `<div class="meta" style="color:var(--bad)">${esc(a.error)}</div>` : ""}
        <div class="tagrow">${tags}</div>
        <div class="actions">
          <button class="btn" data-use="${a.id}" ${a.status !== "ready" ? "disabled" : ""}>Use</button>
          <button class="btn ghost" data-edit="${a.id}">Edit</button>
          <button class="btn ghost danger" data-del="${a.id}" title="Delete"><svg viewBox="0 0 24 24"><path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/></svg></button>
        </div></div></div>`;
  }).join("");
  $$("[data-use]", grid).forEach((b) => b.onclick = () => { state.selected = b.dataset.use; safeStore("as.avatar", b.dataset.use); renderAvatarStrip(); applyAvatarDefaults(); show("create"); });
  $$("[data-edit]", grid).forEach((b) => b.onclick = () => openEditor(state.avatars.find((a) => a.id === b.dataset.edit)));
  $$("[data-del]", grid).forEach((b) => b.onclick = async () => {
    const a = state.avatars.find((x) => x.id === b.dataset.del);
    if (!confirm(`Delete avatar "${a.name}"? Videos already made are kept.`)) return;
    await api(`/api/avatars/${a.id}`, { method: "DELETE" });
    toast("Avatar deleted");
    loadAvatars();
  });
}

// ---------------------------------------------------------------- avatar editor
const TONES = ["Energetic", "Calm & wise", "Witty", "Bold & direct", "Friendly", "Luxury", "Storyteller", "Motivational", "Deadpan funny"];
$("#tone-chips").innerHTML = TONES.map((t) => `<span class="chip">${t}</span>`).join("");
$$("#tone-chips .chip").forEach((c) => c.onclick = () => {
  const inp = $("#am-tone");
  const cur = inp.value.split(",").map((s) => s.trim()).filter(Boolean);
  if (!cur.includes(c.textContent)) cur.push(c.textContent);
  inp.value = cur.join(", ");
});
const AM_FIELDS = ["name", "tagline", "niche", "language", "tone", "personality", "audience", "catchphrases", "cta"];

function openEditor(a = null) {
  state.editing = a;
  state.amVoiceBlob = null;
  $("#am-title").textContent = a ? `Edit ${a.name}` : "New avatar";
  $("#am-save").textContent = a ? "Save changes" : "Create avatar";
  AM_FIELDS.forEach((f) => $(`#am-${f}`).value = a ? a[f] || "" : "");
  if (!a) $("#am-language").value = "English";
  $("#am-tts-voice").value = a?.tts_voice || "en-US-AndrewMultilingualNeural";
  $("#am-face").value = ""; $("#am-voice").value = "";
  const img = $("#am-face-img"), vid = $("#am-face-vid");
  img.classList.add("hidden"); vid.classList.add("hidden"); vid.removeAttribute("src");
  $("#face-drop-text").classList.remove("hidden");
  if (a && a.status === "ready") {
    if (a.base?.kind === "video") { vid.src = `/api/avatars/${a.id}/base`; vid.classList.remove("hidden"); }
    else { img.src = thumbUrl(a); img.classList.remove("hidden"); }
    $("#face-drop-text").classList.add("hidden");
  }
  const vp = $("#am-voice-preview");
  if (a?.has_voice_sample) { vp.src = `/api/avatars/${a.id}/voice?t=${Date.now()}`; vp.classList.remove("hidden"); }
  else { vp.classList.add("hidden"); vp.removeAttribute("src"); }
  $("#am-note").textContent = a ? "Upload a new face only if you want to replace it." : "Preparing a video avatar takes about a minute.";
  $("#avatar-modal").classList.remove("hidden");
  setTimeout(() => $("#am-name").focus(), 50);
}
window.openEditor = openEditor;
$$("[data-close]").forEach((b) => b.onclick = () => $("#avatar-modal").classList.add("hidden"));
$("#avatar-modal").addEventListener("mousedown", (e) => { if (e.target.id === "avatar-modal") $("#avatar-modal").classList.add("hidden"); });
$("#btn-new-avatar").onclick = () => openEditor();

function previewFace(file) {
  const img = $("#am-face-img"), vid = $("#am-face-vid");
  const url = URL.createObjectURL(file);
  $("#face-drop-text").classList.add("hidden");
  if (file.type.startsWith("video")) { img.classList.add("hidden"); vid.src = url; vid.classList.remove("hidden"); }
  else { vid.classList.add("hidden"); img.src = url; img.classList.remove("hidden"); }
}
$("#am-face").onchange = (e) => e.target.files[0] && previewFace(e.target.files[0]);
const drop = $("#face-drop");
["dragenter", "dragover"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("over"); }));
["dragleave", "drop"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("over"); }));
drop.addEventListener("drop", (e) => {
  const f = e.dataTransfer.files[0];
  if (!f) return;
  const dt = new DataTransfer(); dt.items.add(f); $("#am-face").files = dt.files;
  previewFace(f);
});
$("#am-voice").onchange = (e) => {
  const f = e.target.files[0];
  if (!f) return;
  state.amVoiceBlob = null;
  const vp = $("#am-voice-preview"); vp.src = URL.createObjectURL(f); vp.classList.remove("hidden");
};

$("#am-save").onclick = async () => {
  const data = {};
  AM_FIELDS.forEach((f) => data[f] = $(`#am-${f}`).value.trim());
  data.tts_voice = $("#am-tts-voice").value;
  if (!data.name) return toast("Give your avatar a name", true);
  const face = $("#am-face").files[0];
  if (!state.editing && !face) return toast("Add a face video or photo", true);
  const fd = new FormData();
  fd.append("data", JSON.stringify(data));
  if (face) fd.append("face", face);
  const vfile = $("#am-voice").files[0];
  if (vfile) fd.append("voice_sample", vfile);
  else if (state.amVoiceBlob) fd.append("voice_sample", state.amVoiceBlob, "sample.webm");
  $("#am-save").disabled = true;
  try {
    const url = state.editing ? `/api/avatars/${state.editing.id}` : "/api/avatars";
    const res = await api(url, { method: "POST", body: fd });
    $("#avatar-modal").classList.add("hidden");
    toast(res.job ? "Preparing avatar… you can keep working." : "Saved");
    if (!state.editing) { state.selected = res.avatar.id; safeStore("as.avatar", res.avatar.id); }
    loadAvatars();
    if (res.job) pollJob(res.job.id).then((j) => {
      if (j.status === "error") toast(`Avatar failed: ${j.error}`, true);
      else if (j.kind === "avatar") toast(`${data.name} is ready!`);
      loadAvatars();
    });
  } catch (e) { toast(e.message, true); }
  finally { $("#am-save").disabled = false; }
};

// ---------------------------------------------------------------- recording
function recorder(button, label, seconds, onDone) {
  let rec = null, timer = null;
  button.onclick = async () => {
    if (rec) { rec.stop(); return; }
    let stream;
    try { stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: false, noiseSuppression: true } }); }
    catch (e) { return toast("Microphone not available: " + e.message, true); }
    const chunks = [];
    rec = new MediaRecorder(stream);
    rec.ondataavailable = (e) => chunks.push(e.data);
    rec.onstop = () => {
      stream.getTracks().forEach((t) => t.stop());
      clearInterval(timer);
      button.classList.remove("recording");
      label.textContent = "Record again";
      rec = null;
      onDone(new Blob(chunks, { type: chunks[0]?.type || "audio/webm" }));
    };
    rec.start();
    button.classList.add("recording");
    let t = 0;
    label.textContent = `Stop (0s)`;
    timer = setInterval(() => {
      t++;
      label.textContent = `Stop (${t}s)`;
      if (t >= seconds) rec && rec.stop();
    }, 1000);
  };
}
recorder($("#btn-record"), $("#rec-label"), 60, (blob) => {
  state.recordedAudio = blob;
  $("#audio-file").value = "";
  const a = $("#audio-preview"); a.src = URL.createObjectURL(blob); a.classList.remove("hidden");
  updateEstimate();
});
recorder($("#am-record"), $("#am-rec-label"), 30, (blob) => {
  state.amVoiceBlob = blob;
  $("#am-voice").value = "";
  const a = $("#am-voice-preview"); a.src = URL.createObjectURL(blob); a.classList.remove("hidden");
});
$("#audio-file").onchange = (e) => {
  const f = e.target.files[0];
  if (!f) return;
  state.recordedAudio = null;
  const a = $("#audio-preview"); a.src = URL.createObjectURL(f); a.classList.remove("hidden");
  a.onloadedmetadata = updateEstimate;
};

// ---------------------------------------------------------------- script
function maxSeconds() { return state.status?.settings.max_video_seconds || 15; }
function updateScriptStats() {
  const n = wordsOf($("#script").value).length;
  const secs = n / WPS;
  const max = maxSeconds();
  $("#script-stats").textContent = `${n} words · ~${secs.toFixed(0)} s of ${max} s`;
  const bar = $("#script-meter");
  bar.style.width = Math.min(100, (secs / max) * 100) + "%";
  bar.style.background = secs > max ? "var(--bad)" : secs > max * 0.9 ? "var(--warn)" : "var(--ok)";
}
$("#script").addEventListener("input", () => { updateScriptStats(); updateEstimate(); safeStore("as.script", $("#script").value); });

$("#btn-copy-prompt").onclick = async () => {
  const a = current();
  if (!a) return toast("Pick an avatar first", true);
  const topic = $("#topic").value.trim() || "a useful tip for my audience";
  const { prompt } = await postJSON("/api/script/prompt", { avatar_id: a.id, topic, seconds: maxSeconds(), hook_style: $("#hook-style").value });
  try { await navigator.clipboard.writeText(prompt); toast("Prompt copied. Paste it into Claude, then paste the script back here."); }
  catch (_) { window.prompt("Copy this prompt:", prompt); }
};
$("#btn-ai-write").onclick = async () => {
  const a = current();
  if (!a) return toast("Pick an avatar first", true);
  const topic = $("#topic").value.trim();
  if (!topic) { $("#topic").focus(); return toast("Type a topic first", true); }
  const btn = $("#btn-ai-write");
  btn.disabled = true;
  const old = btn.innerHTML;
  btn.innerHTML = "Writing…";
  try {
    const { script } = await postJSON("/api/script/generate", { avatar_id: a.id, topic, seconds: maxSeconds(), hook_style: $("#hook-style").value });
    $("#script").value = script;
    updateScriptStats(); updateEstimate();
    safeStore("as.script", script);
  } catch (e) { toast(e.message, true); }
  finally { btn.disabled = false; btn.innerHTML = old; }
};

// ---------------------------------------------------------------- voice
async function loadVoices() {
  try { state.voices = await api("/api/voices"); } catch (_) { state.voices = []; }
  const opts = (sel) => {
    const feat = state.voices.filter((v) => v.featured), rest = state.voices.filter((v) => !v.featured);
    sel.innerHTML = `<optgroup label="Recommended">${feat.map((v) => `<option value="${v.id}">${esc(v.label)}</option>`).join("")}</optgroup>` +
      (rest.length ? `<optgroup label="All voices">${rest.map((v) => `<option value="${v.id}">${esc(v.label)}</option>`).join("")}</optgroup>` : "");
  };
  opts($("#tts-voice")); opts($("#am-tts-voice"));
  applyAvatarDefaults();
}
segmented($("#voice-mode"), (v) => {
  state.voiceMode = v;
  $$(".voice-pane").forEach((p) => p.classList.toggle("hidden", p.dataset.pane !== v));
  $("#convert-voice").closest(".toggle").classList.toggle("hidden", v === "clone");
  updateEstimate();
});
$("#tts-rate").oninput = (e) => $("#tts-rate-v").textContent = `${e.target.value > 0 ? "+" : ""}${e.target.value}%`;
$("#tts-pitch").oninput = (e) => $("#tts-pitch-v").textContent = `${e.target.value > 0 ? "+" : ""}${e.target.value} Hz`;
$("#btn-preview").onclick = async () => {
  const text = $("#script").value.trim() || "Hi! This is how I sound. Let's make something amazing today.";
  const btn = $("#btn-preview");
  btn.disabled = true;
  try {
    const res = await api("/api/voices/preview", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text.slice(0, 200), voice: $("#tts-voice").value, rate: +$("#tts-rate").value, pitch: +$("#tts-pitch").value }) });
    const url = URL.createObjectURL(await res.blob());
    new Audio(url).play();
  } catch (e) { toast(e.message, true); }
  finally { btn.disabled = false; }
};

// ---------------------------------------------------------------- look
segmented($("#aspect"), (v) => { state.aspect = v; setPreviewAspect(); });
segmented($("#captions"), (v) => state.captions = v);
segmented($("#quality"), (v) => { state.quality = v; updateEstimate(); });
function setPreviewAspect() {
  const map = { "9:16": "9/16", "4:5": "4/5", "1:1": "1/1", "16:9": "16/9" };
  const a = current();
  let ar = map[state.aspect];
  if (!ar && a?.base) ar = `${a.base.width}/${a.base.height}`;
  $("#preview-frame").style.aspectRatio = ar || "9/16";
}

// ---------------------------------------------------------------- estimate & render
function speechSeconds() {
  if (state.voiceMode === "upload") {
    const a = $("#audio-preview");
    return a.duration && isFinite(a.duration) ? a.duration : 10;
  }
  return Math.max(3, wordsOf($("#script").value).length / WPS);
}
let estTimer;
function updateEstimate() {
  clearTimeout(estTimer);
  estTimer = setTimeout(async () => {
    const a = current();
    setPreviewAspect();
    if (!state.status) return;
    if (!state.status.models.wav2lip.ready) { $("#estimate").innerHTML = "Download the AI models first (Settings)"; return; }
    if (!a) { $("#estimate").textContent = state.avatars.length ? "Pick a ready avatar" : "Create your first avatar to start"; return; }
    const secs = Math.min(speechSeconds(), maxSeconds());
    try {
      const { seconds } = await api(`/api/estimate?seconds=${secs}&quality=${state.quality}`);
      const extra = state.voiceMode === "clone" || $("#convert-voice").checked ? 120 : 0;
      $("#estimate").innerHTML = `~${secs.toFixed(0)} s video · renders in about <b>${fmtTime(seconds + extra)}</b> on CPU`;
    } catch (_) {}
  }, 150);
}
$("#convert-voice").onchange = updateEstimate;

$("#btn-render").onclick = async () => {
  const a = current();
  if (!a) return toast("Pick an avatar", true);
  const script = $("#script").value.trim();
  const fd = new FormData();
  const params = {
    avatar_id: a.id, script, voice_mode: state.voiceMode,
    tts_voice: $("#tts-voice").value, tts_rate: +$("#tts-rate").value, tts_pitch: +$("#tts-pitch").value,
    clone_language: $("#clone-lang").value, convert_voice: $("#convert-voice").checked && state.voiceMode !== "clone",
    studio_audio: $("#studio-audio").checked, aspect: state.aspect, caption_style: state.captions,
    quality: state.quality, film_finish: $("#film-finish").checked,
  };
  if (state.voiceMode !== "upload" && !script) return toast("Write a script first", true);
  if (state.voiceMode === "upload") {
    const f = $("#audio-file").files[0];
    if (f) fd.append("audio", f);
    else if (state.recordedAudio) fd.append("audio", state.recordedAudio, "recording.webm");
    else return toast("Upload or record your voice first", true);
  }
  if (wordsOf(script).length / WPS > maxSeconds() + 1 && state.voiceMode !== "upload")
    toast(`Heads up: the script is longer than ${maxSeconds()} s and will be cut. Trim it for a clean ending.`);
  fd.append("data", JSON.stringify(params));

  const btn = $("#btn-render");
  btn.disabled = true;
  $("#btn-download").classList.add("hidden");
  $("#result-video").pause();
  $("#result-video").classList.add("hidden");
  $("#preview-empty").classList.remove("hidden");
  setPreviewAspect();
  $("#render-progress").classList.remove("hidden");
  $("#rp-bar").style.width = "0%";
  try {
    const job = await api("/api/render", { method: "POST", body: fd });
    state.renderJob = job.id;
    const done = await pollJob(job.id, (j) => {
      $("#rp-stage").textContent = j.status === "queued" ? "Waiting for the previous render…" : j.stage;
      $("#rp-pct").textContent = Math.round(j.progress * 100) + "%";
      $("#rp-bar").style.width = j.progress * 100 + "%";
      $("#rp-time").textContent = j.status === "running" ? `Elapsed ${fmtTime(j.elapsed)}${j.eta ? ` · about ${fmtTime(j.eta)} left` : ""}` : "";
    });
    if (done.status === "error") throw new Error(done.error);
    const v = done.result;
    const vid = $("#result-video");
    vid.src = `/media/videos/${v.id}/video.mp4`;
    vid.classList.remove("hidden");
    $("#preview-empty").classList.add("hidden");
    $("#preview-frame").style.aspectRatio = `${v.width}/${v.height}`;
    vid.play().catch(() => {});
    const dl = $("#btn-download");
    dl.href = `/media/videos/${v.id}/video.mp4?download=1`;
    dl.classList.remove("hidden");
    toast(`Done in ${fmtTime(v.render_seconds)}!`);
  } catch (e) {
    toast(e.message, true);
  } finally {
    state.renderJob = null;
    $("#render-progress").classList.add("hidden");
    btn.disabled = false;
  }
};

// ---------------------------------------------------------------- library
async function loadVideos() {
  const vids = await api("/api/videos");
  const grid = $("#video-grid");
  if (!vids.length) {
    grid.innerHTML = `<div class="empty"><b>Nothing here yet</b>Your rendered videos will show up here.<br><button class="btn primary" onclick="show('create')">Create a video</button></div>`;
    return;
  }
  grid.innerHTML = vids.map((v) => `
    <div class="card vid-card">
      <div class="vwrap" style="aspect-ratio:${v.width}/${v.height}"><video src="/media/videos/${v.id}/video.mp4" poster="/media/videos/${v.id}/thumb.jpg" preload="none" controls playsinline></video></div>
      <div class="body">
        <div class="meta"><b>${esc(v.avatar_name)}</b> · ${v.duration.toFixed(1)} s · ${esc(v.aspect)} · ${v.quality === "studio" ? "Studio" : "Fast"}</div>
        <div class="script">${esc(v.script || "(voice upload)")}</div>
        <div class="meta">${new Date(v.created * 1000).toLocaleString()} · rendered in ${fmtTime(v.render_seconds)}</div>
        <div class="actions">
          <a class="btn" href="/media/videos/${v.id}/video.mp4?download=1">Download</a>
          <button class="btn ghost" data-copy="${v.id}">Copy script</button>
          <button class="btn ghost danger" data-del="${v.id}" title="Delete"><svg viewBox="0 0 24 24"><path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/></svg></button>
        </div>
      </div>
    </div>`).join("");
  $$("[data-copy]", grid).forEach((b) => b.onclick = () => {
    const v = vids.find((x) => x.id === b.dataset.copy);
    navigator.clipboard.writeText(v.script || "").then(() => toast("Script copied"), () => {});
  });
  $$("[data-del]", grid).forEach((b) => b.onclick = async () => {
    if (!confirm("Delete this video?")) return;
    await api(`/api/videos/${b.dataset.del}`, { method: "DELETE" });
    loadVideos();
  });
}
window.show = show;

// ---------------------------------------------------------------- boot
(async function boot() {
  const saved = safeGet("as.script");
  if (saved) $("#script").value = saved;
  try { await loadStatus(); } catch (e) { toast("Cannot reach the Avatar Studio server. Is it running?", true); }
  await loadAvatars();
  loadVoices();
  refreshQueue();
})();
