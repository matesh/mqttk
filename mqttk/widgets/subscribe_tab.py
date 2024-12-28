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
from tkinter.colorchooser import askcolor
import base64
import json
from os import linesep
import traceback
from functools import partial
import time
from datetime import datetime
import zlib
from bz2 import decompress
from multiprocessing import Lock
from copy import deepcopy

from mqttk.widgets.scroll_frame import ScrollFrame
from mqttk.widgets.scrolled_text import CustomScrolledText
from mqttk.constants import CONNECT, DECODER_OPTIONS, COLOURS
from mqttk.hex_printer import hex_viewer
from mqttk.helpers import get_clear_combobox_selection_function, clear_combobox_selection

ZLIB_TAG0 = chr(0x78)
ZLIB_TAG1 = (chr(0x01), chr(0x5E), chr(0x9C), chr(0xDA))


def decompress_message(message_data):
    try:
        return zlib.decompress(message_data)
    except Exception:
        pass

    try:
        return decompress(message_data)
    except Exception:
        pass

    return message_data


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
        self.current_connection = None

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
            self.on_colour_change_callback(self.topic, self.colour)


class SubscribeTab(ttk.Frame):
    def __init__(self, master, config_handler, log, root_style, *args, **kwargs):
        super().__init__(master=master, *args, **kwargs)
        self.config_handler = config_handler
        self.log = log
        self.subscription_frames = {}
        self.color_carousel = -1
        self.current_connection = None
        self.last_connection = None
        self.exporting = False
        # Holds messages and relevant stuff
        # {
        #     "id": {
        #         "topic": "message topic",
        #         "subscription_pattern": "subscription pattern",
        #         "timestamp": "date of reception timestamp or date string whatever",
        #         "qos": "message qos",
        #         "payload": "message content",
        #         "message_list_instance_ref": message list object reference
        #     }
        #
        # }
        self.messages = {}

        self.mute_patterns = []
        self.mqtt_manager = None
        self.message_id_counter = 0

        background_colour = root_style.lookup("TLabel", "background")
        foreground_colour = root_style.lookup("TLabel", "foreground")

        # Subscribe frame
        self.subscribe_bar_frame = ttk.Frame(self, height=1)
        self.subscribe_bar_frame.pack(anchor="nw", side=tk.TOP, fill=tk.X)
        # Subscribe selector combobox
        self.subscribe_selector = ttk.Combobox(self.subscribe_bar_frame, width=30, exportselection=False)
        self.subscribe_selector.bind("<<ComboboxSelected>>",
                                     get_clear_combobox_selection_function(self.subscribe_selector))
        self.subscribe_selector.pack(side=tk.LEFT, padx=3, pady=3)
        self.subscribe_selector["values"] = []
        # Subscribe button
        self.subscribe_button = ttk.Button(self.subscribe_bar_frame, width=10)
        self.subscribe_button.pack(side=tk.LEFT, padx=3, pady=3)
        self.subscribe_button["text"] = "Subscribe"
        self.subscribe_button["command"] = self.add_subscription
        # Flush messages button
        self.flush_messages_button = ttk.Button(self.subscribe_bar_frame, text="Clear messages")
        self.flush_messages_button.pack(side=tk.RIGHT, padx=3)
        self.flush_messages_button["command"] = self.flush_messages
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
        self.incoming_messages_list.bind("<<ListboxSelect>>", self.on_message_select)

        self.incoming_messages_scrollbar = ttk.Scrollbar(self.incoming_messages_frame,
                                                         orient='vertical',
                                                         command=self.incoming_messages_list.yview)
        self.incoming_messages_list['yscrollcommand'] = self.incoming_messages_scrollbar.set
        self.incoming_messages_scrollbar.pack(side=tk.RIGHT, fill='y')

        self.incoming_messages_scrollbar_h = ttk.Scrollbar(self.incoming_messages_frame,
                                                           orient='horizontal',
                                                           command=self.incoming_messages_list.xview)
        self.incoming_messages_list['xscrollcommand'] = self.incoming_messages_scrollbar_h.set
        self.incoming_messages_scrollbar_h.pack(side=tk.BOTTOM, fill='x')
        self.incoming_messages_list.pack(side=tk.LEFT, fill='both', expand=1)

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

        self.attempt_to_decompress = tk.IntVar()
        self.decompress_checkbox = ttk.Checkbutton(self.message_date_and_qos_frame,
                                                   text="Attempt to decompress",
                                                   variable=self.attempt_to_decompress,
                                                   offvalue=0,
                                                   onvalue=1,
                                                   command=self.on_message_select)
        self.decompress_checkbox.pack(side=tk.RIGHT, padx=3)

        # Decoder selector
        self.message_decoder_selector = ttk.Combobox(self.message_date_and_qos_frame,
                                                     width=20,
                                                     state='readonly',
                                                     values=DECODER_OPTIONS,
                                                     exportselection=False)
        self.message_decoder_selector.pack(side=tk.RIGHT, padx=3, pady=3)
        self.message_decoder_selector_label = ttk.Label(self.message_date_and_qos_frame, text="Message decoder")
        self.message_decoder_selector_label.pack(side=tk.RIGHT, padx=3, pady=3)
        self.message_decoder_selector.current(0)
        self.message_decoder_selector.bind("<<ComboboxSelected>>", self.on_decoder_select)

        # Message Payload
        self.message_payload_box = CustomScrolledText(self.message_content_frame,
                                                      exportselection=False,
                                                      background="white",
                                                      foreground="black", highlightthickness=0)
        self.message_payload_box.pack(fill="both", expand=True)
        self.message_payload_box.configure(state="disabled")
        # Message decoder

    def interface_toggle(self, connection_state, mqtt_manager, current_connection):
        # Subscribe tab items
        self.mqtt_manager = mqtt_manager
        if connection_state != CONNECT:
            self.last_connection = self.current_connection
        else:
            if self.last_connection != current_connection:
                self.flush_messages()
        self.current_connection = current_connection
        self.subscribe_button.configure(state="normal" if connection_state is CONNECT else "disabled")
        self.subscribe_selector.configure(state="normal" if connection_state is CONNECT else "disabled")

    def on_decoder_select(self, *args, **kwargs):
        clear_combobox_selection(combobox_instance=self.message_decoder_selector)
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
            # message_id = int(message_label[-5:])
            message_id = message_list_id[0]

        message_data = self.get_message_details(message_id)
        self.message_topic_label["state"] = "normal"
        self.message_topic_label.delete(1.0, tk.END)
        self.message_topic_label.insert(1.0, message_data.get("topic", ""))
        self.message_topic_label["state"] = "disabled"
        time_string = "{:.6f} - {}".format(round(message_data.get("timestamp", 0), 6),
                                           datetime.fromtimestamp(message_data.get("timestamp", 0)).strftime("%Y/%m/%d, %H:%M:%S.%f"))
        self.message_date_label["text"] = time_string
        self.message_qos_label["text"] = "QoS: {}".format(message_data.get("qos", ""))
        self.message_id_label["text"] = "ID: {}".format(message_id)
        self.message_payload_box.configure(state="normal")
        self.message_payload_box.delete(1.0, tk.END)

        if bool(self.attempt_to_decompress.get()) and 4 < len(message_data.get("payload", "")):
            payload = decompress_message(message_data["payload"])
        else:
            payload = message_data.get("payload", "")

        try:
            payload_decoded = str(payload.decode("utf-8"))
        except Exception:
            payload_decoded = payload
        decoder = self.message_decoder_selector.get()
        if decoder == "JSON pretty formatter":
            try:
                new_message_structure = json.loads(payload_decoded)
            except Exception as e:
                new_message = "        *** FAILED TO LOAD JSON ***{}{}{}{}".format(linesep+linesep,
                                                                                   e,
                                                                                   linesep+linesep,
                                                                                   traceback.format_exc())
            else:
                new_message = json.dumps(new_message_structure, indent=2, ensure_ascii=False)
            self.message_payload_box.insert(1.0, new_message)

        elif decoder == "Hex formatter":
            try:
                data_to_decode = payload_decoded.encode("utf-8")
            except Exception:
                data_to_decode = payload_decoded
            for line in hex_viewer(data_to_decode):
                self.message_payload_box.insert(tk.END, line+linesep)

        else:
            self.message_payload_box.insert(1.0, payload_decoded)
        self.message_payload_box.configure(state="disabled")

    def get_color(self, topic):
        colour = self.config_handler.get_subscription_colour(self.current_connection, topic)
        if colour is not None:
            return colour
        self.color_carousel += 1
        if self.color_carousel > len(COLOURS):
            self.color_carousel = 0
        return COLOURS[self.color_carousel]

    def add_subscription_frame(self, topic, unsubscribe_callback):
        if topic not in self.subscription_frames:
            self.subscription_frames[topic] = SubscriptionFrame(self.subscriptions_frame.viewPort,
                                                                topic,
                                                                unsubscribe_callback,
                                                                self.get_color(topic),
                                                                self.on_colour_change,
                                                                self.topic_mute_callback,
                                                                height=60)
            self.subscription_frames[topic].pack(fill=tk.X, expand=1, padx=2, pady=1)

    def topic_mute_callback(self, topic, mute_state):
        if mute_state and topic not in self.mute_patterns:
            self.mute_patterns.append(topic)
        if not mute_state and topic in self.mute_patterns:
            self.mute_patterns.remove(topic)

    def on_colour_change(self, topic, colour):
        for message_id in list(self.messages.keys()):
            if self.messages[message_id]["subscription_pattern"] == topic:
                self.incoming_messages_list.itemconfig(message_id, fg=colour)
        self.config_handler.add_subscription_history(self.current_connection, topic, colour)

    def add_subscription(self, topic=None):
        if topic is None:
            topic = self.subscribe_selector.get()
        if topic != "" and topic not in self.subscription_frames:
            self.add_subscription_frame(topic, self.on_unsubscribe)
            try:
                callback = partial(self.on_mqtt_message, subscription_pattern=topic)
                callback.__name__ = "MyCallback"  # This is to fix some weird behaviour of the paho client on linux
                self.mqtt_manager.add_subscription(topic_pattern=topic,
                                                   on_message_callback=callback)
            except Exception as e:
                self.log.exception("Failed to subscribe!", e)
                self.subscription_frames[topic].on_unsubscribe()
                return
            # self.add_subscription_frame(topic, self.on_unsubscribe)
            if self.subscribe_selector["values"] == "":
                self.subscribe_selector["values"] = [topic]
            elif topic not in self.subscribe_selector['values']:
                self.subscribe_selector['values'] += (topic,)
            self.config_handler.add_subscription_history(self.current_connection,
                                                         topic,
                                                         self.subscription_frames[topic].colour)

    def add_new_message(self, mqtt_message_object, subscription_pattern):
        timestamp = time.time()
        # Theoretically there will be no race condition here?
        new_message_id = self.message_id_counter
        self.message_id_counter += 1
        simple_time_string = datetime.fromtimestamp(round(timestamp, 3)).strftime("%H:%M:%S.%f")[:-3]
        self.messages[new_message_id] = {
            "topic": mqtt_message_object.topic,
            "payload": mqtt_message_object.payload,
            "qos": mqtt_message_object.qos,
            "subscription_pattern": subscription_pattern,
            "retained": mqtt_message_object.retain,
            "timestamp": timestamp
        }
        message_title = "{} #{:05d} [QoS:{}] [{}] - {}".format(simple_time_string,
                                                               new_message_id,
                                                               mqtt_message_object.qos,
                                                               "R" if mqtt_message_object.retain else " ",
                                                               mqtt_message_object.topic)
        try:
            colour = self.subscription_frames[subscription_pattern].colour
        except Exception as e:
            self.log.warning("Failed to add new message:", e, mqtt_message_object.topic)
        else:
            self.add_message(message_title, colour)

    def load_subscription_history(self):
        self.subscribe_selector.configure(
            values=self.config_handler.get_subscription_history_list(self.current_connection))
        self.subscribe_selector.set(self.config_handler.get_last_subscribe_used(self.current_connection))
        if self.config_handler.get_resubscribe(self.current_connection) == 1:
            topics = self.config_handler.get_resubscribe_topics(self.current_connection)
            for topic in topics:
                self.add_subscription(topic)

    def cleanup_subscriptions(self):
        current_subscriptions = []
        for topic in list(self.subscription_frames.keys()):
            current_subscriptions.append(topic)
            self.subscription_frames[topic].pack_forget()
            self.subscription_frames[topic].destroy()
        if self.config_handler.get_resubscribe(self.current_connection) == 1:
            self.config_handler.save_resubscribe_topics(self.current_connection, current_subscriptions)
        self.subscription_frames = {}

    def on_mqtt_message(self, _, __, msg, subscription_pattern):
        if self.exporting:
            return
        if subscription_pattern in self.mute_patterns:
            return
        self.add_new_message(mqtt_message_object=msg,
                             subscription_pattern=subscription_pattern)

    def get_message_details(self, message_id):
        return self.messages.get(message_id, {})

    def on_unsubscribe(self, topic):
        self.subscription_frames.pop(topic, None)
        try:
            self.mqtt_manager.unsubscribe(topic)
        except Exception as e:
            self.log.warning("Failed to unsubscribe", topic, "maybe a failed subscription?")

    def flush_messages(self):
        self.message_id_counter = 0
        self.incoming_messages_list.delete(0, "end")
        self.messages = {}
        self.on_message_select()

    def message_list_length(self):
        return len(self.messages)

    def get_selected_message_payload(self):
        try:
            message_list_id = self.incoming_messages_list.curselection()
            message_id = message_list_id[0]
            message_data = self.get_message_details(message_id)["payload"]
        except Exception as e:
            return None
        return message_data

    def get_messages(self, base64_only):
        self.exporting = True
        for message in self.messages.values():
            message_to_export = deepcopy(message)
            if base64_only:
                message_to_export["payload"] = base64.b64encode(message_to_export["payload"]).decode("utf-8")
                yield message_to_export
                continue
            try:
                message_to_export["payload"] = message_to_export["payload"].decode("utf-8")
            except Exception:
                message_to_export["payload"] = base64.b64encode(message_to_export["payload"]).decode("utf-8")
            yield message_to_export
        self.exporting = False
