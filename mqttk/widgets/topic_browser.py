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
import os
import tkinter as tk
import tkinter.ttk as ttk
import time
import sys
import traceback
from functools import partial
from datetime import datetime

from mqttk.constants import CONNECT, COLOURS


class TopicBrowser(ttk.Frame):
    def __init__(self, master, config_handler, log, root, *args, **kwargs):
        super().__init__(master=master, *args, **kwargs)
        self.config_handler = config_handler
        self.log = log
        self.subscription_frames = {}
        self.color_carousel = -1
        self.current_connection = None
        self.last_connection = None
        self.current_subscription = None
        self.root = root

        self.mqtt_manager = None
        self.message_id_counter = 0
        self.individual_topics = 0

        # Subscribe frame
        self.topic_browser_bar_frame = ttk.Frame(self, height=1)
        self.topic_browser_bar_frame.pack(anchor="nw", side=tk.TOP, fill=tk.X)
        # Subscribe selector combobox
        self.subscribe_selector = ttk.Combobox(self.topic_browser_bar_frame, width=30, exportselection=False)
        self.subscribe_selector.pack(side=tk.LEFT, padx=3, pady=3)
        self.subscribe_selector["values"] = []
        # Subscribe button
        self.browse_button = ttk.Button(self.topic_browser_bar_frame, width=10, text="Browse")
        self.browse_button.pack(side=tk.LEFT, padx=3, pady=3)
        self.browse_button["command"] = self.add_subscription
        # Stop button
        self.stop_button = ttk.Button(self.topic_browser_bar_frame, width=10, text="Stop", state="disabled")
        self.stop_button.pack(side=tk.LEFT, padx=3, pady=3)
        self.stop_button["command"] = self.on_unsubscribe

        self.stat_label = ttk.Label(self.topic_browser_bar_frame)
        self.stat_label.pack(side=tk.LEFT, padx=3, pady=3)

        # Flush messages button
        self.flush_messages_button = ttk.Button(self.topic_browser_bar_frame, text="Clear topics")
        self.flush_messages_button.pack(side=tk.RIGHT, padx=3)
        self.flush_messages_button["command"] = self.flush_messages
        # Filter retained checkbox
        self.filter_retained = tk.IntVar()
        self.filter_retained_checkbox = ttk.Checkbutton(self.topic_browser_bar_frame,
                                                        text="Ignore retained messages",
                                                        variable=self.filter_retained,
                                                        offvalue=0,
                                                        onvalue=1)
        self.filter_retained_checkbox.pack(side=tk.RIGHT, padx=3)

        self.treeview_frame = ttk.Frame(self)
        self.treeview_frame.pack(expand=1, fill="both", pady=2, padx=2)
        self.topic_treeview = ttk.Treeview(self.treeview_frame, columns=("qos", "retained", "last_message", "payload"), show="tree headings")
        self.topic_treeview.heading('#0', text='Topic')
        self.topic_treeview.column('#0', minwidth=300, width=300, stretch=tk.NO)
        self.topic_treeview.heading('qos', text='QoS')
        self.topic_treeview.column('qos', minwidth=50, width=50, stretch=tk.NO)
        self.topic_treeview.heading('retained', text='Retained')
        self.topic_treeview.column('retained', minwidth=70, width=80, stretch=tk.NO)
        self.topic_treeview.heading('last_message', text='Last message')
        self.topic_treeview.column('last_message', minwidth=70, width=90, stretch=tk.NO)
        self.topic_treeview.heading('payload', text='Payload')
        self.topic_treeview.column('payload', minwidth=300, width=900, stretch=tk.NO)
        if sys.platform == "darwin":
            self.topic_treeview.bind("<Button-2>", self.popup)
        if sys.platform == "linux":
            self.topic_treeview.bind("<Button-3>", self.popup)
        if sys.platform == "win32":
            self.topic_treeview.bind("<Button-3>", self.popup)

        self.vertical_scrollbar = ttk.Scrollbar(self.treeview_frame, orient="vertical", command=self.topic_treeview.yview)
        self.vertical_scrollbar.pack(side=tk.RIGHT, fill="y")
        self.topic_treeview.configure(yscrollcommand=self.vertical_scrollbar.set)
        self.topic_treeview.pack(fill="both", side=tk.LEFT, expand=1)

        self.horizontal_scrollbar = ttk.Scrollbar(self, orient="horizontal", command=self.topic_treeview.xview)
        self.horizontal_scrollbar.pack(side=tk.BOTTOM, fill="x")
        self.topic_treeview.configure(xscrollcommand=self.horizontal_scrollbar.set)

        self.popup_menu = tk.Menu(self, tearoff=0)
        self.popup_menu.add_command(label="Copy topic", command=self.copy_topic)
        self.popup_menu.add_command(label="Copy payload", command=self.copy_payload)

    def interface_toggle(self, connection_state, mqtt_manager, current_connection):
        # Subscribe tab items
        self.mqtt_manager = mqtt_manager
        if connection_state != CONNECT:
            self.last_connection = self.current_connection
        else:
            if self.last_connection != current_connection:
                self.flush_messages()

        self.current_connection = current_connection
        self.browse_button.configure(state="normal" if connection_state is CONNECT else "disabled")
        self.subscribe_selector.configure(state="normal" if connection_state is CONNECT else "disabled")
        self.current_subscription = None

    def get_color(self, topic):
        colour = self.config_handler.get_subscription_colour(self.current_connection, topic)
        if colour is not None:
            return colour
        self.color_carousel += 1
        if self.color_carousel > len(COLOURS):
            self.color_carousel = 0
        return COLOURS[self.color_carousel]

    def add_subscription(self):
        topic = self.subscribe_selector.get()
        if topic != "":
            try:
                callback = partial(self.on_mqtt_message, subscription_pattern=topic)
                callback.__name__ = "MyCallback"  # This is to fix some weird behaviour of the paho client on linux
                self.mqtt_manager.add_subscription(topic_pattern=topic,
                                                   on_message_callback=callback)
            except Exception as e:
                self.log.exception("Failed to subscribe!", e)
                return
            if self.subscribe_selector["values"] == "":
                self.subscribe_selector["values"] = [topic]
            elif topic not in self.subscribe_selector['values']:
                self.subscribe_selector['values'] += (topic,)
            self.config_handler.add_subscription_history(self.current_connection,
                                                         topic,
                                                         self.get_color(topic))
        self.current_subscription = topic
        self.browse_button["state"] = "disabled"
        self.stop_button["state"] = "normal"

    def load_subscription_history(self):
        self.subscribe_selector.configure(
            values=self.config_handler.get_subscription_history_list(self.current_connection))
        self.subscribe_selector.set(self.config_handler.get_last_subscribe_used(self.current_connection))

    def on_mqtt_message(self, _, __, msg, subscription_pattern):
        try:
            if bool(self.filter_retained.get()) and msg.retain == 1:
                return

            try:
                payload_decoded = str(msg.payload.decode("utf-8"))
            except Exception:
                payload_decoded = msg.payload

            time_string = datetime.fromtimestamp(time.time()).strftime("%H:%M:%S")
            topic_split = msg.topic.split("/")

            # Fix anomaly when someone thinks MQTT is linux and starts the topic with /...
            if msg.topic.startswith("/"):
                topic_split[0] = "/"

            if 1 < len(topic_split):
                if topic_split[0] not in self.topic_treeview.get_children(""):
                    try:
                        self.topic_treeview.insert("", "end", topic_split[0], text=topic_split[0])
                    except Exception:
                        # print(msg.topic, topic_split[0], self.topic_treeview.get_children(""))
                        raise
                for i in range(1, len(topic_split)-1):
                    parent_topic = "/".join(topic_split[0:i])
                    topic = "/".join(topic_split[0:i+1])
                    if topic not in self.topic_treeview.get_children(parent_topic):
                        self.topic_treeview.insert(parent_topic, "end", topic, text=topic_split[i])

            parent_topic = "/".join(topic_split[0:-1])
            topic = "/".join(topic_split)
            if topic not in self.topic_treeview.get_children(parent_topic):
                self.update_individual_topics()
                self.topic_treeview.insert(parent_topic,
                                           "end",
                                           "/".join(topic_split),
                                           text=topic_split[-1],
                                           values=(msg.qos,
                                                   "RETAINED" if msg.retain == 1 else "",
                                                   time_string,
                                                   payload_decoded))
            else:
                self.topic_treeview.set(topic, "qos", msg.qos)
                self.topic_treeview.set(topic, "retained", "RETAINED" if msg.retain == 1 else "")
                self.topic_treeview.set(topic, "last_message", time_string)
                self.topic_treeview.set(topic, "payload", payload_decoded)

        except Exception as e:
            self.log.exception("Exception inserting new message to treeview",
                               os.linesep, msg.topic, msg.payload, os.linesep, e, traceback.format_exc())

    def on_unsubscribe(self):
        try:
            self.mqtt_manager.unsubscribe(self.current_subscription)
        except Exception as e:
            self.log.warning("Failed to unsubscribe", self.current_subscription, "maybe a failed subscription?")
        self.current_subscription = None
        self.stop_button["state"] = "disabled"
        self.browse_button["state"] = "normal"

    def flush_messages(self):
        self.update_individual_topics(0)
        for child in self.topic_treeview.get_children():
            self.topic_treeview.delete(child)

    def update_individual_topics(self, value=None):
        if value is not None:
            self.individual_topics = value
        else:
            self.individual_topics += 1
        self.stat_label["text"] = "{} individual topics mapped".format(self.individual_topics)

    def copy_topic(self, *args, **kwargs):
        try:
            topic = self.topic_treeview.selection()[0]
        except Exception:
            pass
        else:
            self.root.clipboard_clear()
            self.root.clipboard_append(topic)

    def copy_payload(self, *args, **kwargs):
        try:
            selection = self.topic_treeview.selection()[0]
            values = self.topic_treeview.item(selection).get("values", [])
            payload = values[3]
        except Exception:
            pass
        else:
            self.root.clipboard_clear()
            self.root.clipboard_append(payload)

    def popup(self, event, *args, **kwargs):
        try:
            self.popup_menu.tk_popup(event.x_root, event.y_root, 0)
        except Exception as e:
            pass
        finally:
            self.popup_menu.grab_release()
