import json
import os
import ssl


class MqttPublisher:

    def __init__(self, config):
        self.config = config
        self.client = None
        self.enabled = False

    def connect(self):
        ca = self.config['ca_cert']
        cert = self.config['cert']
        key = self.config['key']
        if not (os.path.exists(ca) and os.path.exists(cert) and os.path.exists(key)):
            print("no certs found, skipping aws iot")
            return
        try:
            import paho.mqtt.client as mqtt
            self.client = mqtt.Client(client_id=self.config['client_id'])
            self.client.tls_set(
                ca_certs=ca,
                certfile=cert,
                keyfile=key,
                tls_version=ssl.PROTOCOL_TLSv1_2,
            )
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.connect(self.config['endpoint'], self.config['port'], 60)
            self.client.loop_start()
            self.enabled = True
        except Exception as e:
            print(f"mqtt connect failed: {e}")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("mqtt connected")
        else:
            print(f"mqtt bad rc {rc}")

    def _on_disconnect(self, client, userdata, rc):
        print(f"mqtt disconnected rc {rc}")

    def publish_alert(self, alert):
        if not self.enabled:
            return
        try:
            payload = json.dumps(alert)
            self.client.publish(self.config['topic'], payload, qos=1)
            print(f"published {alert['ticker']}")
        except Exception as e:
            print(f"publish failed: {e}")
