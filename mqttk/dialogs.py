from __init__ import __version__ as version
import tkinter as tk
import tkinter.ttk as ttk

about_text = "MQTTk is a lightweight MQTT client that intends to replace\nthe popular MQTT.fx tool because it is no longer free, the\nfree version is old and no longer maintained, it doesn't\nwork on M1 macs (crashes all the time) and when it works,\nit eats loads of RAM and consumes half of a CPU core just\nby idling. This software intends to keep the most useful\nfeatures of MQTT.fx and over time, extend it to make it\neven more useful.\nIt ain't pretty, but it's not made for a beauty contest."


class AboutDialog(tk.Toplevel):
    def __init__(self, master=None, icon=None):
        super().__init__(master=master)
        self.master = master
        self.title("About")
        width = 600
        height = 300
        screenwidth = self.winfo_screenwidth()
        screenheight = self.winfo_screenheight()
        alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        self.resizable(False, False)
        self.geometry(alignstr)

        self.about_frame = ttk.Frame(self)

        self.about_label = ttk.Label(self.about_frame, text="About MQTTk\n\nVersion {}".format(version), anchor='n', justify=tk.CENTER)
        self.about_label.pack(side=tk.TOP, fill='x', expand=1)

        self.about_content_frame = ttk.Frame(self.about_frame)
        # self.icon_canvas = tk.Canvas(self.about_content_frame, width=200, height=200)
        # self.icon_canvas.create_image(10, 10, anchor='w', image=icon)
        # self.icon_canvas.pack(side=tk.LEFT, expand=1, fill='both')
        self.icon = ttk.Label(self.about_content_frame, image=icon)
        self.icon.pack(side=tk.LEFT, expand=1, fill="both", padx=4)
        self.about_text = ttk.Label(self.about_content_frame, anchor='e', text=about_text, justify=tk.LEFT)
        self.about_text.pack(side=tk.TOP, fill='x', expand=1)
        self.about_text.pack(side=tk.RIGHT, expand=1, fill='x')
        self.protocol("WM_DELETE_WINDOW", self.on_destroy)
        self.about_content_frame.pack(expand=1, fill='x')

        self.ok_button = ttk.Button(self.about_frame, text="OK")
        self.ok_button.pack(side=tk.BOTTOM, pady=4)
        self.ok_button["command"] = self.on_destroy
        self.about_frame.pack(fill='both', expand=1)

    def on_destroy(self, *args, **kwargs):
        self.grab_release()
        self.destroy()
