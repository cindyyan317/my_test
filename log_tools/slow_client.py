
server_ip = "127.0.0.1"
port = 6006

import asyncio
import websockets
import time

async def slow_client(uri):
    async with websockets.connect(uri, ping_interval = 1) as websocket:
        message = '{"command":"subscribe", "streams":["validations","transactions","ledger"]}'
        print(f"Sending: {message}") 
        await websocket.send(message)
        while True:
            #disable ping pong

            # Receive a message from the server
            response = await websocket.recv()
            print(f"Received: {response}")

            # Simulate slow processing of the response
            print("sleep")
            time.sleep(10) 

uri = "ws://localhost:51233" 

# Run the client
asyncio.get_event_loop().run_until_complete(slow_client(uri))
