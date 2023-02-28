#!/bin/sh

set -e

# change to script's parent directory
cd "$(dirname "$0")/.."

nix-shell -p pandoc --run "pandoc -s userscript/index.md -o userscript/index.html"
