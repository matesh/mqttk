import tkinter as tk
import tkinter.ttk as ttk
from mqttk.constants import CONNECT
from functools import partial
import os
import traceback


class BrokerStats(ttk.Frame):
    def __init__(self, master, root, log, *args, **kwargs):
        super().__init__(master=master, *args, **kwargs)

        self.root = root
        self.mqtt_manager = None
        self.log = log

        self.header_frame = ttk.Frame(self)

        self.subscribe_button = ttk.Button(self.header_frame,
                                           text="Subscribe",
                                           command=self.subscribe,
                                           state='disabled')
        self.subscribe_button.pack(side=tk.RIGHT, pady=3, padx=3)

        self.unsubscribe_button = ttk.Button(self.header_frame,
                                             text="Unsubscribe",
                                             command=self.unsubscribe,
                                             state='disabled')
        self.unsubscribe_button.pack(side=tk.RIGHT, pady=3, padx=3)

        self.header_frame.pack(fill="x", padx=3, pady=3)

        self.broker_stats_frame = ttk.Frame(self)
        self.broker_stats_frame.pack(fill='both', expand=1)
        self.broker_stats_treeview = ttk.Treeview(self.broker_stats_frame,
                                                  show="tree headings",
                                                  columns=('value',))
        self.vertical_scrollbar = ttk.Scrollbar(self.broker_stats_frame, orient="vertical",
                                                command=self.broker_stats_treeview.yview)
        self.vertical_scrollbar.pack(side=tk.RIGHT, fill="y")
        self.broker_stats_treeview.configure(yscrollcommand=self.vertical_scrollbar.set)
        self.broker_stats_treeview.pack(fill='both',
                                        expand=1)
        self.broker_stats_treeview.heading('#0', text="Statistic")
        self.broker_stats_treeview.column('#0', minwidth=300, width=300, stretch=tk.NO)
        self.broker_stats_treeview.heading("value", text="Value")
        self.broker_stats_treeview.column('value', minwidth=200, width=200, stretch=tk.NO)

    def subscribe(self, *args, **kwargs):
        try:
            callback = partial(self.on_mqtt_message, subscription_pattern='$SYS/broker/#')
            callback.__name__ = "MyCallback"  # This is to fix some weird behaviour of the paho client on linux
            self.mqtt_manager.add_subscription(topic_pattern='$SYS/broker/#',
                                               on_message_callback=callback)
        except Exception as e:
            self.log.exception("Failed to subscribe!", e)
            return

        self.subscribe_button["state"] = "disabled"
        self.unsubscribe_button["state"] = "normal"

    def unsubscribe(self, *args, **kwargs):
        try:
            self.mqtt_manager.unsubscribe('$SYS/broker/#')
        except Exception as e:
            self.log.warning("Broker stats failed to unsubscribe", "maybe a failed subscription?")
        self.unsubscribe_button["state"] = "disabled"
        self.subscribe_button["state"] = "normal"
        self.flush_messages()

    def on_mqtt_message(self, _, __, msg, subscription_pattern):
        try:
            try:
                payload_decoded = str(msg.payload.decode("utf-8"))
            except Exception:
                payload_decoded = msg.payload

            topic_split = msg.topic.split("/")[2:]

            if 1 < len(topic_split):
                if topic_split[0] not in self.broker_stats_treeview.get_children(""):
                    try:
                        self.broker_stats_treeview.insert("", "end", topic_split[0], text=topic_split[0])
                    except Exception:
                        print(msg.topic, topic_split[0], self.broker_stats_treeview.get_children(""))
                        raise
                for i in range(1, len(topic_split) - 1):
                    parent_topic = "/".join(topic_split[0:i])
                    topic = "/".join(topic_split[0:i + 1])
                    if topic not in self.broker_stats_treeview.get_children(parent_topic):
                        self.broker_stats_treeview.insert(parent_topic, "end", topic, text=topic_split[i])

            parent_topic = "/".join(topic_split[0:-1])
            topic = "/".join(topic_split)
            if topic not in self.broker_stats_treeview.get_children(parent_topic):
                self.broker_stats_treeview.insert(parent_topic,
                                                  "end",
                                                  "/".join(topic_split),
                                                  text=topic_split[-1],
                                                  values=(payload_decoded,))
            else:
                self.broker_stats_treeview.set(topic, "value", payload_decoded)

        except Exception as e:
            self.log.exception("Exception inserting new message to treeview",
                               os.linesep, msg.topic, msg.payload, os.linesep, e, traceback.format_exc())

    def interface_toggle(self, connection_state, mqtt_manager):
        # Subscribe tab items
        self.mqtt_manager = mqtt_manager
        self.subscribe_button.configure(state="normal" if connection_state is CONNECT else "disabled")

    def flush_messages(self):
        for child in self.broker_stats_treeview.get_children():
            self.broker_stats_treeview.delete(child)
