from websocket import create_connection

# max concurrect connection is 1
ws = create_connection("ws://localhost:51233")

ws.send('{"method": "server_info"}')
result =  ws.recv()
print("Received '%s'" % result)
assert('status":"success' in result)

# open new ws

ws1 = create_connection("ws://localhost:51233")

ws1.send('{"method": "server_info"}')
result =  ws1.recv()
print("Received '%s'" % result)
assert("You are placing too much load on the server" in result)

ws.close()
ws1.close()

print("Test pass")

