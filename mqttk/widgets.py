import tkinter as tk
from tkinter.colorchooser import askcolor
import tkinter.ttk as ttk
import platform
import sys


class SubscriptionFrame(ttk.Frame):
    def __init__(self, container, topic, unsubscribe_callback, colour, on_colour_change, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.container = container
        self.topic = topic
        self.colour = colour
        self.unsubscribe_callback = unsubscribe_callback
        self.on_colour_change_callback = on_colour_change
        self["relief"] = "groove"
        self["borderwidth"] = 2

        self.topic_frame = ttk.Frame(self)
        self.topic_frame.pack(side=tk.TOP, expand=1, fill='x')
        self.topic_label = ttk.Label(self.topic_frame)
        self.topic_label["text"] = topic
        self.topic_label.pack(side=tk.LEFT, fill="x", expand=1, padx=2, pady=2)

        self.options_frame = ttk.Frame(self)
        self.options_frame.pack(side=tk.BOTTOM, expand=1, fill='x')
        self.unsubscribe_button = ttk.Button(self.options_frame, text="Unsubscribe")
        self.unsubscribe_button.pack(side=tk.RIGHT, padx=2, pady=2)
        self.unsubscribe_button["command"] = self.on_unsubscribe

        self.colour_picker = ttk.Label(self.options_frame, width=2, background=colour)
        self.colour_picker.bind("<Button-1>", self.on_colour_change)
        self.colour_picker.pack(side=tk.LEFT)

    def on_unsubscribe(self):
        if self.unsubscribe_callback is not None:
            self.unsubscribe_callback(self.topic)
        self.pack_forget()
        self.destroy()

    def on_colour_change(self, *args, **kwargs):
        colors = askcolor(title="Pick a colour")
        if colors is not None:
            self.colour = colors[1]
            self.colour_picker.configure(background=self.colour)
            self.on_colour_change_callback()


class ConnectionFrame(ttk.Frame):
    def __init__(self, container, connection_name, on_select_callback=None, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.container = container
        self.connection_name = connection_name
        self.on_select_callback = on_select_callback
        self["relief"] = "groove"
        self["borderwidth"] = 2
        self.connection = ttk.Label(self)
        self.connection["text"] = connection_name
        self.connection.pack(fill=tk.X, expand=1)
        self.bind("<Button-1>", self.on_click)
        self.connection.bind("<Button-1>", self.on_click)

    def on_click(self, event):
        if self.on_select_callback is not None:
            self.configure(style="Selected.TFrame")
            self.connection.configure(style="Selected.TLabel")
            self.on_select_callback(self.connection_name)

    def on_unselect(self):
        self.configure(style="TFrame")
        self.connection.configure(style="TLabel")
        self.update()


class ScrollFrame(tk.Frame):
    """
    Borrowed from Mark Pointing
    https://gist.github.com/mp035/9f2027c3ef9172264532fcd6262f3b01
    https://github.com/mp035
    """
    def __init__(self, parent):
        super().__init__(parent)

        self.canvas = tk.Canvas(self, borderwidth=0, background="#ffffff")
        self.viewPort = tk.Frame(self.canvas,
                                 background="#ffffff")
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas_window = self.canvas.create_window((4, 4), window=self.viewPort, anchor="nw",
                                                       tags="self.viewPort")
        self.viewPort.bind("<Configure>",
                           self.onFrameConfigure)
        self.canvas.bind("<Configure>",
                         self.onCanvasConfigure)
        self.viewPort.bind('<Enter>', self.onEnter)
        self.viewPort.bind('<Leave>', self.onLeave)
        self.onFrameConfigure(None)

    def onFrameConfigure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def onCanvasConfigure(self, event):
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

    def onMouseWheel(self, event):
        if platform.system() == 'Windows':
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif platform.system() == 'Darwin':
            self.canvas.yview_scroll(int(-1 * event.delta), "units")
        else:
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")

    def onEnter(self, event):
        if platform.system() == 'Linux':
            self.canvas.bind_all("<Button-4>", self.onMouseWheel)
            self.canvas.bind_all("<Button-5>", self.onMouseWheel)
        else:
            self.canvas.bind_all("<MouseWheel>", self.onMouseWheel)

    def onLeave(self, event):
        if platform.system() == 'Linux':
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")
        else:
            self.canvas.unbind_all("<MouseWheel>")

    def to_bottom(self):
        self.canvas.yview_moveto(1.0)
