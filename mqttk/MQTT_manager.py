import ssl

import paho.mqtt.client as mqtt
from mqttk.constants import PROTOCOL_LOOKUP, SSL_LIST, ERROR_CODES
from uuid import uuid4


class MqttManager:
    def __init__(self, connection_configuration, on_connect_callback, on_disconnect_callback, logger):
        if not connection_configuration:
            raise Exception("Invalid connection parameters, configuration empty")
        self.on_connect_callback = on_connect_callback
        self.on_disconnect_callback = on_disconnect_callback
        self.log = logger
        self.disconnect_requested = False

        autogen = connection_configuration.get("client_id_autogen", 0)
        if autogen == 1:
            self.client_id = str(uuid4()).replace("-", "")
        else:
            self.client_id = connection_configuration["client_id"]

        try:
            self.client = mqtt.Client(self.client_id,
                                      clean_session=True,
                                      userdata=None,
                                      protocol=PROTOCOL_LOOKUP.get(connection_configuration["mqtt_version"], mqtt.MQTTv311),
                                      transport="tcp")
        except ValueError:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1,
                                      self.client_id,
                                      clean_session=True,
                                      userdata=None,
                                      protocol=PROTOCOL_LOOKUP.get(connection_configuration["mqtt_version"], mqtt.MQTTv311),
                                      transport="tcp")

        self.client.on_log = self.log.on_paho_log

        if connection_configuration.get("user", "") != "":
            self.client.username_pw_set(username=connection_configuration["user"],
                                        password=connection_configuration.get("pass", ""))

        ssl_config = connection_configuration.get("ssl", None)
        if ssl_config is not None and ssl_config in SSL_LIST and ssl_config != "Disabled":
            if ssl_config.startswith("CA signed"):
                self.client.tls_set(ca_certs=None,
                                    certfile=None,
                                    keyfile=None,
                                    cert_reqs=ssl.CERT_REQUIRED,
                                    tls_version=ssl.PROTOCOL_TLS,
                                    ciphers=None,
                                    keyfile_password=None)
            elif ssl_config.startswith("CA certificate"):
                self.client.tls_set(ca_certs=connection_configuration.get("ca_file", ""),
                                    certfile=None,
                                    keyfile=None,
                                    cert_reqs=ssl.CERT_REQUIRED,
                                    tls_version=ssl.PROTOCOL_TLS,
                                    ciphers=None,
                                    keyfile_password=None)
            elif ssl_config.startswith("Self-signed certificate"):
                self.client.tls_set(ca_certs=connection_configuration.get("ca_file", ""),
                                    certfile=connection_configuration.get("cl_cert", ""),
                                    keyfile=connection_configuration.get("cl_key", ""),
                                    cert_reqs=ssl.CERT_REQUIRED,
                                    tls_version=ssl.PROTOCOL_TLS,
                                    ciphers=None,
                                    keyfile_password=None)

        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.connect(host=connection_configuration.get("broker_addr", ""),
                            port=int(connection_configuration.get("broker_port", "")),
                            keepalive=int(connection_configuration.get("keepalive", 60)))
        self.client.loop_start()
        self.log.info("Paho MQTT client manager initialised")

    def on_connect(self, _, __, ___, rc):
        if rc == 0:
            self.log.info("Paho MQTT Client successfully connected, client ID: {}".format(self.client_id))
            self.client.loop_start()
            self.on_connect_callback()
        else:
            self.log.error("Bad connection, returned code: {}".format(rc))
            self.on_disconnect_callback(notify="Failed to connect: {}".format(ERROR_CODES.get(rc, "Unknown error {}".format(rc))))

    def on_disconnect(self, _, __, rc):
        self.log.info("Paho MQTT client disconnected")
        self.client.loop_stop()
        if rc != 0:
            try:
                self.on_disconnect_callback(notify="Disconnected, return code: {}".format(rc))
            except Exception as e:
                self.log.exception("Failed to reconfigure interface for disconnect: {}".format(e))
        self.on_disconnect_callback()

    def disconnect(self):
        if self.client.is_connected():
            self.log.info("Paho MQTT client manager instructed to disconnect")
            self.client.disconnect()
        else:
            try:
                self.client.disconnect()
            except Exception:
                pass
            self.on_disconnect(0, 0, 0)
        self.disconnect_requested = True

    def add_subscription(self, topic_pattern, on_message_callback):
        self.log.info("MQTT client manager adding subscription", topic_pattern)
        self.client.subscribe(topic_pattern)
        self.client.message_callback_add(topic_pattern, on_message_callback)

    def unsubscribe(self, topic_filter):
        self.log.info("MQTT client manager unsubscribing", topic_filter)
        self.client.unsubscribe(topic_filter)
        self.client.message_callback_remove(topic_filter)

    def publish(self, topic, payload, qos, retained):
        self.log.info("Publish", topic)
        self.client.publish(topic, payload, qos, retained)
