// Shared helpers: a phone-sized persistent browser (keeps its HTTP cache between
// runs) whose requests to wisharo.com go out one at a time with a gap, so a
// filming session stays under the site's rate limit. Requests are made by the
// browser itself (route.continue), unchanged.
const {chromium} = require("playwright");
const path = require("path");

const GAP_MS = Number(process.env.GAP_MS || 450);

async function launch({dsf = 1, profile = "phone-profile"} = {}) {
  const ctx = await chromium.launchPersistentContext(path.join(__dirname, "..", ".cache", profile), {
    viewport: {width: 390, height: 844},
    deviceScaleFactor: dsf,
    isMobile: true,
    hasTouch: true,
  });
  let chain = Promise.resolve();
  let last = 0;
  await ctx.route(
    (u) => u.hostname.endsWith("wisharo.com"),
    (route) => {
      chain = chain.then(async () => {
        const wait = last + GAP_MS - Date.now();
        if (wait > 0) await new Promise((r) => setTimeout(r, wait));
        last = Date.now();
        await route.continue().catch(() => {});
      });
    },
  );
  const page = ctx.pages()[0] || (await ctx.newPage());
  const bad = [];
  page.on("response", (r) => r.status() >= 400 && bad.push(`${r.status()} ${r.url()}`));
  return {ctx, page, bad};
}

const HIDE_CSS = `#wpadminbar{display:none!important} html{margin-top:0!important}`;
module.exports = {launch, HIDE_CSS};
