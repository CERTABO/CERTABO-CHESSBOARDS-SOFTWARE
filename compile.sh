#!/bin/sh
rm -rf dist
rm -rf build

pyinstaller -y run.py
pyinstaller -y usbtool.py

mkdir dist/result

cp -r dist/run/* dist/result/
cp -r dist/usbtool/* dist/result/

cp screen.ini dist/result/
cp -r pics dist/result/
cp -r sprites_1380 dist/result/
cp -r sprites_1920 dist/result/
cp -r fonts dist/result/
cp -r engines dist/result/