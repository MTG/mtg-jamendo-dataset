#!/usr/bin/env bash
cd $1
for i in *.tar
do
    tar -xvf $i && rm $i
done
cd -
