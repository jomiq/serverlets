import datetime as dt
from time import sleep
from typing import Any
import paho.mqtt.client as paho
import paho.mqtt as mqtt
import json

    
class Client(paho.Client):

    topics = []    
    result = []
    userdata = None
    N = 1
    status = "ok"
    
    end_time = None
    subscribed = 0
    accept_func = None
    abort_func = None
    url = ""

    

    def __init__(self, url, user, password):
        super().__init__("", userdata=None, protocol=paho.MQTTv5)
        self.url = url
        self.tls_set(tls_version=paho.ssl.PROTOCOL_TLS)
        self.username_pw_set(user, password)

        self.on_connect = on_connect
        self.on_subscribe = on_subscribe
        self.on_message = on_message


    def run(self, topics: list, timeout=None, accept=None, abort=None, userdata=None, blocking=False):
        self.topics = topics
        self.result = []
        self.userdata = userdata

        self.accept_func = accept
        self.abort_func = abort

        if not self.is_connected():
            self.subscribed = 0
            self.connect(self.url, 8883)

        
        while self.subscribed < len(self.topics):
            self.loop()

        if timeout != None:
            self.end_time = dt.datetime.now() + dt.timedelta(seconds=timeout)
        else:
            self.end_time = None

        print("starting")
        self.loop_start()
        if blocking:
            self.wait()
            
    def wait(self):
        print(self.end_time)
        while self.is_connected():
            t_sleep = 0.1
            if self.end_time != None:
                t = self.end_time - dt.datetime.now() 
                if t.total_seconds() <= 0.0:
                    self.status = "timeout"
                    self.disconnect()
                t_sleep = max(0, min(t_sleep, t.total_seconds()))

            sleep(t_sleep)
        self.loop_stop()

def on_connect(client: Client, userdata, flags, rc, _properties):
    print("CONNACK received with code %s." % rc)
    for t in client.topics:
        client.subscribe(t, 1)

def on_subscribe(client: Client, userdata, mid, granted_qos, _properties):
    v = granted_qos[0].value < 4
    if v < 4:
        client.subscribed += 1
    else:
        raise Exception(f"Failed subscription {granted_qos[0].names[v]}")

def on_message(client: Client, userdata, msg):
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload, "utf-8"))
    try:
        if client.abort_func:
            client.abort_func(client, msg)
        if client.accept_func:
            client.accept_func(client, msg)
    except Exception as e:
        print(e)
        client.status = e
        client.disconnect()



def acc_all(client: Client, msg):
    client.result.append(msg)
    raise Exception("done")

def abort_none(client: Client, msg):
    pass

def accept_bacon(client: Client, msg):
    if msg.topic == "info" and str(msg.payload, "utf-8") == "bacon":
        client.result.append(str(msg.payload, "utf-8"))
        if len(client.result) >= client.userdata.N:
            raise Exception("done")

def abort_chicken(client: Client, msg):
    if msg.topic == "control" and str(msg.payload, "utf-8") == "chicken":
        raise Exception(f"{client.userdata.msg} reason: chicken")

if __name__ == "__main__":
    from collections import namedtuple
    Data = namedtuple("Data", ["N", "msg"])

    URL = None
    with open("mqtt.json", "r") as f:
        URL = json.load(f)["url"]

    secrets = None
    with open("secrets.json", "r") as f:
        secrets = json.load(f)

    bork = Client(URL, secrets["user"], secrets["password"])

    data = Data(3, "I'm outta here...")
    bork.run(["control", "info"], 
                accept=accept_bacon,
                abort=abort_chicken, 
                userdata=data,
                timeout=10.0,
                blocking=False
                )

    bork.wait()

    print(bork.result)
    print(bork.status)

    print("re-entrant: ")

    bork.run(["info"], timeout=5.0)
    bork.wait()

    print(bork.result)
    print(bork.status)
