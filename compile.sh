#!/bin/sh
rm -rf dist
rm -rf build

pyinstaller -y run.py
pyinstaller -y usbtool.py

mkdir dist/result

cp dist/run/* dist/result/
cp dist/usbtool/* dist/result/

cp -r pics dist/result/
cp -r sprites_1380 dist/result/
cp -r sprites_1920 dist/result/
cp -r fonts dist/result/
cp -r engines dist/result/