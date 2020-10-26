pyinstaller -F -w -n CommTest main.py gui/window.py comm.py packet.py hexdump.py
cp main.csv ./dist/CommTest.csv
