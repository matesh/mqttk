import traceback
from datetime import datetime
from functools import partial
try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk
    from tkinter.scrolledtext import ScrolledText

try:
    import ttk
    py3 = False
except ImportError:
    import tkinter.ttk as ttk
    py3 = True

import sys
import time
from mqttk.widgets import ScrollFrame, SubscriptionFrame, MessageFrame
from mqttk.dialogs import AboutDialog
from mqttk.configuration_dialog import ConfigurationWindow
from mqttk.config_handler import ConfigHandler
from mqttk.MQTT_manager import MqttManager

CONNECT = "connected"
DISCONNECT = "disconnected"


class App:
    def __init__(self, root):
        try:
            self.config_handler = ConfigHandler()
        except AssertionError:
            print("Invalid platform")
            #TODO Whatever notification or no save or dunno

        self.subscription_frames = {}
        self.message_id_counter = 0
        self.currently_selected_message = 0
        self.last_used_connection = None
        self.mqtt_manager = None
        self.current_connection_configuration = None

        #Holds messages and relevant stuff
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

        #setting title
        root.title("MQTTk")

        screenwidth = root.winfo_screenwidth()
        screenheight = root.winfo_screenheight()
        saved_geometry = self.config_handler.get_window_geometry()
        out_of_bounds = True
        if saved_geometry is not None:
            out_of_bounds = bool(screenwidth < int(saved_geometry.split("+")[1]) or screenheight < int(
                saved_geometry.split("+")[2]))

        #setting window size
        if out_of_bounds:
            width = 1026
            height = 707
            alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
            root.geometry(alignstr)
        else:
            root.geometry(saved_geometry)

        root.protocol("WM_DELETE_WINDOW", self.on_destroy)

        root.resizable(width=True, height=True)
        self.icon_small = tk.PhotoImage(file="mqttk_small.png")
        self.icon = tk.PhotoImage(file="mqttk.png")
        self.root = root
        self.root.iconphoto(False, self.icon)
        self.root.option_add('*tearOff', tk.FALSE)

        self.style = ttk.Style()
        if sys.platform == "win32":
            self.style.theme_use('winnative')
        if sys.platform == "darwin":
            self.style.theme_use("default") # aqua, clam, alt, default, classic

        self.style.configure("New.TFrame", background="#b3ffb5")
        self.style.configure("New.TLabel", background="#b3ffb5")
        self.style.configure("Selected.TFrame", background="#96bfff")
        self.style.configure("Selected.TLabel", background="#96bfff")
        self.style.configure("Retained.TLabel", background="#ffeeab")

        # ==================================== Menu bar ===============================================================
        self.menubar = tk.Menu(root)
        self.root.config(menu=self.menubar)
        self.file_menu = tk.Menu(self.menubar)
        self.about_menu = tk.Menu(self.menubar)
        self.menubar.add_cascade(menu=self.file_menu, label="File")
        self.menubar.add_cascade(menu=self.about_menu, label="About")
        self.file_menu.add_command(label="Exit", command=self.on_exit)
        self.about_menu.add_command(label="About", command=self.on_about_menu)

        self.main_window_frame = ttk.Frame(root)
        self.main_window_frame.pack(fill='both', expand=1)

        # ==================================== Header frame ===========================================================
        self.header_frame = ttk.Frame(self.main_window_frame, height=35)
        self.header_frame.pack(anchor="w", side=tk.TOP, fill=tk.Y, padx=3, pady=3)

        self.connection_selector = ttk.Combobox(self.header_frame, width=30)
        self.connection_selector.pack(side=tk.LEFT, padx=3, pady=3)
        self.connection_selector.configure(state="readonly")
        self.on_config_update()
        self.config_window_button = ttk.Button(self.header_frame, width=10)
        self.config_window_button["text"] = "Configure"
        self.config_window_button.pack(side=tk.LEFT, expand=False, padx=3, pady=3)
        self.config_window_button["command"] = self.spawn_configuration_window
        self.connect_button = ttk.Button(self.header_frame, width=10)
        self.connect_button["text"] = "Connect"
        self.connect_button["command"] = self.on_connect_button
        self.connect_button.pack(side=tk.LEFT, expand=False, padx=3, pady=3)
        self.disconnect_button = ttk.Button(self.header_frame, width=10)
        self.disconnect_button["text"] = "Disconnect"
        self.disconnect_button["state"] = "disabled"
        self.disconnect_button["command"] = self.on_disconnect_button
        self.disconnect_button.pack(side=tk.LEFT, expand=False, padx=3, pady=3)

        self.tabs = ttk.Notebook(self.main_window_frame)
        self.tabs.pack(anchor="nw", fill="both", expand=True, padx=3, pady=3)

        # ==================================== Subscribe tab ==========================================================

        self.subscribe_frame = ttk.Frame(self.tabs)
        self.tabs.add(self.subscribe_frame, text="Subscribe")

        # Subscribe frame
        self.subscribe_bar_frame = ttk.Frame(self.subscribe_frame, height=1)
        self.subscribe_bar_frame.pack(anchor="nw", side=tk.TOP, fill=tk.Y)
        # Subscribe selector combobox
        self.subscribe_selector = ttk.Combobox(self.subscribe_bar_frame, width=30)
        self.subscribe_selector.pack(side=tk.LEFT, padx=3, pady=3)
        self.subscribe_selector["values"] = []
        # Subscribe button
        self.subscribe_button = ttk.Button(self.subscribe_bar_frame, width=10)
        self.subscribe_button.pack(side=tk.LEFT, padx=3, pady=3)
        self.subscribe_button["text"] = "Subscribe"
        self.subscribe_button["command"] = self.add_subscription

        # Subscribe bottom part frame
        self.subscribe_tab_bottom_frame = ttk.Frame(self.subscribe_frame)
        self.subscribe_tab_bottom_frame.pack(fill="both", anchor="w", expand=True, padx=3, pady=3)

        # Subscriptions scrollable frame
        # self.subscriptions_frame = ScrollableFrame(self.subscribe_tab_bottom_frame)
        self.subscriptions_frame = ScrollFrame(self.subscribe_tab_bottom_frame)
        self.subscriptions_frame.pack(fill="y", side=tk.LEFT)
        # Incoming message resizable panel
        self.message_paned_window = tk.PanedWindow(self.subscribe_tab_bottom_frame,
                                                   orient=tk.VERTICAL,
                                                   sashrelief="groove",
                                                   sashwidth=6,
                                                   sashpad=2)
        self.message_paned_window.pack(fill='both', padx=3, pady=3, expand=1)
        # Incoming messages scrollable frame
        self.incoming_messages = ScrollFrame(self.subscribe_tab_bottom_frame)
        self.incoming_messages.pack()
        self.message_paned_window.add(self.incoming_messages)

        # Message content frame
        self.message_content_frame = ttk.Frame(self.subscribe_tab_bottom_frame)
        self.message_content_frame.pack(anchor="n", expand=True, fill="both")
        self.message_paned_window.add(self.message_content_frame)

        # Message topic and ID frame
        self.message_topic_and_id_frame = ttk.Frame(self.message_content_frame)
        self.message_topic_and_id_frame.pack(fill="x")
        # Message topic label
        self.message_topic_label = tk.Text(self.message_topic_and_id_frame, height=1, borderwidth=0, state="disabled")
        self.message_topic_label.pack(side=tk.LEFT, padx=3, pady=3, fill="x", expand=1)
        # Message ID label
        self.message_id_label = ttk.Label(self.message_topic_and_id_frame, width=5)
        self.message_id_label["text"] = "ID"
        self.message_id_label.pack(side=tk.RIGHT, padx=3, pady=3)

        # Message date frame
        self.message_date_and_qos_frame = ttk.Frame(self.message_content_frame)
        self.message_date_and_qos_frame.pack(fill="x")
        # Message date label
        self.message_date_label = ttk.Label(self.message_date_and_qos_frame)
        self.message_date_label["text"] = "DATE"
        self.message_date_label.pack(side=tk.LEFT, fill="x", padx=3, pady=3)
        # Message QoS label
        self.message_qos_label = ttk.Label(self.message_date_and_qos_frame, width=5)
        self.message_qos_label["text"] = "QOS"
        self.message_qos_label.pack(side=tk.RIGHT, padx=3, pady=3)
        # Message Payload
        self.message_payload_box = ScrolledText(self.message_content_frame)
        self.message_payload_box.pack(fill="both", expand=True)
        self.message_payload_box.configure(state="disabled")

        # ====================================== Publish tab =========================================================

        self.publish_frame = ttk.Frame(self.tabs)
        self.tabs.add(self.publish_frame, text="Publish")

        self.fos = SubscriptionFrame(self.publish_frame, "Pocs")
        self.fos.place(x=3, y=3, width=400, height=400)

        self.content_interface_toggle(DISCONNECT)
        self.config_interface_toggle(DISCONNECT)

        # TEST MESSAGE GENERATION
        # for i in range(1, 10):
        #     topic = "TESTTOPIC_{}".format(i)
        #     content = "testcontent{}".format(i)
        #     retained = True if i % 2 == 0 else False
        #     self.add_new_message(MQTTMESSAGETEMPLATE(topic, content, i, retained), "whateverpattern")

    def on_client_disconnect(self):
        self.cleanup_subscriptions()
        self.content_interface_toggle(DISCONNECT)
        self.config_interface_toggle(DISCONNECT)

    def on_client_connect(self):
        self.content_interface_toggle(CONNECT)
        #TODO connection indicator

    def on_connect_button(self):
        self.config_interface_toggle(CONNECT)
        self.current_connection_configuration = self.config_handler.get_connection_config_dict(self.connection_selector.get())
        try:
            self.mqtt_manager = MqttManager(self.current_connection_configuration["connection_parameters"],
                                            self.on_client_connect,
                                            self.on_client_disconnect)
        except Exception as e:
            print("Failed to initialise MQTT client:", e)
            traceback.print_exc()
            self.config_interface_toggle(DISCONNECT)

        self.subscribe_selector.configure(values=self.current_connection_configuration.get("subscriptions", []))

    def on_disconnect_button(self):
        self.mqtt_manager.disconnect()

    def add_subscription(self):
        topic = self.subscribe_selector.get()
        if topic != "":
            self.add_subscription_frame(topic, self.on_unsubscribe)
            print(self.subscribe_selector["values"])
            if self.subscribe_selector["values"] == "":
                self.subscribe_selector["values"] = [topic]
            elif topic not in self.subscribe_selector['values']:
                self.subscribe_selector['values'] += (topic,)
            self.config_handler.add_subscription_history(self.connection_selector.get(), topic)
            self.mqtt_manager.add_subscription(topic, partial(self.on_mqtt_message, subscription_pattern=topic))

    def add_subscription_frame(self, topic, unsubscribe_callback):
        if topic not in self.subscription_frames:
            # SubscriptionFrame(self.subscriptions_frame.scrollable_frame,
            self.subscription_frames[topic] = SubscriptionFrame(self.subscriptions_frame.viewPort,
                                                                topic,
                                                                unsubscribe_callback,
                                                                height=60,
                                                                # width=self.subscriptions_frame.winfo_width()-10).pack()
                                                                )
            self.subscription_frames[topic].pack(fill=tk.X, expand=1, padx=2, pady=1)

    def on_message_select(self, message_id):
        print("Message selected", message_id)
        if message_id != self.currently_selected_message:
            try:
                self.messages[self.currently_selected_message]["message_list_instance_ref"].on_unselect()
            except Exception as e:
                print("Exception deselecting message", e)
            self.currently_selected_message = message_id
            self.message_topic_label["state"] = "normal"
            self.message_topic_label.delete(1.0, tk.END)
            self.message_topic_label.insert(1.0, self.messages[message_id]["topic"])
            self.message_topic_label["state"] = "disabled"
            self.message_date_label["text"] = self.messages[message_id]["time_string"]
            self.message_qos_label["text"] = "QoS: {}".format(self.messages[message_id]["qos"])
            self.message_id_label["text"] = "ID: {}".format(message_id)
            self.message_payload_box.configure(state="normal")
            self.message_payload_box.delete(1.0, tk.END)
            self.message_payload_box.insert(1.0, self.messages[message_id]["payload"])
            self.message_payload_box.configure(state="disabled")

    def on_unsubscribe(self, topic):
        self.subscription_frames.pop(topic, None)
        #MQTT handler unsub call

    def add_new_message(self, mqtt_message_object, subscription_pattern):
        timestamp = time.time()
        # Theoretically there will be no race condition here?
        self.message_id_counter += 1
        time_string = "{:.6f} - {}".format(round(timestamp, 6), datetime.fromtimestamp(timestamp).strftime("%Y/%m/%d, %H:%M:%S.%f"))
        self.messages[self.message_id_counter] = {
            "topic": mqtt_message_object.topic,
            "payload": mqtt_message_object.payload,
            "qos": mqtt_message_object.qos,
            "subscription_pattern": subscription_pattern,
            "time_string": time_string,
            "retained": mqtt_message_object.retain
        }
        self.messages[self.message_id_counter]["message_list_instance_ref"] = MessageFrame(self.incoming_messages.viewPort,
                                                                                           self.message_id_counter,
                                                                                           mqtt_message_object.topic,
                                                                                           time_string,
                                                                                           subscription_pattern,
                                                                                           mqtt_message_object.qos,
                                                                                           mqtt_message_object.retain,
                                                                                           self.on_message_select,
                                                                                           height=40,
                                                                                           takefocus=True)
        self.messages[self.message_id_counter]["message_list_instance_ref"].pack(fill=tk.X, expand=1, padx=2, pady=1)

    def on_mqtt_message(self, client, userdata, msg, subscription_pattern):
        self.add_new_message(msg, subscription_pattern)

    def on_config_update(self):
        connection_profile_list = sorted(self.config_handler.get_connection_profiles())
        if len(connection_profile_list) != 0:
            self.connection_selector.configure(values=connection_profile_list)
            if self.config_handler.get_last_used_connection() in connection_profile_list:
                self.connection_selector.current(connection_profile_list.index(self.config_handler.get_last_used_connection()))
            else:
                self.connection_selector.current(0)

    def config_interface_toggle(self, connection_state):
        # Top menu items
        self.connection_selector.configure(state="disabled" if connection_state is CONNECT else "readonly")
        self.config_window_button.configure(state="disabled" if connection_state is CONNECT else "normal")
        self.connect_button.configure(state="disabled" if connection_state is CONNECT else "normal")
        self.disconnect_button.configure(state="normal" if connection_state is CONNECT else "disabled")

    def content_interface_toggle(self, connection_state):
        # Subscribe tab items
        self.subscribe_button.configure(state="normal" if connection_state is CONNECT else "disabled")
        self.subscribe_selector.configure(state="normal" if connection_state is CONNECT else "disabled")

        # Publish tab items

    def cleanup_subscriptions(self):
        for topic in list(self.subscription_frames.keys()):
            self.subscription_frames[topic].pack_forget()
            self.subscription_frames[topic].destroy()
        self.subscription_frames = {}

    def spawn_configuration_window(self):
        configuration_window = ConfigurationWindow(self.root, self.config_handler, self.on_config_update)
        configuration_window.transient(self.root)
        configuration_window.wait_visibility()
        configuration_window.grab_set()
        configuration_window.wait_window()

    def on_about_menu(self):
        about_window = AboutDialog(self.root, self.icon_small)
        about_window.transient(self.root)
        about_window.wait_visibility()
        about_window.grab_set()
        about_window.wait_window()

    def on_exit(self):
        self.config_handler.save_window_geometry(self.root.geometry())
        exit(0)

    def on_destroy(self):
        self.config_handler.save_window_geometry(self.root.geometry())
        root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    # sns_config_support.set_Tk_var()
    app = App(root)
    # sns_config_support.init(root, top)
    # root.after(2000, add_shit)
    root.mainloop()

