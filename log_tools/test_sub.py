import http.client
import json
import asyncio
from websockets.sync.client import connect

jjs = {
         "command" : "subscribe",
         "streams": ["ledger","transactions"]
      }
with connect(f"ws://127.0.0.1:51233") as websocket:
    s = json.dumps(jjs)
    websocket.send(s)
    message = websocket.recv()
    res = json.loads(message)
    print(res)
    # message = websocket.recv()
    # res = json.loads(message)
    # print(res)
    print("sleeping")
    import time

    time.sleep(10)
    print("sleep over")
