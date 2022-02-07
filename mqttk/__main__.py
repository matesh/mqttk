import os
import traceback
from datetime import datetime
from functools import partial
import tkinter as tk
import tkinter.ttk as ttk
import sys
import time
from mqttk.widgets import SubscriptionFrame, HeaderFrame, SubscribeTab, PublishTab, CONNECT, DISCONNECT, LogTab
from mqttk.dialogs import AboutDialog, SplashScreen
from mqttk.configuration_dialog import ConfigurationWindow
from mqttk.config_handler import ConfigHandler
from mqttk.MQTT_manager import MqttManager
from paho.mqtt.client import MQTT_LOG_ERR, MQTT_LOG_INFO, MQTT_LOG_NOTICE, MQTT_LOG_WARNING


COLOURS = ['#00aedb', '#28b463', '#a569bd', '#41ead4', '#e8f8c1', '#d6ccf9', '#74a3f4',
           '#5e999a', '#885053', '#009b0a']

root = tk.Tk()


class PotatoLog:
    def __init__(self):
        self.add_message_callback = None
        self.message_queue = []

    def add_message(self, message_level, *args):
        message = "{} - {} ".format(datetime.now().strftime("%H:%M:%S.%f"), message_level)
        message += ", ".join([str(x) for x in args])
        message += os.linesep
        if self.add_message_callback is None:
            self.message_queue.append(message)
        else:
            if len(self.message_queue) != 0:
                for queued_message in self.message_queue:
                    self.add_message_callback(queued_message)
                self.message_queue = []
            self.add_message_callback(message)

    def warning(self, *args):
        message_level = "[W]"
        self.add_message(message_level, *args)

    def error(self, *args):
        message_level = "[E]"
        self.add_message(message_level, *args)

    def exception(self, *args):
        message_level = "[X]"
        self.add_message(message_level, *args)

    def info(self, *args):
        message_level = "[i]"
        self.add_message(message_level, *args)

    def on_paho_log(self, _, __, level, buf):
        if level == MQTT_LOG_INFO:
            self.info("[M] " + buf)
        elif level == MQTT_LOG_NOTICE:
            self.info("[M] " + buf)
        elif level == MQTT_LOG_WARNING:
            self.warning("[M] " + buf)
        elif level == MQTT_LOG_ERR:
            self.error("[M] " + buf)


class App:
    def __init__(self, root):
        self.log = PotatoLog()
        self.config_handler = ConfigHandler(self.log)

        self.subscription_frames = {}
        self.message_id_counter = 0
        self.last_used_connection = None
        self.mqtt_manager = None
        self.current_connection_configuration = None
        self.color_carousel = -1
        self.mute_patterns = []

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
        current_dir = os.path.join(os.path.dirname(__file__))
        self.icon_small = tk.PhotoImage(file=os.path.join(current_dir, "mqttk_small.png"))
        self.icon = tk.PhotoImage(file=os.path.join(current_dir, "mqttk.png"))
        self.splash_icon = tk.PhotoImage(file=os.path.join(current_dir, "mqttk_splash.png"))
        root.withdraw()
        splash_screen = SplashScreen(root, self.splash_icon)
        time.sleep(2)
        splash_screen.destroy()
        root.deiconify()
        self.root = root
        self.root.iconphoto(False, self.icon)
        self.root.option_add('*tearOff', tk.FALSE)

        # Some minimal styling stuff
        self.style = ttk.Style()
        if sys.platform == "win32":
            self.style.theme_use('winnative')
        if sys.platform == "darwin":
            self.style.theme_use("default")  # aqua, clam, alt, default, classic
        self.style.configure("New.TFrame", background="#b3ffb5")
        self.style.configure("New.TLabel", background="#b3ffb5")
        self.style.configure("Selected.TFrame", background="#96bfff")
        self.style.configure("Selected.TLabel", background="#96bfff")
        self.style.configure("Retained.TLabel", background="#ffeeab")

        # ==================================== Menu bar ===============================================================
        self.menubar = tk.Menu(root, background=self.style.lookup("TLabel", "background"),
                               foreground=self.style.lookup("TLabel", "foreground"))
        self.root.config(menu=self.menubar)
        self.file_menu = tk.Menu(self.menubar, background=self.style.lookup("TLabel", "background"),
                                 foreground=self.style.lookup("TLabel", "foreground"))
        self.about_menu = tk.Menu(self.menubar)
        self.menubar.add_cascade(menu=self.file_menu, label="File")
        self.menubar.add_cascade(menu=self.about_menu, label="Help")
        self.file_menu.add_command(label="Exit", command=self.on_exit)
        self.about_menu.add_command(label="About", command=self.on_about_menu)

        self.main_window_frame = ttk.Frame(root)
        self.main_window_frame.pack(fill='both', expand=1)

        # ==================================== Header frame ===========================================================
        self.header_frame = HeaderFrame(self.main_window_frame, self, height=35)
        self.header_frame.pack(anchor="w", side=tk.TOP, fill=tk.X, padx=3, pady=3)

        self.tabs = ttk.Notebook(self.main_window_frame)
        self.tabs.pack(anchor="nw", fill="both", expand=True, padx=3, pady=3)

        self.on_config_update()

        # ==================================== Subscribe tab ==========================================================

        self.subscribe_frame = SubscribeTab(self.tabs, self, self.log, self.style)
        self.tabs.add(self.subscribe_frame, text="Subscribe")
        self.subscribe_frame.autoscroll_state.set(int(self.config_handler.get_autoscroll()))

        # ====================================== Publish tab =========================================================

        self.publish_frame = PublishTab(self.tabs, self, self.log, self.style)
        self.tabs.add(self.publish_frame, text="Publish")

        # ====================================== Log tab =========================================================

        self.log_tab = LogTab(self.tabs)
        self.tabs.add(self.log_tab, text="Log")
        self.log.add_message_callback = self.log_tab.add_message
        self.log.info("Logger output live")

        self.subscribe_frame.interface_toggle(DISCONNECT)
        self.header_frame.interface_toggle(DISCONNECT)
        self.publish_frame.interface_toggle(DISCONNECT)

    def on_client_disconnect(self, notify=None):
        if notify is not None:
            self.header_frame.connection_error_notification["text"] = notify
        self.cleanup_subscriptions()
        try:
            self.subscribe_frame.interface_toggle(DISCONNECT)
            self.header_frame.interface_toggle(DISCONNECT)
            self.publish_frame.interface_toggle(DISCONNECT)
            self.header_frame.connection_indicator_toggle(DISCONNECT)
        except Exception as e:
            self.log.exception("Failed to toggle user interface element!", e)

    def on_client_connect(self):
        self.subscribe_frame.interface_toggle(CONNECT)
        self.publish_frame.interface_toggle(CONNECT, self.header_frame.connection_selector.get())
        self.header_frame.connection_indicator_toggle(CONNECT)

    def on_connect_button(self):
        self.header_frame.connection_error_notification["text"] = ""
        self.current_connection_configuration = self.config_handler.get_connection_config_dict(
            self.header_frame.connection_selector.get())
        if not self.current_connection_configuration:
            return
        self.header_frame.interface_toggle(CONNECT)
        self.config_handler.update_last_used_connection(self.header_frame.connection_selector.get())
        try:
            self.mqtt_manager = MqttManager(self.current_connection_configuration["connection_parameters"],
                                            self.on_client_connect,
                                            self.on_client_disconnect,
                                            self.log)
        except Exception as e:
            self.log.exception("Failed to initialise MQTT client:", e, "\r\n", traceback.format_exc())
            self.header_frame.interface_toggle(DISCONNECT)
            self.publish_frame.interface_toggle(DISCONNECT)

        self.subscribe_frame.subscribe_selector.configure(values=self.current_connection_configuration.get(
            "subscriptions", []))
        self.subscribe_frame.subscribe_selector.set(self.config_handler.get_last_subscribe_used(
            self.header_frame.connection_selector.get()))

    def on_publish(self, topic, payload, qos, retained):
        if self.mqtt_manager is not None:
            self.mqtt_manager.publish(topic, payload, qos, retained)

    def on_disconnect_button(self):
        if self.mqtt_manager is not None:
            self.mqtt_manager.disconnect()

    def topic_mute_callback(self, topic, mute_state):
        if mute_state and topic not in self.mute_patterns:
            self.mute_patterns.append(topic)
        if not mute_state and topic in self.mute_patterns:
            self.mute_patterns.remove(topic)

    def add_subscription(self):
        topic = self.subscribe_frame.subscribe_selector.get()
        if topic != "" and topic not in self.subscription_frames:
            try:
                callback = partial(self.on_mqtt_message, subscription_pattern=topic)
                callback.__name__ = "MyCallback"  # This is to fix some weird behaviour of the paho client on linux
                self.mqtt_manager.add_subscription(topic_pattern=topic,
                                                   on_message_callback=callback)
            except Exception as e:
                self.log.exception("Failed to subscribe!", e)
                return
            self.add_subscription_frame(topic, self.on_unsubscribe)
            if self.subscribe_frame.subscribe_selector["values"] == "":
                self.subscribe_frame.subscribe_selector["values"] = [topic]
            elif topic not in self.subscribe_frame.subscribe_selector['values']:
                self.subscribe_frame.subscribe_selector['values'] += (topic,)
            self.config_handler.add_subscription_history(self.header_frame.connection_selector.get(), topic)

    def add_subscription_frame(self, topic, unsubscribe_callback):
        if topic not in self.subscription_frames:
            self.subscription_frames[topic] = SubscriptionFrame(self.subscribe_frame.subscriptions_frame.viewPort,
                                                                topic,
                                                                unsubscribe_callback,
                                                                self.get_color(),
                                                                self.on_colour_change,
                                                                self.topic_mute_callback,
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
        time_string = "{:.6f} - {}".format(round(timestamp, 6),
                                           datetime.fromtimestamp(timestamp).strftime("%Y/%m/%d, %H:%M:%S.%f"))
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
        try:
            colour = self.subscription_frames[subscription_pattern].colour
        except Exception as e:
            print("Failed to add stuff")
        else:
            self.subscribe_frame.add_message(message_title, colour)

    def on_mqtt_message(self, _, __, msg, subscription_pattern):
        if subscription_pattern in self.mute_patterns:
            return
        self.add_new_message(mqtt_message_object=msg,
                             subscription_pattern=subscription_pattern)

    def on_config_update(self):
        connection_profile_list = sorted(self.config_handler.get_connection_profiles())
        if len(connection_profile_list) != 0:
            self.header_frame.connection_selector.configure(values=connection_profile_list)
            if self.config_handler.get_last_used_connection() in connection_profile_list:
                self.header_frame.connection_selector.current(
                    connection_profile_list.index(self.config_handler.get_last_used_connection()))
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
        self.header_frame.connection_error_notification["text"] = ""
        configuration_window = ConfigurationWindow(self.root,
                                                   self.config_handler,
                                                   self.on_config_update,
                                                   self.log,
                                                   self.icon)
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
                subscription_frame = self.subscription_frames.get(
                    self.messages[message_id]["subscription_pattern"], None)
                if subscription_frame is not None:
                    self.subscribe_frame.incoming_messages_list.itemconfig(message_id, bg=subscription_frame.colour)
            except Exception as e:
                self.log.warning("Failed to change message colour!", e)

    def on_exit(self):
        self.on_disconnect_button()
        self.config_handler.save_window_geometry(self.root.geometry())
        self.config_handler.save_autoscroll(self.subscribe_frame.autoscroll_state.get())
        root.after(100, root.destroy())
        # root.destroy()

    def on_destroy(self):
        self.on_exit()


def main():
    app = App(root)
    root.mainloop()


if __name__ == "__main__":
    sys.exit(main())

