#!/usr/bin/env bash
for i in *.tar
do
    tar -xvf $i && rm $i
done
