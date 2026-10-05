#!/usr/bin/env bash
# Download the raw 1K renders listed in textures.json into raw/.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p raw
python3 -c 'import json;[print(k,v["url"]) for k,v in json.load(open("textures.json")).items()]' |
while read -r name url; do curl -sSfL -o "raw/$name.png" "$url" && echo "ok $name"; done
