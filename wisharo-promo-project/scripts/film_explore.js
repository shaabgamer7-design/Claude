// Phase 1: walk the real Make card flow on wisharo.com at a phone viewport,
// screenshot every step and dump the clickable controls, so the recording
// script (phase 2) can target exact elements. Gentle: one page, few loads.
// Usage: node scripts/film_explore.js [outDir]
const {launch, HIDE_CSS} = require("./polite");
const fs = require("fs");
const path = require("path");

const OUT = process.argv[2] || path.join(__dirname, "..", "out", "explore");
fs.mkdirSync(OUT, {recursive: true});

(async () => {
  const {ctx, page, bad} = await launch();
  let n = 0;
  const shot = async (name) => page.screenshot({path: path.join(OUT, `${String(++n).padStart(2, "0")}_${name}.png`)});
  const controls = async (name) => {
    const list = await page.evaluate(() =>
      [...document.querySelectorAll("button,a,[role=button],[role=tab],.wds-tile,[data-id],[data-bg],[data-el]")]
        .filter((e) => e.offsetParent !== null)
        .slice(0, 400)
        .map((e) => {
          const r = e.getBoundingClientRect();
          return {tag: e.tagName, cls: e.className?.toString().slice(0, 80), id: e.id, txt: (e.innerText || e.getAttribute("aria-label") || e.title || "").trim().slice(0, 60),
            data: Object.fromEntries(Object.entries(e.dataset).slice(0, 4)), x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2), w: Math.round(r.width), h: Math.round(r.height)};
        }),
    );
    fs.writeFileSync(path.join(OUT, `${String(n).padStart(2, "0")}_${name}.json`), JSON.stringify({url: page.url(), list}, null, 1));
  };

  await page.goto("https://wisharo.com/tuesday-blessings/", {waitUntil: "networkidle", timeout: 90000});
  await page.addStyleTag({content: HIDE_CSS});
  await shot("tuesday_top");
  const btn = page.locator(".wds-card-btn").first();
  await btn.scrollIntoViewIfNeeded();
  await page.mouse.wheel(0, -250);
  await page.waitForTimeout(600);
  await shot("copy_cards");
  await controls("copy_cards");
  const href = await btn.getAttribute("href");
  console.log("Make card href:", href);
  await btn.tap();
  await page.waitForLoadState("networkidle", {timeout: 90000});
  await page.addStyleTag({content: HIDE_CSS});
  await page.waitForTimeout(2500);
  await shot("editor_open");
  await controls("editor_open");
  // scroll the editor page down in steps to reveal panels/toolbars
  for (let i = 0; i < 4; i++) {
    await page.mouse.wheel(0, 600);
    await page.waitForTimeout(500);
    await shot(`editor_scroll${i}`);
    await controls(`editor_scroll${i}`);
  }
  fs.writeFileSync(path.join(OUT, "errors.txt"), bad.join("\n"));
  console.log(`done: ${n} screenshots in ${OUT}; ${bad.length} HTTP errors`);
  await ctx.close();
})();
