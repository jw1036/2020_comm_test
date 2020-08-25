# how to make env (tested in python 3.6.9)
# $ python -m venv venv
# $ ./venv/bin/python -m pip install -r requirements.txt
# $ ./venv/bin/python -m pip install pyinstaller
# how to make exe
# $ ./venv/bin/pyuic5 gui/window.ui -o gui/window.py
# $ ./venv/bin/python -m PyInstaller -F -w -n SerialTest main.py gui/window.py
# $ cp main.csv ./dis/SerialTest.csv
# $ ./dist/SerialTest

import binascii
import csv
import datetime
import os
import sys
import threading
from PyQt5 import uic
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox

from comm import Comm, CommError, CommTimeoutError
from packet import PacketBuilder
import hexdump

_ENCODING = "euc-kr"


class SerialTest(QMainWindow):
    def __init__(self):
        super().__init__()
        if os.path.exists("gui/window.ui"):
            self.ui = uic.loadUi("gui/window.ui", self)
        else:
            from gui.window import Ui_MainWindow
            self.ui = Ui_MainWindow()
            self.ui.setupUi(self)
        self.comm = None
        self.comm_thread_running = False
        self.comm_thread = None
        self.preset = {}
        self.has_log = 0
        self.on_btn_reload_clicked()

    def init_port(self):
        items = Comm.scan_ports()

        item = self.ui.cb_port.currentText()
        if len(item) == 0 and len(items) > 0:
            item = items[0]

        self.ui.cb_port.clear()
        self.ui.cb_port.addItems(items)
        self.ui.cb_port.setCurrentText(item)

    def init_speed(self):
        items = ["9600", "19200", "38400", "57600", "115200"]

        item = self.ui.cb_speed.currentText()
        if item not in items:
            item = "38400"

        self.ui.cb_speed.clear()
        self.ui.cb_speed.addItems(items)
        self.ui.cb_speed.setCurrentText(item)

    def init_preset(self):
        self.preset = {}
        try:
            filename = os.path.splitext(sys.argv[0])[0] + '.csv'
            with open(filename, 'r', encoding=_ENCODING) as f:
                reader = csv.reader(f, skipinitialspace=True)
                for key, *val in reader:
                    self.preset[key] = val
        except Exception as ex:
            print(f"init_preset: {ex}")

        self.ui.lst_preset.clear()
        self.ui.lst_preset.addItems(list(self.preset.keys()))

    @pyqtSlot()
    def on_btn_reload_clicked(self):
        if self.comm:
            self.on_btn_open_clicked()

        self.init_port()
        self.init_speed()
        self.init_preset()

    @pyqtSlot()
    def on_btn_clear_clicked(self):
        self.ui.lst_log.clear()
        self.ui.edt_log.clear()
        self.ui.txt_log.clear()

    @pyqtSlot()
    def on_lst_preset_itemSelectionChanged(self):
        key = self.ui.lst_preset.currentItem().text()
        self.ui.edt_caption.setText(key)
        self.ui.edt_dat.clear()
        for val in self.preset[key]:
            self.ui.edt_dat.append(val)

    @pyqtSlot()
    def on_btn_send_clicked(self):
        try:
            if self.comm:
                dat = self.ui.edt_dat.toPlainText().replace('\n', '').encode(_ENCODING)
                dat = PacketBuilder().decode(dat).build()
                dat = Comm.build(dat)

                self.append_log(dat, ">>")
                self.scroll_log()

                self.comm.write(dat)
        except Exception as ex:
            QMessageBox.warning(self, "SEND", str(ex))

    def append_log(self, dat, sender):
        ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        dump = binascii.hexlify(dat).decode().upper()
        self.ui.lst_log.addItem(f"[{ts}] {sender} {dump}")
        self.has_log = 1

    def scroll_log(self):
        if self.has_log:
            self.ui.lst_log.scrollToBottom()
            self.has_log = 0

    @pyqtSlot()
    def on_lst_log_itemSelectionChanged(self):
        log = self.ui.lst_log.currentItem().text()
        ts, sender, dump = log.split()
        dat = binascii.unhexlify(dump)
        hd = hexdump.hexdump(dat)
        sd = hexdump.strdump(dat, encoding=_ENCODING)
        self.ui.edt_log.setPlainText(f"{ts} {sender} {len(dat)} bytes\n{hd}")
        self.ui.txt_log.setText(sd)

    @pyqtSlot()
    def on_btn_open_clicked(self):
        if self.comm:
            self.comm_thread_running = False
            self.comm_thread.join()
            self.comm_thread = None

            self.comm.close()
            self.comm = None

            self.ui.btn_open.setText("&OPEN")
        else:
            try:
                self.comm = Comm(self.ui.cb_port.currentText(), int(self.ui.cb_speed.currentText()))
                self.comm.open()

                self.comm_thread_running = True
                self.comm_thread = threading.Thread(target=self.run_comm_thread, daemon=True)
                self.comm_thread.start()

                self.ui.btn_open.setText("CL&OSE")
            except Exception as ex:
                self.comm = None
                QMessageBox.warning(self, "OPEN", str(ex))

    def run_comm_thread(self):
        print("run_ser_thread: start")

        while self.comm_thread_running:
            try:
                dat = self.comm.read(1, True)
                self.append_log(dat, "<<")
            except CommTimeoutError as ex:
                self.scroll_log()
            except CommError as ex:
                self.append_log(ex.raw, "<" + str(ex)[0])
            except Exception as ex:
                print(f"run_ser_thread: {ex}")
                break

        print("run_ser_thread: stop")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SerialTest()
    window.show()
    sys.exit(app.exec())
