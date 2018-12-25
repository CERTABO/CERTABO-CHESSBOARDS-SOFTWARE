#!/bin/sh
rm -rf dist
rm -rf build

pyinstaller -y run.py
pyinstaller -y usbtool.py

mkdir dist/result

cp -r dist/run/* dist/result/
cp -r dist/usbtool/* dist/result/

cp screen.ini dist/result/
cp /usr/lib/python2.7/_sysconfigdata.py dist/result
cp run.sh dist/result
chmod +x dist/result/run.sh

cp -r pics dist/result/
cp -r sprites dist/result/
cp -r sprites_1380 dist/result/
cp -r sprites_1920 dist/result/
cp -r fonts dist/result/
cp -r engines dist/result/
cp -r macosx/Certabo.app dist/result