
/* ===================== Wiring ===================== */
["create", "edit", "export"].forEach(n => $("tab-" + n).onclick = () => setTab(n));
document.querySelector(".tabs").addEventListener("keydown", e => {
  if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
  const order = ["create", "edit", "export"], i = order.indexOf(curTab), j = (i + (e.key === "ArrowRight" ? 1 : 2)) % 3;
  setTab(order[j]); $("tab-" + order[j]).focus();
});
$("playBtn").onclick = togglePlay;
$("prevBtn").onclick = () => stepFrame(-1);
$("nextBtn").onclick = () => stepFrame(1);
$("scrub").oninput = e => seek(e.target.value / 1000);
$("undoBtn").onclick = undo; $("redoBtn").onclick = redo;
["aspect", "dur", "fps"].forEach(id => $(id).onchange = () => { layoutView(); renderVarTiles(); buildStrip(); scheduleSeam(); updateFmtNote(); $("result").hidden = true; });
$("xSize").onchange = () => { layoutView(); updateFmtNote(); };
["xColors", "xDither", "xCap", "xRepeat", "xOptimize", "xBoomerang", "xBlur", "vFormat", "vLength"].forEach(id => $(id).onchange = updateFmtNote);
$("xTransparent").onchange = () => { $("matteRow").hidden = !(fmt === "gif" && $("xTransparent").checked); $("xOptimize").disabled = $("xBlur").disabled = $("xTransparent").checked; updateFmtNote(); };
$("fmtSeg").querySelectorAll("button").forEach(b => b.onclick = () => setFmt(b.dataset.fmt));
$("renderBtn").onclick = doExport;
$("cancelBtn").onclick = () => { exportCancel = true; };
$("saveBtn").onclick = () => lastOut && saveOut(lastOut.blob, lastOut.name);
$("remixBtn").onclick = () => { setVariants(remixSet(normSpec(clone(spec)), (Date.now() & 0xfffff) + 7), ["Current", "Bolder", "Minimal", "Twist"]); };
$("goBtn").onclick = () => generate(false);
$("stopBtn").onclick = () => genCtl && genCtl.abort();
$("surpriseBtn").onclick = () => { $("prompt").value = SURPRISES[Math.floor(Math.random() * SURPRISES.length)]; updateCount(); generate(true); };
$("director").onchange = setBadge;
const updateCount = () => { $("promptCount").textContent = `${$("prompt").value.length} / 600`; };
$("prompt").addEventListener("input", updateCount);
$("prompt").addEventListener("keydown", e => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)){ e.preventDefault(); generate(false); } });
$("refineBtn").onclick = refine;
$("refineStop").onclick = () => refCtl && refCtl.abort();
$("refineIn").addEventListener("keydown", e => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)){ e.preventDefault(); refine(); } });
QUICK.forEach(q => { const b = document.createElement("button"); b.type = "button"; b.className = "chip"; b.textContent = q; b.onclick = () => { $("refineIn").value = q.toLowerCase(); refine(); }; $("quickRefine").appendChild(b); });
["capTop", "capBot"].forEach(id => { $(id).addEventListener("input", () => applyCaptions(false)); $(id).addEventListener("change", () => applyCaptions(true)); });
["capStyle", "capMotion"].forEach(id => $(id).onchange = () => applyCaptions(true));
const addSel = $("addLayer");
Object.entries(KINDS).forEach(([k, v]) => { const o = document.createElement("option"); o.value = k; o.textContent = v.label; addSel.appendChild(o); });
addSel.onchange = () => { if (addSel.value){ addLayer(addSel.value); addSel.value = ""; } };
$("fileIn").onchange = e => { addPhotos(e.target.files); e.target.value = ""; };
/* drag & drop + paste */
let dragDepth = 0;
document.addEventListener("dragenter", e => { if ([...(e.dataTransfer?.types || [])].includes("Files")){ dragDepth++; $("dropOverlay").hidden = false; } });
document.addEventListener("dragleave", () => { dragDepth = Math.max(0, dragDepth - 1); if (!dragDepth) $("dropOverlay").hidden = true; });
document.addEventListener("dragover", e => { if ([...(e.dataTransfer?.types || [])].includes("Files")) e.preventDefault(); });
document.addEventListener("drop", e => {
  dragDepth = 0; $("dropOverlay").hidden = true;
  const files = e.dataTransfer?.files; if (!files || !files.length) return; e.preventDefault();
  const json = [...files].find(f => /json/.test(f.type) || /\.json$/i.test(f.name));
  if (json) loadRecipeFile(json); else { addPhotos(files); setTab("create"); }
});
document.addEventListener("paste", e => { const files = [...(e.clipboardData?.files || [])].filter(f => /^image\//.test(f.type)); if (files.length){ e.preventDefault(); addPhotos(files); } });
/* recipes */
async function loadRecipeFile(file){
  const note = $("recipeNote");
  try { const data = JSON.parse(await file.text()); const sp = normSpec(data.spec || data); setSpec(sp); note.className = "note ok"; note.textContent = `Opened “${sp.title}”.`; }
  catch { note.className = "note warn"; note.textContent = "That file isn't a Loopsmith recipe. Choose a .json file saved from here."; }
}
$("loadRecipe").onchange = e => { const f = e.target.files[0]; if (f) loadRecipeFile(f); e.target.value = ""; };
$("saveRecipe").onclick = () => { const c = cfg(); saveOut(new Blob([JSON.stringify({ app: "loopsmith", version: 2, canvas: { aspect: c.aspect, fps: c.fps, dur: c.dur }, spec }, null, 2)], { type: "application/json" }), slug() + ".json", $("recipeNote")); };
$("copyRecipe").onclick = async () => {
  const note = $("recipeNote"), txt = JSON.stringify(spec, null, 2);
  try { await navigator.clipboard.writeText(txt); note.className = "note ok"; note.textContent = "Recipe copied."; }
  catch { const d = $("json").closest("details"); d.open = true; $("json").textContent = txt; const r = document.createRange(); r.selectNodeContents($("json")); const s = getSelection(); s.removeAllRanges(); s.addRange(r); note.className = "note"; note.textContent = "Copying isn't allowed here, so the JSON is selected below. Press Ctrl+C or ⌘C."; }
};
/* keyboard */
document.addEventListener("keydown", e => {
  const tag = (e.target.tagName || "").toLowerCase(), typing = tag === "input" || tag === "textarea" || tag === "select" || e.target.isContentEditable;
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z" && !typing){ e.preventDefault(); if (e.shiftKey) redo(); else undo(); return; }
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "y" && !typing){ e.preventDefault(); redo(); return; }
  if (typing || e.target.closest?.("button,[role=option],canvas[role=button]")) return;
  if (e.key === " "){ e.preventDefault(); togglePlay(); }
  else if (e.key === "ArrowLeft"){ e.preventDefault(); stepFrame(-1); }
  else if (e.key === "ArrowRight"){ e.preventDefault(); stepFrame(1); }
});
new ResizeObserver(() => layoutView()).observe($("stage"));
window.addEventListener("resize", layoutView);

/* ===================== Boot ===================== */
(function boot(){
  let restored = false;
  try {
    const saved = JSON.parse(lsGet(K_CUR) || "null");
    if (saved && saved.spec && Array.isArray(saved.spec.layers)){
      const sp = normSpec(saved.spec);
      sp.layers = sp.layers.filter(l => !((l.kind === "image" && !IMAGES.has(l.src)) || (l.kind === "slides")));
      if (sp.layers.length > 1){ spec = normSpec(sp); restored = true; if (typeof saved.prompt === "string") $("prompt").value = saved.prompt.slice(0, 600); }
    }
  } catch {}
  if (!restored) spec = tplSpec(TEMPLATES.findIndex(t => t[1] === "Love pulse"));
  selId = defaultSel(); pushHist();
  const tab = lsGet(K_TAB); setTab(["create", "edit", "export"].includes(tab) ? tab : "create");
  updateCount(); renderStyles(); renderTplCats(); renderTpls(); renderTakes(); detectVideo(); setFmt("gif");
  setVariants(remixSet(spec, 4242), [restored ? "Current" : "Sample", "Bolder", "Minimal", "Twist"]);
  layoutView(); afterSpec(true); setPlayBtn();
  if (restored) status("Welcome back. Your last scene is restored.", "ok");
  requestAnimationFrame(tick);
  if (document.fonts && document.fonts.load){
    Promise.all(FONT_LOADS.map(f => document.fonts.load(f).catch(() => null))).then(() => { dirty = true; buildStrip(); renderVarTiles(); renderTpls(); renderTakes(); scheduleSeam(); });
  }
  setBadge();
  if (window.claude && typeof window.claude.use === "function"){
    window.claude.use("sample").then(async s => { sample = s; if (s){ $("director").value = "claude"; try { const lim = await s.limits(); sampleImages = lim && lim.images ? lim.images : null; } catch { sampleImages = null; } } setBadge(); }).catch(() => setBadge());
    window.claude.use("downloads").then(d => { downloads = d; }).catch(() => {});
  }
})();
