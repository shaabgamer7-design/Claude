#!/usr/bin/env bash
# Wrap dist/FreeFlow.app in a drag-to-Applications disk image.
set -euo pipefail

version="$(python -c 'import freeflow; print(freeflow.__version__)')"
arch="$(uname -m)"
stage="$(mktemp -d)"
cp -R dist/FreeFlow.app "$stage/"
ln -s /Applications "$stage/Applications"
out="dist/FreeFlow-${version}-macOS-${arch}.dmg"
rm -f "$out"
hdiutil create -volname "FreeFlow" -srcfolder "$stage" -ov -format UDZO "$out"
rm -rf "$stage"
echo "built $out"
