from websocket import create_connection
import time

max_requests = 10

ws = create_connection("ws://localhost:51233")
# bad syntax
for i in range(0,max_requests):
    ws.send("{}")
# print("Sent")
# print("Receiving...")
    result =  ws.recv()
    print("Received '%s'" % result)
    assert("badSyntax" in result)

ws.send("{}")
result =  ws.recv()
print("Received '%s'" % result)
assert("You are placing too much load on the server" in result)

#sleep interval 20s, request can be served normally

time.sleep(20)
ws.send('{"method": "server_info"}')
result =  ws.recv()
print("Received '%s'" % result)
assert('status":"success' in result)
ws.close()

print("Test pass")



