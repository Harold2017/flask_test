#!/usr/bin/env bash
for f in *.py
do echo "$f" nosetests "$f" --with-html --html-file="$f".html
done