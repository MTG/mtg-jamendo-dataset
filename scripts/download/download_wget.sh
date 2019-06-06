#!/usr/bin/env bash
wget -r -np -nH -c --cut-dirs=2 -R index.html* $1 -P $2
