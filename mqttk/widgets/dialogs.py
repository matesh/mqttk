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
import os.path
import traceback

from mqttk import __version__ as version
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
import json
from mqttk.helpers import validate_name, clear_combobox_selection, get_clear_combobox_selection_function
from tkinter import messagebox
from copy import deepcopy


about_text = "MQTTk is a lightweight, free and open source graphical MQTT\n" \
             "client/analyser. It is licensed under the GNU GPLv3 license.\n" \
             "For license information please see:\n" \
             "https://www.gnu.org/licenses/\n\n" \
             "This software is written in pure Python and is powered by\n" \
             "the below open source projects:\n\n" \
             "Python 3 and Tkinter/ttk:\n" \
             "https://docs.python.org/3/license.html\n\n" \
             "Eclipse paho-mqtt python client library:\n" \
             "https://github.com/eclipse/paho.mqtt.python\n\n" \
             "xmltodict library:\n" \
             "https://github.com/martinblech/xmltodict\n\n" \
             "Copyright (C) 2022  Máté Szabó"


class AboutDialog(tk.Toplevel):
    def __init__(self, master, icon, style):
        super().__init__(master=master)
        self.transient(master)
        self.master = master
        self.title("About")

        self.resizable(False, False)
        self.iconphoto(False, icon)

        self.about_frame = ttk.Frame(self)

        self.about_label = ttk.Label(self.about_frame, text="About MQTTk\n\nVersion {}".format(version), anchor='n', justify=tk.CENTER, font="Arial 14 bold")
        self.about_label.pack(side=tk.TOP, fill='x', expand=1)

        self.about_content_frame = ttk.Frame(self.about_frame)
        # self.icon_canvas = tk.Canvas(self.about_content_frame, width=200, height=200)
        # self.icon_canvas.create_image(10, 10, anchor='w', image=icon)
        # self.icon_canvas.pack(side=tk.LEFT, expand=1, fill='both')
        self.icon = ttk.Label(self.about_content_frame, image=icon)
        self.icon.pack(side=tk.LEFT, padx=8)
        self.about_text = tk.Text(self.about_content_frame, wrap='word', width=55, height=18, exportselection=False, font='Arial 14')
        self.about_text.pack(side=tk.RIGHT, fill='x', expand=1, padx=6, pady=6)
        self.about_text.insert(1.0, about_text)
        self.about_text.configure(bg=style.lookup("TLabel", "background"),
                                  relief='flat',
                                  state='disabled',
                                  borderwidth=0,
                                  border=0,
                                  highlightcolor=style.lookup("TLabel", "background"))
        self.about_content_frame.pack(expand=1, fill='x')

        self.ok_button = ttk.Button(self.about_frame, text="OK")
        self.ok_button.pack(side=tk.BOTTOM, pady=4)
        self.ok_button["command"] = self.on_destroy
        self.about_frame.pack(fill='both', expand=1)

        self.grab_set()

        self.geometry("")
        self.update()
        screenwidth = self.winfo_screenwidth()
        screenheight = self.winfo_screenheight()
        height = self.winfo_height()
        width = self.winfo_width()
        alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        self.geometry(alignstr)
        self.protocol("WM_DELETE_WINDOW", self.on_destroy)
        self.bind("<Return>", self.on_destroy)
        self.bind("<Escape>", self.on_destroy)
        self.focus_set()
        self.wait_window(self)

    def on_destroy(self, *args, **kwargs):
        self.grab_release()
        self.destroy()


class PublishNameDialog(tk.Toplevel):
    def __init__(self, master, current_value, name_callback):
        super().__init__(master=master)
        self.master = master
        self.title("Please enter publish template name")
        self.name_callback = name_callback
        width = 250
        height = 140
        screenwidth = self.winfo_screenwidth()
        screenheight = self.winfo_screenheight()
        alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        self.resizable(False, False)
        self.geometry(alignstr)
        self.protocol("WM_DELETE_WINDOW", self.on_destroy)

        self.dialog_frame = ttk.Frame(self)
        self.dialog_frame.pack(fill='both', expand=1)

        self.instruction_text = ttk.Label(self.dialog_frame, text="Please enter publish template name".format(version), anchor='n', justify=tk.CENTER)
        self.instruction_text.pack(side=tk.TOP, fill='x', padx=10, pady=10)

        self.name_input = ttk.Entry(self.dialog_frame)
        self.name_input.insert(0, current_value)
        self.name_input.pack(expand=1, fill='x', side=tk.TOP, padx=10, pady=10)

        self.buttons_frame = ttk.Frame(self.dialog_frame)
        self.buttons_frame.pack(side=tk.TOP, fill='x', expand=1)
        self.ok_button = ttk.Button(self.dialog_frame, text="OK")
        self.ok_button.pack(side=tk.RIGHT, pady=10, padx=20)
        self.ok_button["command"] = self.on_save
        self.cancel_button = ttk.Button(self.dialog_frame, text="Cancel")
        self.cancel_button.pack(side=tk.LEFT, pady=10, padx=20)
        self.cancel_button["command"] = self.on_destroy

    def on_save(self, ):
        if self.name_input.get() != "":
            self.name_callback(self.name_input.get())
        self.on_destroy()

    def on_destroy(self, *args, **kwargs):
        self.grab_release()
        self.destroy()


class SplashScreen(tk.Toplevel):
    def __init__(self, master, splash_icon):
        super().__init__(master=master)
        screenwidth = master.winfo_screenwidth()
        screenheight = master.winfo_screenheight()
        self.overrideredirect(True)
        width = 370
        height = 350
        alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        self.geometry(alignstr)
        self.title("Splash")
        splash_label = ttk.Label(self, image=splash_icon, anchor=tk.CENTER)
        splash_label.pack(expand=1, fill="both")
        self.update()


class ConnectionConfigImportExport(tk.Toplevel):
    def __init__(self, master, icon, config_handler, logger, is_import=False):
        super().__init__(master=master)
        self.transient(master)
        self.is_import = is_import
        self.master = master
        self.title("{} connection config".format("Import" if is_import else "Export"))
        self.resizable(False, False)
        self.iconphoto(False, icon)
        self.config_handler = config_handler
        self.log = logger
        self.imported_connection_configs = None

        self.dialog_frame = ttk.Frame(self)
        self.dialog_frame.pack(fill="both", expand=1)

        if not is_import:
            self.select_profile_frame = ttk.Frame(self.dialog_frame)
            self.select_profile_frame.pack(expand=1, fill='y', padx=4, pady=4)

            connection_selector_label = ttk.Label(self.select_profile_frame, text="Select connection")
            connection_selector_label.pack(side=tk.LEFT)

            self.connection_selector = ttk.Combobox(self.select_profile_frame, width=30, exportselection=False)
            self.connection_selector.bind("<<ComboboxSelected>>", get_clear_combobox_selection_function(self.connection_selector))
            self.connection_selector.pack(side=tk.LEFT, padx=3, pady=3)
            connection_profile_list = sorted(self.config_handler.get_connection_profiles())
            if len(connection_profile_list) != 0:
                self.connection_selector.configure(values=connection_profile_list)
                if self.config_handler.get_last_used_connection() in connection_profile_list:
                    self.connection_selector.current(
                        connection_profile_list.index(self.config_handler.get_last_used_connection()))
                else:
                    self.connection_selector.current(0)

        self.browse_frame = ttk.Frame(self.dialog_frame)
        self.browse_frame.pack(fill="x", padx=4, pady=4)
        self.browse_label = ttk.Label(self.browse_frame, text="File")
        self.browse_label.pack(side=tk.LEFT, anchor="w", padx=2, pady=4, expand=1)
        self.file_input = ttk.Entry(self.browse_frame, width=40)
        self.file_input.pack(side=tk.LEFT, padx=2)
        self.browser_button = ttk.Button(self.browse_frame, width=3, text="...", command=self.browse_file)
        self.browser_button.pack(side=tk.LEFT, padx=2, pady=2)

        self.info_frame = ttk.Frame(self.dialog_frame)
        self.info_frame.pack(padx=4, pady=4, fill="x", expand=1)
        self.info_label = ttk.Label(self.info_frame)
        self.info_label.pack(fill="x")

        self.button_frame = ttk.Frame(self.dialog_frame)
        self.button_frame.pack(expand=1, pady=4, padx=4, fill="x")
        self.ok_button = ttk.Button(self.button_frame,
                                    text="Import" if is_import else "Export",
                                    command=self.ok,
                                    state="disabled")
        self.ok_button.pack(side=tk.RIGHT)

        self.cancel_button = ttk.Button(self.button_frame,
                                        text="Cancel",
                                        command=self.on_destroy)
        self.cancel_button.pack(side=tk.RIGHT, padx=4, pady=4)

        self.grab_set()
        self.geometry("")
        self.update()
        screenwidth = self.winfo_screenwidth()
        screenheight = self.winfo_screenheight()
        height = self.winfo_height()
        width = self.winfo_width()
        alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        self.geometry(alignstr)
        self.protocol("WM_DELETE_WINDOW", self.on_destroy)
        self.bind("<Escape>", self.on_destroy)
        self.focus_set()
        self.wait_window(self)

    def browse_file(self):
        self.imported_connection_configs = None
        self.ok_button["state"] = "disabled"
        if self.is_import:
            file_path_name = filedialog.askopenfilename(initialdir=self.config_handler.get_last_used_directory(),
                                                        title="Import connection configuration")
            if file_path_name == "":
                self.log.warning("Empty file name when browsing for connection config to import. Maybe the cancel button was pressed?")
                return
        else:
            file_path_name = filedialog.asksaveasfilename(initialdir=self.config_handler.get_last_used_directory(),
                                                          title="Export connection configuration",
                                                          defaultextension="json",
                                                          initialfile="{}-config".format(self.connection_selector.get().replace(" ", "_")))

            if file_path_name == "":
                self.log.warning("Empty file name when exporting connection config. Maybe the cancel button was pressed?")
                return

        self.config_handler.save_last_used_directory(file_path_name)
        self.file_input.delete(0, tk.END)
        self.file_input.insert(0, file_path_name)

        if not self.is_import:
            self.log.info("File selected for communication config export: {}".format(file_path_name))
            self.ok_button["state"] = "normal"
            return

        if not os.path.isfile(file_path_name):
            self.log.error("The file picked for connection config import doesn't exist!", file_path_name)
            self.info_label["text"] = "Invalid file"
            self.info_label["foreground"] = "red"
            return

        try:
            with open(file_path_name, "r", encoding="utf-8") as configfile:
                config_dict = json.loads(configfile.read())
        except Exception as e:
            self.log.error("Failed to load connection config file", e, traceback.format_exc())

        connection_configs = config_dict.get("connections", None)
        if not connection_configs:
            self.log.error("There are no connection profiles in this file.")
            self.info_label["text"] = "There are no connection profiles in this file."
            self.info_label["foreground"] = "red"
            return

        self.info_label["text"] = "Found {} connection configuration{}!".format(len(connection_configs),
                                                                                "" if len(connection_configs) == 1 else "s")
        self.info_label["foreground"] = "green"
        self.imported_connection_configs = connection_configs
        self.ok_button["state"] = "normal"
        self.log.info("File selected for communication config import: {}".format(file_path_name))

    def on_destroy(self, *args, **kwargs):
        self.grab_release()
        self.destroy()

    def ok(self, *args, **kwargs):
        if self.is_import:
            self.log.info("Attempting to import connection configuration")
            try:
                all_connection_configs = self.config_handler.get_connection_profiles()
                for connection_name, configuration in self.imported_connection_configs.items():
                    name = validate_name(connection_name, all_connection_configs)
                    self.config_handler.save_connection_config(name, configuration.get("connection_parameters", {}))
            except Exception as e:
                self.log.error("Failed to import connection configurations", e, traceback.format_exc())
                messagebox.showerror("Error importing communication config", "See log for details")
            else:
                messagebox.showinfo("Success", "Communication configuration{} imported successfully".format(
                    "" if len(self.imported_connection_configs) == 1 else "s"
                ))
            self.on_destroy()
        else:
            connection_to_export = self.connection_selector.get()
            connection_config = self.config_handler.get_connection_config_dict(connection_to_export)
            self.log.info("Exporting connection config {} into {}".format(connection_to_export,
                                                                           self.file_input.get()))
            export_dict = {
                "connections": {
                    connection_to_export: deepcopy(connection_config)
                }
            }

            export_dict["connections"][connection_to_export].pop("subscriptions", None)
            export_dict["connections"][connection_to_export].pop("publish_topics", None)
            export_dict["connections"][connection_to_export].pop("stored_publishes", None)
            export_dict["connections"][connection_to_export].pop("last_publish_used", None)
            export_dict["connections"][connection_to_export].pop("last_subscribe_used", None)

            try:
                with open(self.file_input.get(), "w", encoding="utf-8") as export_file:
                    export_file.write(json.dumps(export_dict, indent=2, ensure_ascii=False))
            except Exception as e:
                self.log.error("Failed to export connection config", e, traceback.format_exc())
                messagebox.showerror("Error", "Error exporting communication config. SSee log for details")
            else:
                self.log.info("Successfully exported connection config")
                messagebox.showinfo("Success", "Communication profile exported successfully")
            self.on_destroy()


class SubscribePublishImportExport(tk.Toplevel):
    def __init__(self, master, icon, config_handler, logger, is_import=False):
        super().__init__(master=master)
        self.transient(master)
        self.is_import = is_import
        self.master = master
        self.title("{} subscribe/publish/template content".format("Import" if is_import else "Export"))
        self.resizable(False, False)
        self.iconphoto(False, icon)
        self.config_handler = config_handler
        self.log = logger
        self.imported_history = None

        self.dialog_frame = ttk.Frame(self)
        self.dialog_frame.pack(fill="both", expand=1)

        self.select_profile_frame = ttk.Frame(self.dialog_frame)
        self.select_profile_frame.pack(expand=1, fill='y', padx=4, pady=4)

        connection_selector_label = ttk.Label(self.select_profile_frame, text="Select connection")
        connection_selector_label.pack(side=tk.LEFT)

        self.connection_selector = ttk.Combobox(self.select_profile_frame, width=30, exportselection=False)
        self.connection_selector.bind("<<ComboboxSelected>>", self.on_profile_select)
        self.connection_selector.pack(side=tk.LEFT, padx=3, pady=3)

        self.browse_frame = ttk.Frame(self.dialog_frame)
        self.browse_frame.pack(fill="x", padx=4, pady=4)
        self.browse_label = ttk.Label(self.browse_frame, text="File")
        self.browse_label.pack(side=tk.LEFT, anchor="w", padx=2, pady=4, expand=1)
        self.file_input = ttk.Entry(self.browse_frame, width=40)
        self.file_input.pack(side=tk.LEFT, padx=2)
        self.browser_button = ttk.Button(self.browse_frame, width=3, text="...", command=self.browse_file)
        self.browser_button.pack(side=tk.LEFT, padx=2, pady=2)

        self.checkbox_frame = ttk.Frame(self.dialog_frame)
        self.checkbox_frame.pack(padx=4, pady=4, expand=1)

        self.subscribe_topic_selection = tk.IntVar()
        self.subscribe_topic_checkbox = ttk.Checkbutton(self.checkbox_frame,
                                                        text="Subscribe topic history items",
                                                        variable=self.subscribe_topic_selection,
                                                        offvalue=0,
                                                        onvalue=1,
                                                        command=self.on_checkbox)
        self.subscribe_topic_checkbox.pack(expand=1, fill="x", padx=4, pady=4)

        self.publish_topic_selection = tk.IntVar()
        self.publish_topic_checkbox = ttk.Checkbutton(self.checkbox_frame,
                                                      text="Publish topic history items",
                                                      variable=self.publish_topic_selection,
                                                      offvalue=0,
                                                      onvalue=1,
                                                      command=self.on_checkbox)
        self.publish_topic_checkbox.pack(expand=1, fill="x", padx=4, pady=4)

        self.message_template_selection = tk.IntVar()
        self.message_template_checkbox = ttk.Checkbutton(self.checkbox_frame,
                                                         text="Message template items",
                                                         variable=self.message_template_selection,
                                                         offvalue=0,
                                                         onvalue=1,
                                                         command=self.on_checkbox)
        self.message_template_checkbox.pack(expand=1, fill="x", padx=4, pady=4)

        self.info_frame = ttk.Frame(self.dialog_frame)
        self.info_frame.pack(padx=4, pady=4, fill="x", expand=1)
        self.info_label = ttk.Label(self.info_frame)
        self.info_label.pack(fill="x")

        self.button_frame = ttk.Frame(self.dialog_frame)
        self.button_frame.pack(expand=1, pady=4, padx=4, fill="x")
        self.ok_button = ttk.Button(self.button_frame,
                                    text="Import" if is_import else "Export",
                                    command=self.ok,
                                    state="disabled")
        self.ok_button.pack(side=tk.RIGHT)

        self.cancel_button = ttk.Button(self.button_frame,
                                        text="Cancel",
                                        command=self.on_destroy)
        self.cancel_button.pack(side=tk.RIGHT, padx=4, pady=4)

        connection_profile_list = sorted(self.config_handler.get_connection_profiles())
        if len(connection_profile_list) != 0:
            self.connection_selector.configure(values=connection_profile_list)
            if self.config_handler.get_last_used_connection() in connection_profile_list:
                self.connection_selector.current(
                    connection_profile_list.index(self.config_handler.get_last_used_connection()))
                self.on_profile_select()
            else:
                self.connection_selector.current(0)
                self.on_profile_select()

        self.grab_set()
        self.geometry("")
        self.update()
        screenwidth = self.winfo_screenwidth()
        screenheight = self.winfo_screenheight()
        height = self.winfo_height()
        width = self.winfo_width()
        alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        self.geometry(alignstr)
        self.protocol("WM_DELETE_WINDOW", self.on_destroy)
        self.bind("<Escape>", self.on_destroy)
        self.focus_set()
        self.wait_window(self)

    def on_checkbox(self):
        if any((bool(self.subscribe_topic_selection.get()),
                bool(self.publish_topic_selection.get()),
                bool(self.message_template_selection.get()))) and self.file_input.get() != "":
            self.ok_button["state"] = "normal"
        else:
            self.ok_button["state"] = "disabled"

    def on_profile_select(self, *args, **kwargs):
        clear_combobox_selection(combobox_instance=self.connection_selector)
        if self.is_import:
            return

        connection_config = self.config_handler.get_connection_config_dict(self.connection_selector.get())
        self.update_items(connection_config)

    def browse_file(self):
        self.imported_history = None
        self.ok_button["state"] = "disabled"
        self.info_label["text"] = ""

        if self.is_import:
            file_path_name = filedialog.askopenfilename(initialdir=self.config_handler.get_last_used_directory(),
                                                        title="Import connection configuration")
            if file_path_name == "":
                self.log.warning("Empty file name when importing subscribe/publish stuff. Maybe the cancel button was pressed?")
                return
        else:
            file_path_name = filedialog.asksaveasfilename(initialdir=self.config_handler.get_last_used_directory(),
                                                          title="Export connection configuration",
                                                          defaultextension="json",
                                                          initialfile="{}-topics-content".format(self.connection_selector.get().replace(" ", "_")))
            if file_path_name == "":
                self.log.warning("Empty file name when exporting subscribe/publish stuff. Maybe the cancel button was pressed?")
                return

        self.config_handler.save_last_used_directory(file_path_name)
        self.file_input.delete(0, tk.END)
        self.file_input.insert(0, file_path_name)

        if not self.is_import:
            self.log.info("File selected for topic and message export: {}".format(file_path_name))
            self.on_checkbox()
            return

        if not os.path.isfile(file_path_name):
            self.log.error("The file picked for topic and message history import doesn't exist!", file_path_name)
            self.info_label["text"] = "Invalid file"
            self.info_label["foreground"] = "red"
            return

        try:
            with open(file_path_name, "r", encoding="utf-8") as configfile:
                history_dict = json.loads(configfile.read())
        except Exception as e:
            self.log.error("Failed to load topic and message history file", e, traceback.format_exc())

        self.update_items(history_dict)

        self.imported_history = history_dict
        self.log.info("File selected for communication config import: {}".format(file_path_name))

    def on_destroy(self, *args, **kwargs):
        self.grab_release()
        self.destroy()

    def update_items(self, history_dict):
        self.subscribe_topic_checkbox["text"] = "{} Subscribe topic history items".format(
            0 if "subscriptions" not in history_dict else len(history_dict["subscriptions"]))

        self.publish_topic_checkbox["text"] = "{} Publish topic history items".format(
            0 if "publish_topics" not in history_dict else len(history_dict["publish_topics"])
        )

        self.message_template_checkbox["text"] = "{} Message template items".format(
            0 if "stored_publishes" not in history_dict else len(history_dict["stored_publishes"]))

    def ok(self, *args, **kwargs):
        if self.is_import:
            connection_to_import_to = self.connection_selector.get()
            self.log.info("Attempting to import publish/subscribe history into {}".format(connection_to_import_to))
            config_to_update = self.config_handler.get_connection_config_dict(connection_to_import_to)
            try:
                for key in ("subscriptions", "stored_publishes"):
                    config_to_update[key].update(self.imported_history.get(key, {}))
                if "publish_topics" in self.imported_history:
                    for topic in self.imported_history["publish_topics"]:
                        if topic not in config_to_update["publish_topics"]:
                            config_to_update["publish_topics"].append(topic)
                self.config_handler.save_connection_dict(connection_to_import_to, config_to_update)
            except Exception as e:
                self.log.error("Failed to import subscribe/publish history", e, traceback.format_exc())
                messagebox.showerror("Error", "Error importing subscribe/publish history. See log for details")
            else:
                messagebox.showinfo("Success", "Publish/subscribe history imported successfully")
            self.on_destroy()
        else:
            connection_to_export = self.connection_selector.get()
            connection_config = self.config_handler.get_connection_config_dict(connection_to_export)
            self.log.info("Exporting subscription and publish history from {} into {}".format(connection_to_export,
                                                                                              self.file_input.get()))
            export_dict = {}
            if bool(self.subscribe_topic_selection.get()):
                export_dict["subscriptions"] = connection_config.get("subscriptions", {})
            if bool(self.publish_topic_selection.get()):
                export_dict["publish_topics"] = connection_config.get("publish_topics", {})
            if bool(self.message_template_selection.get()):
                export_dict["stored_publishes"] = connection_config.get("stored_publishes", {})

            try:
                with open(self.file_input.get(), "w", encoding="utf-8") as export_file:
                    export_file.write(json.dumps(export_dict, indent=2, ensure_ascii=False))
            except Exception as e:
                self.log.error("Failed to export publish and subscription history", e, traceback.format_exc())
                messagebox.showerror("Error exporting publish and subscription history", "See log for details")
            else:
                self.log.info("Successfully exported publish and subscription history")
                messagebox.showinfo("Success", "Subscription/publish history exported successfully")
            self.on_destroy()
