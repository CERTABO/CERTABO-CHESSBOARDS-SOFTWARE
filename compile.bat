pyinstaller -y run.py
copy usb.py usb2.py
pyinstaller -y usb2.py
del usb2.py
pyinstaller -y move.py

mkdir dist\result

xcopy /s /e /h /y dist\run dist\result
xcopy /s /e /h /y dist\usb2 dist\result\
move dist\result\usb2.exe dist\result\usb.exe
xcopy /s /e /h /y dist\move dist\result\

copy stockfish.exe dist\result\
copy calibration.bin dist\result\
copy bestmove.p dist\result\
copy move_history_tmp.p dist\result
copy screen.ini dist\result\

mkdir dist\result\pics
xcopy /s /e /h /y pics dist\result\pics
mkdir dist\result\sprites_1380
xcopy /s /e /h /y sprites_1380 dist\result\sprites_1380
mkdir dist\result\sprites_1920
xcopy /s /e /h /y sprites_1920 dist\result\sprites_1920
mkdir dist\result\fonts
xcopy /s /e /h /y fonts dist\result\fonts