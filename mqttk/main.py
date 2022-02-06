import traceback
from datetime import datetime
from functools import partial
import tkinter as tk

import tkinter.ttk as ttk

import sys
import time
from widgets import SubscriptionFrame, HeaderFrame, SubscribeTab, PublishTab, CONNECT, DISCONNECT
from dialogs import AboutDialog
from configuration_dialog import ConfigurationWindow
from config_handler import ConfigHandler
from MQTT_manager import MqttManager



COLOURS = ['#00aedb', '#28b463', '#a569bd', '#41ead4', '#e8f8c1', '#d6ccf9', '#74a3f4',
           '#5e999a', '#885053', '#009b0a']


class App:
    def __init__(self, root):
        try:
            self.config_handler = ConfigHandler()
        except AssertionError:
            print("Invalid platform")
            #TODO Whatever notification or no save or dunno

        self.subscription_frames = {}
        self.message_id_counter = 0
        self.last_used_connection = None
        self.mqtt_manager = None
        self.current_connection_configuration = None
        self.autoscroll = self.config_handler.get_autoscroll()
        self.color_carousel = -1
        self.style_ids = 0

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

        root.title("MQTTk")

        # Restore window size and position, if not available or out of bounds, reset to default
        screenwidth = root.winfo_screenwidth()
        screenheight = root.winfo_screenheight()
        saved_geometry = self.config_handler.get_window_geometry()
        out_of_bounds = True
        if saved_geometry is not None:
            out_of_bounds = bool(screenwidth < int(saved_geometry.split("+")[1]) or screenheight < int(
                saved_geometry.split("+")[2]))

        if out_of_bounds:
            width = 1300
            height = 900
            alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
            root.geometry(alignstr)
        else:
            root.geometry(saved_geometry)
        root.protocol("WM_DELETE_WINDOW", self.on_destroy)
        root.resizable(width=True, height=True)

        # App icon stuff
        self.icon_small = tk.PhotoImage(file="mqttk_small.png")
        self.icon = tk.PhotoImage(file="mqttk.png")
        self.root = root
        self.root.iconphoto(False, self.icon)
        self.root.option_add('*tearOff', tk.FALSE)

        # Some minimal styling stuff
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
        self.style.configure("Pressed.TButton", relief="sunken")

        # ==================================== Menu bar ===============================================================
        self.menubar = tk.Menu(root)
        self.root.config(menu=self.menubar)
        self.file_menu = tk.Menu(self.menubar)
        self.about_menu = tk.Menu(self.menubar)
        self.menubar.add_cascade(menu=self.file_menu, label="File")
        self.menubar.add_cascade(menu=self.about_menu, label="Help")
        self.file_menu.add_command(label="Exit", command=self.on_exit)
        self.about_menu.add_command(label="About", command=self.on_about_menu)

        self.main_window_frame = ttk.Frame(root)
        self.main_window_frame.pack(fill='both', expand=1)

        # ==================================== Header frame ===========================================================
        self.header_frame = HeaderFrame(self.main_window_frame, self, height=35)
        self.header_frame.pack(anchor="w", side=tk.TOP, fill=tk.Y, padx=3, pady=3)

        self.tabs = ttk.Notebook(self.main_window_frame)
        self.tabs.pack(anchor="nw", fill="both", expand=True, padx=3, pady=3)

        self.on_config_update()

        # ==================================== Subscribe tab ==========================================================

        self.subscribe_frame = SubscribeTab(self.tabs, self)
        self.tabs.add(self.subscribe_frame, text="Subscribe")

        # ====================================== Publish tab =========================================================

        self.publish_frame = PublishTab(self.tabs, self)
        self.tabs.add(self.publish_frame, text="Publish")

        self.subscribe_frame.interface_toggle(DISCONNECT)
        self.header_frame.interface_toggle(DISCONNECT)
        self.publish_frame.interface_toggle(DISCONNECT)

    def on_client_disconnect(self):
        self.cleanup_subscriptions()
        try:
            self.subscribe_frame.interface_toggle(DISCONNECT)
            self.header_frame.interface_toggle(DISCONNECT)
            self.publish_frame.interface_toggle(DISCONNECT)
        except Exception as e:
            print("Failed to toggle user interface element!", e)

    def on_client_connect(self):
        self.subscribe_frame.interface_toggle(CONNECT)
        self.publish_frame.interface_toggle(CONNECT, self.header_frame.connection_selector.get())
        #TODO connection indicator

    def on_connect_button(self):
        self.current_connection_configuration = self.config_handler.get_connection_config_dict(
            self.header_frame.connection_selector.get())
        if not self.current_connection_configuration:
            return
        self.header_frame.interface_toggle(CONNECT)
        try:
            self.mqtt_manager = MqttManager(self.current_connection_configuration["connection_parameters"],
                                            self.on_client_connect,
                                            self.on_client_disconnect)
        except Exception as e:
            print("Failed to initialise MQTT client:", e)
            traceback.print_exc()
            self.header_frame.interface_toggle(DISCONNECT)
            self.publish_frame.interface_toggle(DISCONNECT)

        self.subscribe_frame.subscribe_selector.configure(values=self.current_connection_configuration.get("subscriptions", []))
        self.subscribe_frame.subscribe_selector.set(self.config_handler.get_last_subscribe_used(self.header_frame.connection_selector.get()))

    def on_publish(self, topic, payload, qos, retained):
        if self.mqtt_manager is not None:
            self.mqtt_manager.publish(topic, payload, qos, retained)

    def on_disconnect_button(self):
        if self.mqtt_manager is not None:
            self.mqtt_manager.disconnect()

    def add_subscription(self):
        topic = self.subscribe_frame.subscribe_selector.get()
        if topic != "" and topic not in self.subscription_frames:
            self.style_ids += 1
            style_id = "subscription{}.TLabel".format(self.style_ids)
            try:
                self.mqtt_manager.add_subscription(topic_pattern=topic,
                                                   on_message_callback=partial(self.on_mqtt_message,
                                                                               subscription_pattern=topic))
            except Exception:
                print("Failed to subscribe")
                return
            self.add_subscription_frame(topic, self.on_unsubscribe, style_id)
            if self.subscribe_frame.subscribe_selector["values"] == "":
                self.subscribe_frame.subscribe_selector["values"] = [topic]
            elif topic not in self.subscribe_frame.subscribe_selector['values']:
                self.subscribe_frame.subscribe_selector['values'] += (topic,)
            self.config_handler.add_subscription_history(self.header_frame.connection_selector.get(), topic)

    def add_subscription_frame(self, topic, unsubscribe_callback, style_id):
        if topic not in self.subscription_frames:

            self.subscription_frames[topic] = SubscriptionFrame(self.subscribe_frame.subscriptions_frame.viewPort,
                                                                topic,
                                                                unsubscribe_callback,
                                                                self.get_color(),
                                                                self.on_colour_change,
                                                                height=60)
            self.subscription_frames[topic].pack(fill=tk.X, expand=1, padx=2, pady=1)

    def get_message_details(self, message_id):
        return self.messages.get(message_id, {})

    def on_unsubscribe(self, topic):
        self.subscription_frames.pop(topic, None)
        self.mqtt_manager.unsubscribe(topic)

    def add_new_message(self, mqtt_message_object, subscription_pattern):
        timestamp = time.time()
        # Theoretically there will be no race condition here?
        new_message_id = self.message_id_counter
        self.message_id_counter += 1
        time_string = "{:.6f} - {}".format(round(timestamp, 6), datetime.fromtimestamp(timestamp).strftime("%Y/%m/%d, %H:%M:%S.%f"))
        simple_time_string = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S.%f")
        self.messages[new_message_id] = {
            "topic": mqtt_message_object.topic,
            "payload": mqtt_message_object.payload,
            "qos": mqtt_message_object.qos,
            "subscription_pattern": subscription_pattern,
            "time_string": time_string,
            "retained": mqtt_message_object.retain
        }
        message_title = "{}  -  {:70} {:8} QoS: {} #{:05d}".format(simple_time_string,
                                                                   mqtt_message_object.topic,
                                                                   "RETAINED" if mqtt_message_object.retain else "",
                                                                   mqtt_message_object.qos,
                                                                   new_message_id)

        colour = self.subscription_frames[subscription_pattern].colour
        self.subscribe_frame.add_message(message_title, colour, self.autoscroll)

    def on_mqtt_message(self, client, userdata, msg, subscription_pattern):
        self.add_new_message(mqtt_message_object=msg,
                             subscription_pattern=subscription_pattern)

    def on_config_update(self):
        connection_profile_list = sorted(self.config_handler.get_connection_profiles())
        if len(connection_profile_list) != 0:
            self.header_frame.connection_selector.configure(values=connection_profile_list)
            if self.config_handler.get_last_used_connection() in connection_profile_list:
                self.header_frame.connection_selector.current(connection_profile_list.index(self.config_handler.get_last_used_connection()))
            else:
                self.header_frame.connection_selector.current(0)

    def cleanup_subscriptions(self):
        for topic in list(self.subscription_frames.keys()):
            self.subscription_frames[topic].pack_forget()
            self.subscription_frames[topic].destroy()
        self.subscription_frames = {}

    def flush_messages(self):
        self.message_id_counter = 0
        self.messages = {}
        self.subscribe_frame.flush_messages()

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

    def get_color(self):
        self.color_carousel += 1
        if self.color_carousel > len(COLOURS):
            self.color_carousel = 0
        return COLOURS[self.color_carousel]

    def on_colour_change(self):
        for message_id in list(self.messages.keys()):
            try:
                subscription_frame = self.subscription_frames.get(self.messages[message_id]["subscription_pattern"], None)
                if subscription_frame is not None:
                    self.subscribe_frame.incoming_messages_list.itemconfig(message_id, bg=subscription_frame.colour)
            except Exception as e:
                print("Failed to chanage message colour", e)

    def autoscroll_toggle(self):
        self.autoscroll = not self.autoscroll
        self.subscribe_frame.autoscroll_button.configure(style="Pressed.TButton" if self.autoscroll else "TButton")

    def on_exit(self):
        self.on_disconnect_button()
        self.config_handler.save_window_geometry(self.root.geometry())
        self.config_handler.save_autoscroll(self.autoscroll)
        root.after(100, root.destroy())
        # root.destroy()

    def on_destroy(self):
        self.on_exit()


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()

