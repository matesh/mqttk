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

from mqttk.constants import CONNECT
from mqttk.helpers import get_clear_combobox_selection_function


class HeaderFrame(ttk.Frame):
    def __init__(self, master, app, *args, **kwargs):
        super().__init__(master=master, *args, **kwargs)

        self.connection_selector = ttk.Combobox(self, width=30, exportselection=False)
        self.connection_selector.bind("<<ComboboxSelected>>",
                                      get_clear_combobox_selection_function(self.connection_selector))
        self.connection_selector.pack(side=tk.LEFT, padx=3, pady=3)
        self.connection_selector.configure(state="readonly")
        self.config_window_button = ttk.Button(self, width=10, text="Configure", command=app.spawn_configuration_window)
        self.config_window_button.pack(side=tk.LEFT, expand=False, padx=3, pady=3)
        self.connect_button = ttk.Button(self, width=10, text="Connect", command=app.on_connect_button)
        self.connect_button.pack(side=tk.LEFT, expand=False, padx=3, pady=3)
        self.disconnect_button = ttk.Button(self,
                                            width=10,
                                            text="Disconnect",
                                            state="disabled",
                                            command=app.on_disconnect_button)
        self.disconnect_button.pack(side=tk.LEFT, expand=False, padx=3, pady=3)

        self.connection_indicator = tk.Label(self, text="DISCONNECTED", bg="#ff6b6b")
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
                                            bg="#76ff61" if connection_state == CONNECT else "#ff6b6b")
