import datetime as dt
from time import sleep
from typing import Any
import paho.mqtt.client as paho
import paho.mqtt as mqtt
import json

    
class MQTTListener(paho.Client):
    """A listener for doing tasks like awaiting a message,
        Can be extended to run more extensive state machines
    """

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

    blocking = False
    userdata = None
    

    def __init__(self, url, user, password):
        super().__init__("", userdata=None, protocol=paho.MQTTv5)
        self.url = url
        self.tls_set(tls_version=paho.ssl.PROTOCOL_TLS)
        self.username_pw_set(user, password)

        self.on_connect = on_connect
        self.on_subscribe = on_subscribe
        self.on_message = on_message

    def setup(self, topics: list=[], timeout=None, accept_func=None, abort_func=None, userdata=None, blocking=False):
        self.topics = topics
        self.timeout = timeout
        self.accept_func = accept_func
        self.abort_func = abort_func
        self.userdata = userdata
        self.blocking = blocking
    

    def run(self):
        self.result = []
        if not self.is_connected():
            self.subscribed = 0
            self.connect(self.url, 8883)

        
        while self.subscribed < len(self.topics):
            self.loop()

        if self.timeout != None:
            self.end_time = dt.datetime.now() + dt.timedelta(seconds=self.timeout)
        else:
            self.end_time = None

        print("Starting")
        self.loop_start()
        if self.blocking:
            self.wait()
            
    def wait(self):
        while self.is_connected():
            t_sleep = 0.1
            if self.end_time != None:
                t = self.end_time - dt.datetime.now() 
                if t.total_seconds() <= 0.0:
                    self.status = "timeout"
                    self.disconnect()
                t_sleep = max(0, min(t_sleep, t.total_seconds()))

            sleep(t_sleep)

def on_disconnect(client: MQTTListener, _userdata, rc, _properties):
    print(f"DISCONNECT received with code  {rc}.")
    client.loop_stop()

def on_connect(client: MQTTListener, userdata, flags, rc, _properties):
    print(f"CONNACK received with code {rc}.")
    for t in client.topics:
        client.subscribe(t, 1)

def on_subscribe(client: MQTTListener, userdata, mid, granted_qos, _properties):
    v = granted_qos[0].value < 4
    if v < 4:
        client.subscribed += 1
    else:
        raise Exception(f"Failed subscription {mid}: {granted_qos[0].names[v]}")


def on_message(client: MQTTListener, userdata, msg):
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload, "utf-8"))
    try:
        if client.abort_func != None:
            client.abort_func(client, msg)
        if client.accept_func != None:
            client.accept_func(client, msg)
    except Exception as e:
        print(e)
        client.status = e
        client.disconnect()

    
def acc_all(client: MQTTListener, msg):
    client.result.append(msg)
    raise Exception("done")

def abort_none(client: MQTTListener, msg):
    pass

def accept_bacon(client: MQTTListener, msg):
    if msg.topic == "info" and str(msg.payload, "utf-8") == "bacon":
        client.result.append(str(msg.payload, "utf-8"))
        if len(client.result) >= client.userdata.N:
            raise Exception("done")

def abort_chicken(client: MQTTListener, msg):
    if msg.topic == "control" and str(msg.payload, "utf-8") == "chicken":
        raise Exception(f"{client.userdata.msg} reason: chicken")


if __name__ == "__main__":
    from collections import namedtuple
    from credentials import CRED
    Data = namedtuple("Data", ["N", "msg"])

    ms = CRED["mqtt"]
    bork = MQTTListener(url=ms["url"], user=ms["user"], password=ms["password"])

    data = Data(3, "I'm outta here...")
    bork.setup(["control", "info"], 
                accept_func=accept_bacon,
                abort_func=abort_chicken, 
                userdata=data,
                timeout=10.0,
                blocking=False
                )
    bork.run()
    bork.wait()

    print(bork.result)
    print(bork.status)

    print("re-entrant: ")

    bork.setup(["info"], timeout=5.0)
    bork.run()
    bork.wait()

    print(bork.result)
    print(bork.status)
