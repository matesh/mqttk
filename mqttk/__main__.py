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
import traceback
from datetime import datetime
import sys
import time
try:
    import tkinter as tk
    import tkinter.ttk as ttk
    from tkinter import messagebox
    from tkinter import filedialog
except ImportError:
    print("Couldn't find a valid installation of tkinter/ttk. "
          "Please make sure you installed the necessary requirements!")
    if sys.platform == "darwin":
        print("Install the python-tk package via homebrew")
    elif sys.platform == "linux":
        print("Install the python-tk or python3-tk package via your operating system's package manager!")
    exit(0)


from mqttk.widgets.subscribe_tab import SubscribeTab
from mqttk.widgets.header_frame import HeaderFrame
from mqttk.widgets.publish_tab import PublishTab
from mqttk.constants import CONNECT, DISCONNECT
from mqttk.widgets.log_tab import LogTab
from mqttk.widgets.dialogs import AboutDialog, SplashScreen
from mqttk.widgets.configuration_dialog import ConfigurationWindow
from mqttk.config_handler import ConfigHandler
from mqttk.MQTT_manager import MqttManager
from paho.mqtt.client import MQTT_LOG_ERR, MQTT_LOG_INFO, MQTT_LOG_NOTICE, MQTT_LOG_WARNING


__author__ = "Máté Szabó"
__copyright__ = "Copyright 2022, Máté Szabó"
__credits__ = ["Máté Szabó"]
__license__ = "GPLv3"
__maintainer__ = "Máté Szabó"
__status__ = "Production"


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

        self.mqtt_manager = None
        self.current_connection_configuration = None

        root.title("MQTTk")
        # root.createcommand('tk::mac::ShowPreferences', self.show_preferences)  # set preferences menu
        root.createcommand('tk::mac::ShowHelp', self.on_about_menu)

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

        self.import_menu = tk.Menu(self.menubar, background=self.style.lookup("TLabel", "background"),
                                   foreground=self.style.lookup("TLabel", "foreground"))
        self.about_menu = tk.Menu(self.menubar)
        self.menubar.add_cascade(menu=self.file_menu, label="File")
        self.menubar.add_cascade(menu=self.import_menu, label="Import")
        self.menubar.add_cascade(menu=self.about_menu, label="Help")
        self.file_menu.add_command(label="Exit", command=self.on_exit)
        self.about_menu.add_command(label="About MQTTk", command=self.on_about_menu)
        self.import_menu.add_command(label="Import MQTT.fx config", command=self.import_mqttfx_config)

        self.main_window_frame = ttk.Frame(root)
        self.main_window_frame.pack(fill='both', expand=1)

        # ==================================== Header frame ===========================================================
        self.header_frame = HeaderFrame(self.main_window_frame, self, height=35)
        self.header_frame.pack(anchor="w", side=tk.TOP, fill=tk.X, padx=3, pady=3)

        self.tabs = ttk.Notebook(self.main_window_frame)
        self.tabs.pack(anchor="nw", fill="both", expand=True, padx=3, pady=3)

        self.on_config_update()

        # ==================================== Subscribe tab ==========================================================

        self.subscribe_frame = SubscribeTab(self.tabs, self.config_handler, self.log, self.style)
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

        self.subscribe_frame.interface_toggle(DISCONNECT, None, None)
        self.header_frame.interface_toggle(DISCONNECT)
        self.publish_frame.interface_toggle(DISCONNECT)

    def on_client_disconnect(self, notify=None):
        if notify is not None:
            self.header_frame.connection_error_notification["text"] = notify
        self.subscribe_frame.cleanup_subscriptions()
        try:
            self.subscribe_frame.interface_toggle(DISCONNECT, None, None)
            self.header_frame.interface_toggle(DISCONNECT)
            self.publish_frame.interface_toggle(DISCONNECT)
            self.header_frame.connection_indicator_toggle(DISCONNECT)
        except Exception as e:
            self.log.exception("Failed to toggle user interface element!", e)

    def on_client_connect(self):
        self.subscribe_frame.interface_toggle(CONNECT, self.mqtt_manager, self.header_frame.connection_selector.get())
        self.publish_frame.interface_toggle(CONNECT, self.mqtt_manager, self.header_frame.connection_selector.get())
        self.header_frame.connection_indicator_toggle(CONNECT)
        self.subscribe_frame.load_subscription_history()

    def on_connect_button(self):
        self.header_frame.connection_error_notification["text"] = ""
        self.header_frame.interface_toggle(CONNECT)
        self.config_handler.update_last_used_connection(self.header_frame.connection_selector.get())
        try:
            self.mqtt_manager = MqttManager(self.config_handler.get_connection_broker_parameters(self.header_frame.connection_selector.get()),
                                            self.on_client_connect,
                                            self.on_client_disconnect,
                                            self.log)
        except Exception as e:
            self.log.exception("Failed to initialise MQTT client:", e, "\r\n", traceback.format_exc())
            self.header_frame.connection_error_notification["text"] = "Failed to connect, see log for details"
            self.header_frame.interface_toggle(DISCONNECT)
            self.publish_frame.interface_toggle(DISCONNECT)

    def on_disconnect_button(self):
        if self.mqtt_manager is not None:
            self.mqtt_manager.disconnect()

    def on_config_update(self):
        connection_profile_list = sorted(self.config_handler.get_connection_profiles())
        if len(connection_profile_list) != 0:
            self.header_frame.connection_selector.configure(values=connection_profile_list)
            if self.config_handler.get_last_used_connection() in connection_profile_list:
                self.header_frame.connection_selector.current(
                    connection_profile_list.index(self.config_handler.get_last_used_connection()))
            else:
                self.header_frame.connection_selector.current(0)

    def spawn_configuration_window(self):
        self.header_frame.connection_error_notification["text"] = ""
        configuration_window = ConfigurationWindow(self.root,
                                                   self.config_handler,
                                                   self.on_config_update,
                                                   self.log,
                                                   self.icon)

    def on_about_menu(self):
        about_window = AboutDialog(self.root, self.icon_small, self.style)

    def on_exit(self):
        self.on_disconnect_button()
        self.config_handler.save_window_geometry(self.root.geometry())
        self.config_handler.save_autoscroll(self.subscribe_frame.autoscroll_state.get())
        root.after(100, root.destroy())
        # root.destroy()

    def on_destroy(self):
        self.on_exit()

    def import_mqttfx_config(self):
        response = messagebox.askquestion("Warning", "This feature is experimental. Would you like to proceed?", )
        if response == "no":
            return
        success = self.config_handler.import_mqttfx_config()
        if success:
            self.on_config_update()


def main():
    app = App(root)
    root.mainloop()


if __name__ == "__main__":
    sys.exit(main())

