#!/bin/bash

# 0. ak existuje swos.zip, zmaze ho
if [ -f swos.zip ]; then
    rm swos.zip
fi

# 1. ak neexistuje slozka, vyrobi slozku swos_release
mkdir -p swos_release

# 2. skopiruje .py a .json subory z ./swos do slozky swos_release
cp ./custom_components/swos/*.py ./swos_release/
cp ./custom_components/swos/*.json ./swos_release/
cp ./custom_components/swos/*.png ./swos_release/

# 3. vyrobi swos.zip zo swos_release
cd swos_release || exit 1
zip -r ../swos.zip ./*
cd ..

# 4. smaze swos_release
rm -rf swos_release
