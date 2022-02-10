import tkinter as tk
import tkinter.ttk as ttk

from mqttk.constants import CONNECT


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
