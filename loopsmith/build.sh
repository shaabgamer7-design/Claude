#!/usr/bin/env bash
# Assembles loopsmith/index.html from the parts in src/ and syntax-checks the script.
set -euo pipefail
cd "$(dirname "$0")/src"
js=(p3_core.js p4_render.js p5_model.js p6_content.js p7_encode.js p8_ui_a.js p9_ui_b.js p10_init.js)
{ echo '(() => {'; cat "${js[@]}"; echo '})();'; } > ../app.tmp.js
node --check ../app.tmp.js
{ cat p1_head.html p2_body.html; echo '<script>'; cat ../app.tmp.js; echo '</script>'; } > ../index.html
rm ../app.tmp.js
echo "Built loopsmith/index.html"
