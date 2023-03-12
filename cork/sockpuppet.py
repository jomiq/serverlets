import atexit
from credentials import pyngrok_config
from pyngrok.ngrok import NgrokTunnel
from pyngrok import ngrok

tcp_tunnel = NgrokTunnel()

def start_ngrok(port:int = 9999, whimsical=True):
    global tcp_tunnel
    name = "tcp_tunnel" 
    if whimsical:
        try:
            from random_word import RandomWords as RW
            r = RW()
            name = r.get_random_word()
        except Exception as e:
            print("Install random-word to enable the whimsical option.")
            raise(e)

    conf = pyngrok_config()
    tcp_tunnel = ngrok.connect(addr=port, proto="tcp", name=name, pyngrok_config=conf)
    atexit.register(ngrok_cleanup)


def ngrok_cleanup():
    for t in ngrok.get_tunnels():
        ngrok.disconnect(t.public_url)
    
