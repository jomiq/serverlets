import json
import time
import paho.mqtt.client as paho
from paho import mqtt
import datetime as dt

import pyshark

URL = None
with open("mqtt.json", "r") as f:
    URL = json.load(f)["url"]

secrets = None
with open("secrets.json", "r") as f:
    secrets = json.load(f)

def on_connect(client, userdata, flags, rc, properties=None):
    print("CONNACK received with code %s." % rc)
    client.subscribe("control", 1)

def on_publish(client, userdata, mid, properties=None):
    print("mid: " + str(mid))

def on_subscribe(client, userdata, mid, granted_qos, properties):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    if msg.topic == "control" and str(msg.payload, "utf-8") == "die":
        print("Exit per request")
        exit(0)

client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
client.tls_set(tls_version=paho.ssl.PROTOCOL_TLS)
client.username_pw_set(secrets["user"], secrets["password"])
client.on_connect = on_connect
client.on_subscribe = on_subscribe
client.on_message = on_message

client.connect(URL, 8883)

cap = pyshark.LiveCapture("lo")

print("pyshark go")
for packet in cap.sniff_continuously():
    client.publish("data", packet.ip.dst)
    time.sleep(1)
    client.loop()


print("bye")
client.disconnect()
