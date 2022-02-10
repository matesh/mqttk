import tkinter as tk
import tkinter.ttk as ttk
from mqttk.widgets.scrolled_text import CustomScrolledText


class LogTab(ttk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master=master, *args, **kwargs)

        self.log_output = CustomScrolledText(self, font="Courier 14", exportselection=False, state='disabled',
                                             background="white", foreground="black")
        self.log_output.pack(fill='both', expand=1, padx=3, pady=3)

    def add_message(self, message):
        self.log_output.configure(state="normal")
        self.log_output.insert(tk.END, message)
        self.log_output.configure(state="disabled")
