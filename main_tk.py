# how to make env (tested in python 3.6.9)
# $ sudo apt-get install python-tk
# $ python -m venv venv
# $ ./venv/bin/python -m pip install -r requirements.txt
# $ ./venv/bin/python -m pip install pyinstaller
# how to make exe
# $ ./venv/bin/pyuic5 gui/window.ui -o gui/window.py
# $ ./venv/bin/python -m PyInstaller -F -w -n CommTest main_tk.py comm.py packet.py hexdump.py
# $ cp main_tk.csv ./dis/CommTest.csv
# $ ./dist/CommTest

import csv
import os
import sys
import threading
import tkinter as tk
import tkinter.ttk as ttk
import datetime
from tkinter import messagebox

import hexdump
from comm import *
from packet import PacketBuilder

_ENCODING = 'euc-kr'


class App(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack(fill=tk.BOTH, expand=True)
        self.create_widgets_1st()
        self.create_widgets_2nd()
        self.create_widgets_3rd()
        self.master.bind_class("Text", "<Control-a>", self.on_select_all_text)
        self.master.bind_class("Entry", "<Control-a>", self.on_select_all_entry)

        self.comm = None
        self.comm_thread_running = False
        self.comm_thread = None
        self.preset = {}
        self.has_log = 0

        self.on_reload_btn_clicked()

    def create_widgets_1st(self):
        frame = tk.Frame(self)
        frame.pack(fill=tk.X)

        self.port_label = tk.Label(frame, text="PORT:")
        self.port_label.pack(side=tk.LEFT)

        self.port_cb = ttk.Combobox(frame)
        self.port_cb.pack(side=tk.LEFT)

        self.speed_label = tk.Label(frame, text="SPEED:")
        self.speed_label.pack(side=tk.LEFT)

        self.speed_cb = ttk.Combobox(frame, state="readonly")
        self.speed_cb.pack(side=tk.LEFT)

        self.open_btn = tk.Button(frame, text="OPEN", underline=0, command=self.on_open_btn_clicked)
        self.master.bind('<Alt-o>', self.on_open_btn_clicked)
        self.open_btn.pack(side=tk.LEFT)

        self.clear_btn = tk.Button(frame, text="CLEAR", underline=1, command=self.on_clear_btn_clicked)
        self.master.bind('<Alt-l>', self.on_clear_btn_clicked)
        self.clear_btn.pack(side=tk.RIGHT)

        self.reload_btn = tk.Button(frame, text="RELOAD", underline=0, command=self.on_reload_btn_clicked)
        self.master.bind('<Alt-r>', self.on_reload_btn_clicked)
        self.reload_btn.pack(side=tk.RIGHT)

    def create_widgets_2nd(self):
        frame = tk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True)

        frame_1 = tk.Frame(frame)
        frame_1.pack(side=tk.LEFT, fill=tk.Y)

        self.preset_lb = tk.Listbox(frame_1)
        self.preset_lb.bind('<<ListboxSelect>>', self.on_preset_lb_selected)
        self.preset_lb.pack(side=tk.LEFT, fill=tk.BOTH)

        self.preset_lb_scroll = tk.Scrollbar(frame_1)
        self.preset_lb_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.preset_lb.config(yscrollcommand=self.preset_lb_scroll.set)
        self.preset_lb_scroll.config(command=self.preset_lb.yview)

        frame_2 = tk.Frame(frame)
        frame_2.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        frame_1_1 = tk.Frame(frame_2)
        frame_1_1.pack(side=tk.TOP, fill=tk.X)

        self.caption_ed = tk.Entry(frame_1_1)
        self.caption_ed.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.send_btn = tk.Button(frame_1_1, text="SEND", underline=0, command=self.on_send_btn_clicked)
        self.master.bind('<Alt-s>', self.on_send_btn_clicked)
        self.send_btn.pack(side=tk.RIGHT)

        self.data_txt = tk.Text(frame_2, height=6)
        self.data_txt.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    def create_widgets_3rd(self):
        frame = tk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True)

        frame_1 = tk.Frame(frame)
        frame_1.pack(fill=tk.BOTH)

        self.log_lb = tk.Listbox(frame_1, height=6)
        self.log_lb.bind("<<ListboxSelect>>", self.on_log_lb_selected)
        self.log_lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.log_lb_scroll = tk.Scrollbar(frame_1)
        self.log_lb_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_lb.config(yscrollcommand=self.log_lb_scroll.set)
        self.log_lb_scroll.config(command=self.log_lb.yview)

        self.log_txt = tk.Text(frame, height=6)
        self.log_txt.pack(fill=tk.BOTH, expand=True)

        self.log_ed = tk.Entry(frame)
        self.log_ed.pack(fill=tk.X)

    def on_select_all_text(self, event=None):
        event.widget.tag_add(tk.SEL, '1.0', tk.END)

    def on_select_all_entry(self, event=None):
        event.widget.select_range(0, tk.END)

    def on_reload_btn_clicked(self, event=None):
        if self.comm:
            self.on_open_btn_clicked()

        self.init_port()
        self.init_speed()
        self.init_preset()

    def init_port(self):
        items = Comm.scan_ports()

        item = self.port_cb.get()
        if len(item) == 0 and len(items) > 0:
            item = items[0]

        self.port_cb.config(values=items)
        self.port_cb.set(item)

    def init_speed(self):
        items = ["9600", "19200", "38400", "57600", "115200"]

        item = self.speed_cb.get()
        if item not in items:
            item = "38400"

        self.speed_cb.config(values=items)
        self.speed_cb.set(item)

    def init_preset(self):
        self.preset = {}
        try:
            filename = os.path.splitext(sys.argv[0])[0] + '.csv'
            with open(filename, 'r', encoding=_ENCODING) as f:
                reader = csv.reader(f, skipinitialspace=True)
                for key, *val in reader:
                    self.preset[key] = val
        except Exception as ex:
            print(f'load_preset: {ex}')

        self.preset_lb.delete(0, tk.END)
        for key in self.preset:
            self.preset_lb.insert(tk.END, key)

    def on_clear_btn_clicked(self, event=None):
        self.log_lb.delete(0, tk.END)
        self.log_txt.delete("1.0", tk.END)
        self.log_ed.delete(0, tk.END)

    def on_preset_lb_selected(self, event=None):
        index = self.preset_lb.curselection()[0]
        key = self.preset_lb.get(index)

        self.caption_ed.delete(0, tk.END)
        self.caption_ed.insert(tk.END, key)

        self.data_txt.delete("1.0", tk.END)
        for val in self.preset[key]:
            self.data_txt.insert(tk.END, val + '\n')

    def on_send_btn_clicked(self, event=None):
        try:
            if self.comm:
                dat = self.data_txt.get("1.0", tk.END)
                dat = dat.replace("\n", "").encode(_ENCODING)
                dat = PacketBuilder().decode(dat).build()
                dat = Comm.build(dat)

                self.append_log(dat, ">>")
                self.scroll_log()

                self.comm.write(dat)
        except Exception as ex:
            messagebox.showerror("SEND", str(ex))

    def append_log(self, dat, sender):
        ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        dump = binascii.hexlify(dat).decode().upper()
        self.log_lb.insert(tk.END, f'[{ts}] {sender} {dump}')
        self.has_log = 1

    def scroll_log(self):
        if self.has_log:
            self.log_lb.yview(tk.END)
            self.has_log = 0

    def on_open_btn_clicked(self, event=None):
        if self.comm:
            self.comm_thread_running = False
            self.comm_thread.join()
            self.comm_thread = None

            self.comm.close()
            self.comm = None

            self.open_btn.config(text="OPEN", underline=0)
        else:
            try:
                print(self.port_cb.get(), self.speed_cb.get())
                self.comm = Comm(self.port_cb.get(), int(self.speed_cb.get()))
                self.comm.open()

                self.comm_thread_running = True
                self.comm_thread = threading.Thread(target=self.run_comm_thread, daemon=True)
                self.comm_thread.start()

                self.open_btn.config(text="CLOSE", underline=2)
            except Exception as ex:
                self.comm = None
                messagebox.showerror("OPEN", str(ex))

    def run_comm_thread(self):
        print("run_comm_thread: start")

        while self.comm_thread_running:
            try:
                dat = self.comm.read(1, True)
                self.append_log(dat, "<<")
            except CommTimeoutError as ex:
                self.scroll_log()
            except CommError as ex:
                self.append_log(ex.raw, "<" + str(ex)[0])
            except Exception as ex:
                print(f"run_comm_thread: {ex}")
                break

        print("run_comm_thread: stop")

    def on_log_lb_selected(self, event):
        index = self.log_lb.curselection()[0]
        log = self.log_lb.get(index)
        ts, sender, dump = log.split()

        dat = binascii.unhexlify(dump)
        hd = hexdump.hexdump(dat)
        sd = hexdump.strdump(dat, encoding=_ENCODING)

        self.log_txt.delete("1.0", tk.END)
        self.log_txt.insert(tk.END, f"{ts} {sender} {len(dat)} bytes\n{hd}")

        self.log_ed.delete(0, tk.END)
        self.log_ed.insert(tk.END, sd)


if __name__ == '__main__':
    root = tk.Tk()
    root.title(os.path.splitext(os.path.basename(sys.argv[0]))[0])
    app = App(root)
    app.mainloop()
