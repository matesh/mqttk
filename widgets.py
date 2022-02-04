try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk

try:
    import ttk
    py3 = False
except ImportError:
    import tkinter.ttk as ttk
    py3 = True
from collections import  namedtuple
import platform


class MQTTMESSAGETEMPLATE:
    def __init__(self, topic, payload, qos):
        self.topic = topic
        self.payload = payload
        self.qos = qos


class SubscriptionFrame(ttk.Frame):
    def __init__(self, container, topic, unsubscribe_callback=None, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        #TODO
        # Add unique colour to each message:
        # - Colour picker added here
        # - Callback to main to change colour for this subscription group
        self.container = container
        self.topic = topic
        self.unsubscribe_callback = unsubscribe_callback
        self.unsubscribe_button = ttk.Button(self)
        self["relief"] = "groove"
        self["borderwidth"] = 2
        # self.unsubscribe_button.place(x=self.winfo_width()-80, y=(self.winfo_height()/2)-12, width=75, height=25)
        self.unsubscribe_button.place(relx=.5, rely=.5, relwidth=.49, relheight=.49)
        self.unsubscribe_button["text"] = "Unsubscribe"
        self.unsubscribe_button["command"] = self.on_unsubscribe
        self.topic_label = ttk.Label(self)
        self.topic_label["text"] = topic
        self.topic_label.place(x=3, y=3, relwidth=0.95, height=25)

    def on_unsubscribe(self):
        print("UNSUB", self.topic)
        if self.unsubscribe_callback is not None:
            self.unsubscribe_callback(self.topic)
        self.pack_forget()
        self.destroy()


class MessageFrame(ttk.Frame):
    def __init__(self, container, message_id, topic, timestamp, on_select_callback=None, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        #TODO
        # Add unique colour to each message:
        # - Add frame here (tk.frame prolly for simplicity)
        # - Get colour in args?
        self.container = container
        self.message_id = message_id
        self.topic = topic
        self.on_select_callback = on_select_callback
        self["relief"] = "groove"
        self["borderwidth"] = 2
        self.topic_label = ttk.Label(self)
        self.topic_label["text"] = topic
        self.topic_label.pack(fill=tk.X, expand=1)
        self.date_label = ttk.Label(self)
        self.date_label["text"] = timestamp
        self.date_label.pack(fill=tk.X, expand=1)
        self.bind("<Button-1>", self.on_click)
        self.topic_label.bind("<Button-1>", self.on_click)
        self.date_label.bind("<Button-1>", self.on_click)

    def on_click(self, event):
        if self.on_select_callback is not None:
            self.configure(style="Selected.TFrame")
            self.on_select_callback(self.message_id)

    def on_unselect(self):
        self.configure(style="Normal.TFrame")
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
            self.on_select_callback(self.connection_name)

    def on_unselect(self):
        self.configure(style="Normal.TFrame")
        self.update()


class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = tk.Canvas(self)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="left", fill="y")
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        # self.canvas.yview_scroll(-1 * (event.delta / 120), "units")
        print(event.delta)
        self.canvas.yview_scroll(-1*event.delta, "units")


class ScrollFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)  # create a frame (self)

        self.canvas = tk.Canvas(self, borderwidth=0, background="#ffffff")  # place canvas on self
        self.viewPort = tk.Frame(self.canvas,
                                 background="#ffffff")  # place a frame on the canvas, this frame will hold the child widgets
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)  # place a scrollbar on self
        self.canvas.configure(yscrollcommand=self.vsb.set)  # attach scrollbar action to scroll of canvas

        self.vsb.pack(side="right", fill="y")  # pack scrollbar to right of self
        self.canvas.pack(side="left", fill="both", expand=True)  # pack canvas to left of self and expand to fil
        self.canvas_window = self.canvas.create_window((4, 4), window=self.viewPort, anchor="nw",
                                                       # add view port frame to canvas
                                                       tags="self.viewPort")

        self.viewPort.bind("<Configure>",
                           self.onFrameConfigure)  # bind an event whenever the size of the viewPort frame changes.
        self.canvas.bind("<Configure>",
                         self.onCanvasConfigure)  # bind an event whenever the size of the canvas frame changes.

        self.viewPort.bind('<Enter>', self.onEnter)  # bind wheel events when the cursor enters the control
        self.viewPort.bind('<Leave>', self.onLeave)  # unbind wheel events when the cursorl leaves the control

        self.onFrameConfigure(
            None)  # perform an initial stretch on render, otherwise the scroll region has a tiny border until the first resize

    def onFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self.canvas.configure(scrollregion=self.canvas.bbox(
            "all"))  # whenever the size of the frame changes, alter the scroll region respectively.

    def onCanvasConfigure(self, event):
        '''Reset the canvas window to encompass inner frame when required'''
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window,
                               width=canvas_width)  # whenever the size of the canvas changes alter the window region respectively.

    def onMouseWheel(self, event):  # cross platform scroll wheel event
        if platform.system() == 'Windows':
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif platform.system() == 'Darwin':
            self.canvas.yview_scroll(int(-1 * event.delta), "units")
        else:
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")

    def onEnter(self, event):  # bind wheel events when the cursor enters the control
        if platform.system() == 'Linux':
            self.canvas.bind_all("<Button-4>", self.onMouseWheel)
            self.canvas.bind_all("<Button-5>", self.onMouseWheel)
        else:
            self.canvas.bind_all("<MouseWheel>", self.onMouseWheel)

    def onLeave(self, event):  # unbind wheel events when the cursorl leaves the control
        if platform.system() == 'Linux':
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")
        else:
            self.canvas.unbind_all("<MouseWheel>")


class ScrolledText(tk.Text):
    def __init__(self, master=None, **kw):
        self.frame = tk.Frame(master)
        self.vbar = ttk.Scrollbar(self.frame)
        self.vbar.pack(side=tk.RIGHT, fill=tk.Y)

        kw.update({'yscrollcommand': self.vbar.set})
        tk.Text.__init__(self, self.frame, **kw)
        self.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.vbar['command'] = self.yview

        # Copy geometry methods of self.frame without overriding Text
        # methods -- hack!
        text_meths = vars(tk.Text).keys()
        methods = vars(tk.Pack).keys() | vars(tk.Grid).keys() | vars(tk.Place).keys()
        methods = methods.difference(text_meths)

        for m in methods:
            if m[0] != '_' and m != 'config' and m != 'configure':
                setattr(self, m, getattr(self.frame, m))

    def __str__(self):
        return str(self.frame)
