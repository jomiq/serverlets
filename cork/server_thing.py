"""A server that forwards TCP messages to a MQTT broker.
    The server can be stopped by publishing to the control topic.
"""

import atexit
from socketserver import TCPServer, BaseRequestHandler
from typing import cast
from mqttlistener import MQTTListener
from credentials import CRED

ms = CRED["mqtt"]
mqtt = MQTTListener(url=ms["url"], user=ms["user"], password=ms["password"])

class TCPHandler(BaseRequestHandler):
    
    def handle(self):
        self.data = self.request.recv(1024).strip()
        print(f"{self.client_address[0]}:")
        print(self.data)
        mqtt.publish(f"{self.client_address[0]}", self.data)
        

def abort_all_control(client: MQTTListener, msg):
    if msg.topic == "control":
        cast(TCPServer, client.userdata).shutdown()
        raise Exception(f"Abort: control {msg.payload}")
        
        
if __name__ == "__main__":

    HOST, PORT = "localhost", 9999
    
    server = TCPServer((HOST, PORT), TCPHandler)
    
    atexit.register(mqtt.disconnect)
    atexit.register(server.server_close)

    print("Setup mqtt")
    mqtt.setup(["control"], abort_func=abort_all_control, userdata=server)
    mqtt.run()
    print("Starting server")
    server.serve_forever(0.5)
    print("done")

