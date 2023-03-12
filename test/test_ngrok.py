from cork.credentials import pyngrok_config
from pyngrok import ngrok

from time import sleep

conf = pyngrok_config()
tcp_tunnel = ngrok.connect(addr=9999, proto="tcp", name="basher", pyngrok_config=conf)
print(f"NGROK running {tcp_tunnel.public_url} -> yo mama")
sleep(5)
print("shutdown!")
ngrok.disconnect(tcp_tunnel.public_url)