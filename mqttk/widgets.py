import tkinter as tk
from tkinter.colorchooser import askcolor
import tkinter.ttk as ttk
import platform
import sys


class SubscriptionFrame(ttk.Frame):
    def __init__(self, container, topic, unsubscribe_callback=None, style_id=None, colour_change_callback=None, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        #TODO
        # Add unique colour to each message:
        # - Colour picker added here
        # - Callback to main to change colour for this subscription group
        self.container = container
        self.colour_change_callback = colour_change_callback
        self.topic = topic
        self.unsubscribe_callback = unsubscribe_callback
        self.style_id = style_id
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

        self.color_picker = ttk.Label(self.options_frame, width=2, style=self.style_id)
        self.color_picker.bind("<Button-1>", self.on_colour_change)
        self.color_picker.pack(side=tk.LEFT)

    def on_unsubscribe(self):
        if self.unsubscribe_callback is not None:
            self.unsubscribe_callback(self.topic)
        self.pack_forget()
        self.destroy()

    def on_colour_change(self, *args, **kwargs):
        colors = askcolor(title="Pick a colour")
        if colors is not None:
            self.colour = colors[1]
            # self.color_picker.configure(bg=self.colour, fg=self.colour)
            if self.colour_change_callback is not None:
                print("Changing colour for", self.style_id, self.colour)
                self.colour_change_callback(self.style_id, self.colour)


class MessageFrame(ttk.Frame):
    def __init__(self, container, message_id, topic, timestamp, qos, retained, indicator_style,
                 on_select_callback=None, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.container = container
        self.message_id = message_id
        self.on_select_callback = on_select_callback
        self["relief"] = "groove"
        self["borderwidth"] = 1
        self.configure(style="New.TFrame")
        self.bind("<Button-1>", self.on_click)

        # self.color_frame = ttk.Frame(self, width=10, style=indicator_style)
        # self.color_frame.pack(side=tk.LEFT, fill='y')

        self.id_qos_label = ttk.Label(self, style=indicator_style, justify=tk.RIGHT)
        self.id_qos_label["text"] = "{}    ID: {} \nQoS: {}".format("RETAINED" if retained else "",
                                                                    message_id,
                                                                    qos)
        self.id_qos_label.pack(side=tk.RIGHT, pady=2, padx=2, fill='y')

        if sys.platform == "win32":
            font = "TkDefaultFont 10 bold"
        elif sys.platform == "darwin":
            font = "TkDefaultFont 12 bold"
        else:
            font = "TkDefaultFont"

        self.topic_label = ttk.Label(self, text=topic, style="New.TLabel", anchor='w', font=font)
        self.topic_label.bind("<Button-1>", self.on_click)
        self.topic_label.pack(side=tk.TOP, expand=1, fill="x", padx=4, pady=2)
        self.date_label = ttk.Label(self,
                                    text=timestamp,
                                    style="New.TLabel")
        self.date_label.bind("<Button-1>", self.on_click)
        self.date_label.pack(side=tk.BOTTOM, expand=1, fill="x", padx=4, pady=2)

    def on_click(self, event):
        if self.on_select_callback is not None:
            self.topic_label.configure(style="Selected.TLabel")
            self.date_label.configure(style="Selected.TLabel")
            # self.id_qos_label.configure(style="Selected.TLabel")
            self.on_select_callback(self.message_id)
            self.configure(style="Selected.TFrame")

    def on_unselect(self):
        self.configure(style="TLabel")
        self.topic_label.configure(style="TLabel")
        self.date_label.configure(style="TLabel")
        # self.id_qos_label.configure(style="TLabel")
        self.configure(style="TFrame")
        self.update()


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
