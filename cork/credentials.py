import json
CRED = None
with open("secrets.json", "r") as f:
    CRED = json.load(f)

def pyngrok_config():
    from pyngrok.conf import PyngrokConfig
    s = CRED["pyngrok"]
    res = PyngrokConfig(**s)
    return res