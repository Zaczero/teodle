#!/usr/bin/env bash

set -e

# change to script's parent directory
cd "$(dirname "$0")/.."

# for each file in find output
while read -r file; do

    # get short file hash
    hash=$(sha1sum "$file" | cut -c1-8)

    # skip if filename already contains hash
    if [[ $file == *".$hash."* ]]; then
        continue
    fi

    # insert hash before extension
    hash_file="${file%.*}.$hash.${file##*.}"

    # copy file to hash file
    if [ ! -f "$hash_file" ]; then
        echo "[Hash] $file -> $hash_file"
        cp "$file" "$hash_file"
    fi

done < <(find ./userscript/hash \
    -type f \
    -not -name '.*')

# error if .user.js contains beta and is not commented
if grep -q 'beta' ./userscript/teodle.user.js && ! grep -q ' //.*beta' ./userscript/teodle.user.js; then
    echo "Error: Userscript looks like a beta version"
    exit 1
fi

# copy newer files to destination
rsync \
    --verbose \
    --archive \
    --update \
    --checksum \
    --exclude '__pycache__' \
    ./userscript/ server:/var/www/teodle.monicz.dev/
