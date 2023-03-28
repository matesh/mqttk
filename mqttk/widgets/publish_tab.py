"""
MQTTk - Lightweight graphical MQTT client and message analyser

Copyright (C) 2022  Máté Szabó

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

import tkinter as tk
import tkinter.ttk as ttk
from mqttk.widgets.scrolled_text import CustomScrolledText
from mqttk.widgets.scroll_frame import ScrollFrame
from mqttk.widgets.dialogs import PublishNameDialog
from mqttk.helpers import get_clear_combobox_selection_function
import base64
from mqttk.constants import QOS_NAMES, CONNECT, DISCONNECT


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
        self.mqtt_manager = None

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
                              base64.b64decode(self.configuration["payload"]).decode("utf-8"),
                              self.configuration["qos"],
                              self.configuration["retained"])


class PublishTab(ttk.Frame):
    def __init__(self, master, app, log, root_style, *args, **kwargs):
        super().__init__(master=master, *args, **kwargs)

        background_colour = root_style.lookup("TLabel", "background")

        self.app_root = app.root
        self.config_handler = app.config_handler
        self.current_connection = None
        self.mqtt_manager = None
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
        self.publish_topic_selector.bind("<<ComboboxSelected>>",
                                         get_clear_combobox_selection_function(self.publish_topic_selector))
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
        self.qos_selector.bind("<<ComboboxSelected>>",
                               get_clear_combobox_selection_function(self.qos_selector))
        self.qos_selector.current(0)
        self.qos_selector.pack(side=tk.RIGHT, pady=4, padx=2)

        self.payload_editor = CustomScrolledText(self.publish_interface,
                                                 font="Courier 13",
                                                 background="white",
                                                 foreground="black", highlightthickness=0)
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
            if self.mqtt_manager is not None:
                self.mqtt_manager.publish(topic, payload, qos, retained)
        except Exception as e:
            self.log.exception("Failed to publish!", e, topic, payload, qos, retained)

    def on_publish_button(self, *args, **kwargs):
        if self.publish_topic_selector.get() != "":
            payload = self.payload_editor.get(1.0, tk.END)
            # Remove stupid fucking newline that gets added to the bloody text widget for no reason
            if payload[-1] == '\n':
                payload = payload[0:-1]
            self.publish_message(self.publish_topic_selector.get(),
                                 payload,
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
            "payload": base64.b64encode(self.payload_editor.get(1.0, tk.END).encode("utf-8")).decode("utf-8")
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
        self.payload_editor.insert(1.0, base64.b64decode(history_item.configuration["payload"]).decode("utf-8"))
        self.current_publish_history_selected = history_item

    def interface_toggle(self, connection_state, mqtt_manager=None, current_connection=None):
        self.mqtt_manager = mqtt_manager
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
