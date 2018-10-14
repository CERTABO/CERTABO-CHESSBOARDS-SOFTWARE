rmdir /s /q dist
rmdir /s /q build

pyinstaller -y run.py
pyinstaller -y usbtool.py

mkdir dist\result

xcopy /s /e /h /y dist\run dist\result
xcopy /s /e /h /y dist\usbtool dist\result\

copy stockfish.exe dist\result\
copy screen.ini dist\result\

mkdir dist\result\pics
xcopy /s /e /h /y pics dist\result\pics
mkdir dist\result\sprites_1380
xcopy /s /e /h /y sprites_1380 dist\result\sprites_1380
mkdir dist\result\sprites_1920
xcopy /s /e /h /y sprites_1920 dist\result\sprites_1920
mkdir dist\result\fonts
xcopy /s /e /h /y fonts dist\result\fonts
mkdir dist\result\engines
xcopy /s /e /h /y engines dist\result\engines