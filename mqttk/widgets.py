import tkinter as tk
import traceback
from tkinter.colorchooser import askcolor
import tkinter.ttk as ttk
import platform
from mqttk.dialogs import PublishNameDialog
from mqttk.hex_printer import hex_viewer
import json
from os import linesep

CONNECT = "connected"
DISCONNECT = "disconnected"
QOS_NAMES = {
    "QoS 0": 0,
    "QoS 1": 1,
    "QoS 2": 2
}
DECODER_OPTIONS = [
    "Plain data",
    "JSON pretty formatter",
    "Hex formatter"
]


class SubscriptionFrame(ttk.Frame):
    def __init__(self,
                 container,
                 topic,
                 unsubscribe_callback,
                 colour,
                 on_colour_change,
                 mute_callback,
                 *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.container = container
        self.topic = topic
        self.colour = colour
        self.unsubscribe_callback = unsubscribe_callback
        self.on_colour_change_callback = on_colour_change
        self.mute_callback = mute_callback
        self.mute_state = False

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

        self.mute_state_checkbutton = tk.IntVar()
        self.mute_button = ttk.Checkbutton(self.options_frame,
                                           text="Mute",
                                           variable=self.mute_state_checkbutton,
                                           onvalue=1,
                                           offvalue=0)
        self.mute_button.pack(side=tk.RIGHT, padx=4, pady=4)
        self.mute_button['command'] = self.on_mute

        self.colour_picker = ttk.Label(self.options_frame, width=2, background=colour)
        self.colour_picker.bind("<Button-1>", self.on_colour_change)
        self.colour_picker.pack(side=tk.LEFT)

    def on_mute(self):
        self.mute_callback(self.topic, int(self.mute_state_checkbutton.get()))

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


class HeaderFrame(ttk.Frame):
    def __init__(self, master, app, *args, **kwargs):
        super().__init__(master=master, *args, **kwargs)

        self.connection_selector = ttk.Combobox(self, width=30, exportselection=False)
        self.connection_selector.pack(side=tk.LEFT, padx=3, pady=3)
        self.connection_selector.configure(state="readonly")
        self.config_window_button = ttk.Button(self, width=10)
        self.config_window_button["text"] = "Configure"
        self.config_window_button.pack(side=tk.LEFT, expand=False, padx=3, pady=3)
        self.config_window_button["command"] = app.spawn_configuration_window
        self.connect_button = ttk.Button(self, width=10)
        self.connect_button["text"] = "Connect"
        self.connect_button["command"] = app.on_connect_button
        self.connect_button.pack(side=tk.LEFT, expand=False, padx=3, pady=3)
        self.disconnect_button = ttk.Button(self, width=10)
        self.disconnect_button["text"] = "Disconnect"
        self.disconnect_button["state"] = "disabled"
        self.disconnect_button["command"] = app.on_disconnect_button
        self.disconnect_button.pack(side=tk.LEFT, expand=False, padx=3, pady=3)

        self.connection_indicator = tk.Label(self, text="DISCONNECTED", bg="red")
        self.connection_indicator.pack(side=tk.RIGHT, padx=5, pady=5)
        self.connection_error_notification = ttk.Label(self, foreground='red')
        self.connection_error_notification.pack(side=tk.RIGHT, expand=1, fill='x')

    def interface_toggle(self, connection_state):
        self.connection_selector.configure(state="disabled" if connection_state is CONNECT else "readonly")
        self.config_window_button.configure(state="disabled" if connection_state is CONNECT else "normal")
        self.connect_button.configure(state="disabled" if connection_state is CONNECT else "normal")
        self.disconnect_button.configure(state="normal" if connection_state is CONNECT else "disabled")

    def connection_indicator_toggle(self, connection_state):
        self.connection_indicator.configure(text='CONNECTED' if connection_state == CONNECT else "DISCONNECTED",
                                            bg="green" if connection_state == CONNECT else "red")


class SubscribeTab(ttk.Frame):
    def __init__(self, master, app, log, root_style, *args, **kwargs):
        super().__init__(master=master, *args, **kwargs)

        self.get_message_data = app.get_message_details
        self.log = log

        background_colour = root_style.lookup("TLabel", "background")
        foreground_colour = root_style.lookup("TLabel", "foreground")

        # Subscribe frame
        self.subscribe_bar_frame = ttk.Frame(self, height=1)
        self.subscribe_bar_frame.pack(anchor="nw", side=tk.TOP, fill=tk.X)
        # Subscribe selector combobox
        self.subscribe_selector = ttk.Combobox(self.subscribe_bar_frame, width=30, exportselection=False)
        self.subscribe_selector.pack(side=tk.LEFT, padx=3, pady=3)
        self.subscribe_selector["values"] = []
        # Subscribe button
        self.subscribe_button = ttk.Button(self.subscribe_bar_frame, width=10)
        self.subscribe_button.pack(side=tk.LEFT, padx=3, pady=3)
        self.subscribe_button["text"] = "Subscribe"
        self.subscribe_button["command"] = app.add_subscription
        # Flush messages button
        self.flush_messages_button = ttk.Button(self.subscribe_bar_frame, text="Clear messages")
        self.flush_messages_button.pack(side=tk.RIGHT, padx=3)
        self.flush_messages_button["command"] = app.flush_messages
        # Autoscroll checkbox
        self.autoscroll_state = tk.IntVar()
        self.autoscroll_checkbox = ttk.Checkbutton(self.subscribe_bar_frame,
                                                   text="Autoscroll",
                                                   variable=self.autoscroll_state,
                                                   offvalue=0,
                                                   onvalue=1)
        self.autoscroll_checkbox.pack(side=tk.RIGHT, padx=3)

        # Subscribe bottom part frame
        self.subscribe_tab_bottom_frame = ttk.Frame(self)
        self.subscribe_tab_bottom_frame.pack(fill="both", anchor="w", expand=True, padx=3, pady=3)
        # Subscription list paned window
        self.subscription_paned_window = tk.PanedWindow(self.subscribe_tab_bottom_frame,
                                                        orient=tk.HORIZONTAL,
                                                        sashrelief="groove",
                                                        sashwidth=6,
                                                        sashpad=2,
                                                        background=background_colour)
        self.subscription_paned_window.pack(side=tk.LEFT, fill="both", expand=1)
        self.subscriptions_frame = ScrollFrame(self.subscribe_tab_bottom_frame)
        self.subscriptions_frame.pack(fill="y", side=tk.LEFT)
        self.subscription_paned_window.add(self.subscriptions_frame)

        # Incoming message resizable panel
        self.message_paned_window = tk.PanedWindow(self.subscribe_tab_bottom_frame,
                                                   orient=tk.VERTICAL,
                                                   sashrelief="groove",
                                                   sashwidth=6,
                                                   sashpad=2,
                                                   background=background_colour)
        self.message_paned_window.pack(fill='both', padx=3, pady=3, expand=1)
        self.subscription_paned_window.add(self.message_paned_window)

        # Incoming messages listbox
        self.incoming_messages_frame = ttk.Frame(self.subscribe_tab_bottom_frame)
        self.incoming_messages_frame.pack(expand=1, fill='both')
        self.incoming_messages_list = tk.Listbox(self.incoming_messages_frame, selectmode="browse",
                                                 font="Courier 13", background=background_colour)  # TkFixedFont, "Courier 13"
        self.incoming_messages_list.pack(side=tk.LEFT, fill='both', expand=1)
        self.incoming_messages_list.bind("<<ListboxSelect>>", self.on_message_select)
        self.incoming_messages_scrollbar = ttk.Scrollbar(self.incoming_messages_frame,
                                                         orient='vertical',
                                                         command=self.incoming_messages_list.yview)
        self.incoming_messages_list['yscrollcommand'] = self.incoming_messages_scrollbar.set
        self.incoming_messages_scrollbar.pack(side=tk.RIGHT, fill='y')
        self.message_paned_window.add(self.incoming_messages_frame, height=300)

        # Incoming messages scrollable frame
        # self.incoming_messages = ScrollFrame(self.subscribe_tab_bottom_frame)
        # self.incoming_messages.pack()
        # self.message_paned_window.add(self.incoming_messages)

        # Message content frame
        self.message_content_frame = ttk.Frame(self.subscribe_tab_bottom_frame)
        self.message_content_frame.pack(anchor="n", expand=True, fill="both")
        self.message_paned_window.add(self.message_content_frame)

        # Message topic and ID frame
        self.message_topic_and_id_frame = ttk.Frame(self.message_content_frame)
        self.message_topic_and_id_frame.pack(fill="x")
        # Message topic label
        self.message_topic_label = tk.Text(self.message_topic_and_id_frame, height=1, borderwidth=0,
                                           state="disabled", background="white", foreground="black",
                                           exportselection=False)
        self.message_topic_label.pack(side=tk.LEFT, padx=3, pady=3, fill="x", expand=1)
        # Message ID label
        self.message_id_label = ttk.Label(self.message_topic_and_id_frame, width=10)
        self.message_id_label["text"] = "ID"
        self.message_id_label.pack(side=tk.RIGHT, padx=3, pady=3)

        # Message date frame
        self.message_date_and_qos_frame = ttk.Frame(self.message_content_frame)
        self.message_date_and_qos_frame.pack(fill="x")
        # Message date label
        self.message_date_label = ttk.Label(self.message_date_and_qos_frame)
        self.message_date_label["text"] = "DATE"
        self.message_date_label.pack(side=tk.LEFT, padx=3, pady=3)
        # Message QoS label
        self.message_qos_label = ttk.Label(self.message_date_and_qos_frame, width=10)
        self.message_qos_label["text"] = "QOS"
        self.message_qos_label.pack(side=tk.RIGHT, padx=3, pady=3)
        # Decoder selector
        self.message_decoder_selector = ttk.Combobox(self.message_date_and_qos_frame,
                                                     width=40,
                                                     state='readonly',
                                                     values=DECODER_OPTIONS,
                                                     exportselection=False)
        self.message_decoder_selector.bind()
        self.message_decoder_selector.pack(side=tk.RIGHT, padx=3, pady=3)
        self.message_decoder_selector_label = ttk.Label(self.message_date_and_qos_frame, text="Message decoder")
        self.message_decoder_selector_label.pack(side=tk.RIGHT, padx=3, pady=3)
        self.message_decoder_selector.current(0)
        self.message_decoder_selector.bind("<<ComboboxSelected>>", self.on_decoder_select)

        # Message Payload
        self.message_payload_box = CustomScrolledText(self.message_content_frame,
                                                      exportselection=False,
                                                      background="white",
                                                      foreground="black")
        self.message_payload_box.pack(fill="both", expand=True)
        self.message_payload_box.configure(state="disabled")
        # Message decoder

    def interface_toggle(self, connection_state):
        # Subscribe tab items
        self.subscribe_button.configure(state="normal" if connection_state is CONNECT else "disabled")
        self.subscribe_selector.configure(state="normal" if connection_state is CONNECT else "disabled")

    def on_decoder_select(self, *args, **kwargs):
        self.on_message_select()
        pass

    def add_message(self, message_title, colour):
        self.incoming_messages_list.insert(tk.END, message_title)
        self.incoming_messages_list.itemconfig(tk.END, fg=colour)
        if bool(self.autoscroll_state.get()):
            self.incoming_messages_list.selection_clear(0, tk.END)
            self.incoming_messages_list.activate(tk.END)
            self.incoming_messages_list.see("end")
            self.incoming_messages_list.selection_set("end", "end")
            self.on_message_select(None)

    def on_message_select(self, *args, **kwargs):
        message_list_id = self.incoming_messages_list.curselection()
        try:
            message_label = self.incoming_messages_list.get(message_list_id)
        except Exception as e:
            self.log.warning("Failed to get message from incoming message list (maybe empty?)", message_list_id)
            message_label = None
        if message_label is None:
            message_id = 0
        else:
            message_id = int(message_label[-5:])
        message_data = self.get_message_data(message_id)
        self.message_topic_label["state"] = "normal"
        self.message_topic_label.delete(1.0, tk.END)
        self.message_topic_label.insert(1.0, message_data.get("topic", ""))
        self.message_topic_label["state"] = "disabled"
        self.message_date_label["text"] = message_data.get("time_string", "")
        self.message_qos_label["text"] = "QoS: {}".format(message_data.get("qos", ""))
        self.message_id_label["text"] = "ID: {}".format(message_id)
        self.message_payload_box.configure(state="normal")
        self.message_payload_box.delete(1.0, tk.END)
        decoder = self.message_decoder_selector.get()
        if decoder == "JSON pretty formatter":
            try:
                new_message_structure = json.loads(message_data.get("payload", ""))
            except Exception as e:
                new_message = "        *** FAILED TO LOAD JSON ***{}{}{}{}".format(linesep+linesep,
                                                                                   e,
                                                                                   linesep+linesep,
                                                                                   traceback.format_exc())
            else:
                new_message = json.dumps(new_message_structure, indent=2)
            self.message_payload_box.insert(1.0, new_message)

        elif decoder == "Hex formatter":
            for line in hex_viewer(message_data.get("payload", "")):
                self.message_payload_box.insert(tk.END, line+linesep)

        else:
            self.message_payload_box.insert(1.0, message_data.get("payload", ""))
        self.message_payload_box.configure(state="disabled")

    def flush_messages(self):
        self.incoming_messages_list.delete(0, "end")
        self.on_message_select()


class PublishHistoryFrame(ttk.Frame):
    def __init__(self,
                 master,
                 name,
                 config,
                 publish_callback,
                 delete_callback,
                 on_select_callback,
                 on_edit_callback,
                 *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.name = name
        self.configuration = config
        self.publish_callback = publish_callback
        self.delete_callback = delete_callback
        self.on_select_callback = on_select_callback
        self.on_edit_callback = on_edit_callback

        self["relief"] = "groove"
        self["borderwidth"] = 2
        self.bind("<Button-1>", self.on_select)

        self.name_label = ttk.Label(self, text=name, justify="left")
        self.name_label.pack(expand=1, fill="x", side=tk.TOP, padx=3, pady=6)
        self.name_label.bind("<Button-1>", self.on_select)

        self.publish_history_actions = ttk.Frame(self)
        self.publish_history_actions.pack(side=tk.TOP, fill='x', padx=3, pady=3)
        self.publish_history_actions.bind("<Button-1>", self.on_select)

        self.publish_button = ttk.Button(self.publish_history_actions, text="Publish")
        self.publish_button["command"] = self.on_publish_button
        self.publish_button.pack(side=tk.RIGHT, padx=3, pady=3)

        self.edit_button = ttk.Button(self.publish_history_actions, text="Rename")
        self.edit_button["command"] = self.on_edit_button
        self.edit_button.pack(side=tk.LEFT, padx=3, pady=3)

        self.delete_button = ttk.Button(self.publish_history_actions, text="Delete")
        self.delete_button["command"] = self.on_delete_button
        self.delete_button.pack(side=tk.LEFT, padx=3, pady=3)

    def on_select(self, *args, **kwargs):
        self.publish_history_actions.configure(style="Selected.TFrame")
        self.configure(style="Selected.TFrame")
        self.name_label.configure(style="Selected.TLabel")
        self.on_select_callback(self)

    def on_unselect(self, *args, **kwargs):
        self.publish_history_actions.configure(style="TFrame")
        self.configure(style="TFrame")
        self.name_label.configure(style="TLabel")

    def on_delete_button(self):
        self.delete_callback(self.name)

    def on_edit_button(self):
        self.on_select()
        self.on_edit_callback()

    def on_publish_button(self):
        self.publish_callback(self.configuration["topic"],
                              self.configuration["payload"],
                              self.configuration["qos"],
                              self.configuration["retained"])


class PublishTab(ttk.Frame):
    def __init__(self, master, app, log, root_style, *args, **kwargs):
        super().__init__(master=master, *args, **kwargs)

        background_colour = root_style.lookup("TLabel", "background")

        self.app_root = app.root
        self.config_handler = app.config_handler
        self.publish = app.on_publish
        self.current_connection = None
        self.topic_history = []
        self.log = log

        self.current_publish_history_selected = None  # Reference to the selected PublishHistoryFrame
        self.publish_history_frames = {}  # publish history name to object reference
        self.selected_history_unselect_callback = None

        self.publish_paned_window = tk.PanedWindow(self,
                                                   orient=tk.HORIZONTAL,
                                                   sashrelief="groove",
                                                   sashwidth=6,
                                                   sashpad=2,
                                                   background=background_colour)
        self.publish_paned_window.pack(fill='both', expand=1, side=tk.LEFT)
        self.saved_publishes = ScrollFrame(self)
        self.saved_publishes.pack(fill="y", expand=1, side=tk.LEFT)
        self.publish_paned_window.add(self.saved_publishes, width=350)

        self.publish_interface = ttk.Frame(self)
        self.publish_interface.pack(fill='both', expand=1)

        self.publish_interface_actions = ttk.Frame(self.publish_interface)
        self.publish_interface_actions.pack(fill='x', side=tk.TOP)
        self.publish_topic_selector = ttk.Combobox(self.publish_interface_actions, width=40)
        self.publish_topic_selector.pack(side=tk.LEFT, padx=4, pady=4)

        self.publish_button = ttk.Button(self.publish_interface_actions, text="Publish")
        self.publish_button['command'] = self.on_publish_button
        self.publish_button.pack(side=tk.LEFT, padx=2, pady=4)

        self.save_publish_button = ttk.Button(self.publish_interface_actions, text="Save")
        self.save_publish_button.pack(side=tk.LEFT, padx=4, pady=4)
        self.save_publish_button["command"] = self.on_publish_save

        self.retained_state_var = tk.IntVar()
        self.retained_checkbox = ttk.Checkbutton(self.publish_interface_actions,
                                                 text="Retained",
                                                 onvalue=1,
                                                 offvalue=0,
                                                 variable=self.retained_state_var)
        self.retained_checkbox.pack(side=tk.RIGHT, pady=4, padx=2)

        self.qos_selector = ttk.Combobox(self.publish_interface_actions,
                                         exportselection=False,
                                         width=7,
                                         values=list(QOS_NAMES.keys()))
        self.qos_selector.current(0)
        self.qos_selector.pack(side=tk.RIGHT, pady=4, padx=2)

        self.payload_editor = CustomScrolledText(self.publish_interface,
                                                 font="Courier 13",
                                                 background="white",
                                                 foreground="black")
        self.payload_editor.pack(fill="both", expand=1, side=tk.BOTTOM)
        self.publish_paned_window.add(self.publish_interface)

    def on_publish_history_delete(self, name):
        self.publish_history_frames[name].pack_forget()
        self.publish_history_frames[name].destroy()
        self.config_handler.delete_publish_history_item(self.current_connection, name)

    def publish_message(self, topic, payload, qos, retained):
        if topic not in self.topic_history:
            self.config_handler.save_publish_topic_history_item(self.current_connection, topic)
        try:
            self.publish(topic, payload, qos, retained)
        except Exception as e:
            self.log.exception("Failed to publish!", e, topic, payload, qos, retained)

    def on_publish_button(self, *args, **kwargs):
        if self.publish_topic_selector.get() != "":
            self.publish(self.publish_topic_selector.get(),
                         self.payload_editor.get(1.0, tk.END),
                         QOS_NAMES.get(self.qos_selector.get(), 0),
                         bool(self.retained_state_var.get()))
            new = self.config_handler.save_publish_topic_history_item(self.current_connection,
                                                                      self.publish_topic_selector.get())
            if new:
                if len(self.config_handler.get_publish_topic_history(self.current_connection)) > 1:
                    self.publish_topic_selector['values'] += (self.publish_topic_selector.get(),)
                else:
                    self.publish_topic_selector['values'] = (self.publish_topic_selector.get(),)

    def on_publish_save(self, *args, **kwargs):
        if self.publish_topic_selector.get() == "":
            return
        current_name = ""
        if self.current_publish_history_selected is not None:
            current_name = self.current_publish_history_selected.name
        name_entry_window = PublishNameDialog(self.app_root, current_name, self.save_new_name_callback)
        name_entry_window.transient(self.app_root)
        name_entry_window.wait_visibility()
        name_entry_window.grab_set()
        name_entry_window.wait_window()

    def on_new_name_rename(self, new_name):
        if self.current_publish_history_selected.name == new_name:
            return
        self.publish_history_frames[new_name] = self.current_publish_history_selected
        self.publish_history_frames.pop(self.current_publish_history_selected.name)
        self.config_handler.save_publish_history_item(self.current_connection,
                                                      new_name,
                                                      self.current_publish_history_selected.configuration)
        self.config_handler.delete_publish_history_item(self.current_connection,
                                                        self.current_publish_history_selected.name)
        self.current_publish_history_selected.name = new_name
        self.current_publish_history_selected.name_label["text"] = new_name

    def on_rename_callback(self):
        current_name = self.current_publish_history_selected.name
        name_entry_window = PublishNameDialog(self.app_root, current_name, self.on_new_name_rename)
        name_entry_window.transient(self.app_root)
        name_entry_window.wait_visibility()
        name_entry_window.grab_set()
        name_entry_window.wait_window()

    def save_new_name_callback(self, new_name):
        new_config = {
            "topic": self.publish_topic_selector.get(),
            "qos": QOS_NAMES.get(self.qos_selector.get(), 0),
            "retained": bool(self.retained_state_var.get()),
            "payload": self.payload_editor.get(1.0, tk.END)
        }
        self.config_handler.save_publish_history_item(self.current_connection, new_name, new_config)
        if self.current_publish_history_selected is None or self.current_publish_history_selected.name != new_name:
            self.add_new_publish_history_item(new_name, new_config)
            self.publish_history_frames[new_name].on_select()
        else:
            self.current_publish_history_selected.configuration = new_config

    def add_new_publish_history_item(self, name, config):
        self.publish_history_frames[name] = PublishHistoryFrame(self.saved_publishes.viewPort,
                                                                name,
                                                                config,
                                                                self.publish_message,
                                                                self.on_publish_history_delete,
                                                                self.on_publish_history_select,
                                                                self.on_rename_callback)
        self.publish_history_frames[name].pack(fill=tk.X, expand=1, padx=2, pady=1)

    def load_publish_and_topic_history(self, current_connection):
        self.current_connection = current_connection
        self.publish_topic_selector.set(self.config_handler.get_last_publish_topic(self.current_connection))
        publish_history = self.config_handler.get_publish_history(current_connection)
        for name, config in publish_history.items():
            self.add_new_publish_history_item(name, config)
        self.topic_history = self.config_handler.get_publish_topic_history(current_connection)
        self.publish_topic_selector.configure(values=self.topic_history)

    def on_publish_history_select(self, history_item):
        if self.selected_history_unselect_callback is not None and history_item.name != self.current_publish_history_selected.name:
            try:
                self.selected_history_unselect_callback()
            except Exception as e:
                self.log.warning("Failed to deselect item, maybe no longer present?", e)
        self.selected_history_unselect_callback = history_item.on_unselect
        self.publish_topic_selector.set(history_item.configuration["topic"])
        self.qos_selector.current(int(history_item.configuration["qos"]))
        self.retained_state_var.set(history_item.configuration["retained"])
        self.payload_editor.delete(1.0, tk.END)
        self.payload_editor.insert(1.0, history_item.configuration["payload"])
        self.current_publish_history_selected = history_item

    def interface_toggle(self, connection_state, current_connection=None):
        if connection_state == CONNECT:
            self.load_publish_and_topic_history(current_connection)
        if connection_state == DISCONNECT:
            for name, publish_history_element in self.publish_history_frames.items():
                publish_history_element.pack_forget()
                publish_history_element.destroy()
            self.publish_history_frames = {}
            self.payload_editor.delete(1.0, tk.END)
            self.publish_topic_selector.configure(values=[])
            self.publish_topic_selector.set("")

        self.publish_button.configure(state="normal" if connection_state is CONNECT else "disabled")
        self.save_publish_button.configure(state="normal" if connection_state is CONNECT else "disabled")
        self.retained_checkbox.configure(state="normal" if connection_state is CONNECT else "disabled")
        self.qos_selector.configure(state="readonly" if connection_state is CONNECT else "disabled")
        self.publish_topic_selector.configure(state="normal" if connection_state is CONNECT else "disabled")
        self.payload_editor.configure(state="normal" if connection_state is CONNECT else "disabled")


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


class CustomScrolledText(tk.Text):
    def __init__(self, master=None, **kw):
        self.frame = ttk.Frame(master)
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
