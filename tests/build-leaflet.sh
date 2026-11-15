#!/bin/sh
# Construit une VRAIE carte Leaflet 1.9.4 pour les tests (tests/e2e_realmap.py) : /tmp/lf (source) → /tmp/leaflet-real.js
set -e
[ -d /tmp/lf ] || git clone -q --depth 1 --branch v1.9.4 https://github.com/Leaflet/Leaflet /tmp/lf
printf 'import * as L from "/tmp/lf/src/Leaflet.js";\nwindow.L = Object.assign({}, L);\n' > /tmp/lfentry.js
bun build /tmp/lfentry.js --outfile /tmp/leaflet-real.js --format iife --minify
