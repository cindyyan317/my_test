# playback for line 
# playback.py log.txt 200

# example of log 
#2023-10-09 23:55:33.084628 (src/web/RPCServerHandler.h:147) [0x00007f85fa7fc700] RPC:NFO [601841126] http received request from work queue: 
#{"jsonrpc":"1.0","id":"wallet-rpc-client","method":"account_tx","params":[{"account":"rMovKurqd9y9KqXJnUDfUTgz8SmuzSi7Ei","ledger_index":"current",
#"ledger_index_min":"83109239"}]} ip = 34.206.141.159
import sys
import re
import http.client
import json
import time
import argparse
import pprint
from datetime import datetime

HOST = "127.0.0.1"

def send_http_request(request,retry = 0):
    while True:
        try:
            conn = http.client.HTTPConnection(HOST, 51233)
            conn.request("POST","/", body=request)
            response = conn.getresponse()
            response = response.read().decode('utf-8')
        except OSError:
            if retry == 0:
                print("ERROR: connection refused, stop trying")
                break
            retry -= 1
            print("ERROR: connection refused, retrying")
            time.sleep(30)
            continue
        try:
            json.loads(response)
            return
        except:
            print("ERROR:",request, response)

def parser():
    parser = argparse.ArgumentParser(description='log helper')
    parser.add_argument('log_file', help='log file', type = str)
    parser.add_argument('start_line', help='start line', type = int)
    parser.add_argument('end_line', help='end line, -1 means the end of the file', type = int)
    parser.add_argument('--dry', help='not issue the request', action='store_true')
    parser.add_argument('--ip', help='print ip states', action='store_true')
    parser.add_argument('--network', help='print http/ws states', action='store_true')
    parser.add_argument('--request', help='print request states', action='store_true')
    parser.add_argument('--cut', help='print log', action='store_true')
    parser.add_argument('--interval', help='sample the states by interval (s)', type = int, required = False, default = 0)
    return parser.parse_args()

last = None
types_ip = {}
def sample(time,req_json,req_type,ip):
    global methods_map,types_ip,args
    method = req_json["method"] if "method" in req_json else req_json["command"]
    methods_map[method] = methods_map.get(method,0) + 1
    types_ip_key = req_type + '_' +ip
    types_ip[types_ip_key] = types_ip.get(types_ip_key,0) + 1

def print_and_clear(args):
    global methods_map,types_ip,network_map
    if args.ip:
        print("type_ip:request_count")
        pprint.pprint(types_ip)
    if args.network:
        print("ws or http new/closed: count")
        pprint.pprint(network_map)
    if args.request:
        print("method: count")
        pprint.pprint(methods_map)
    methods_map = {}
    types_ip = {}
    network_map = {}

def filter_request(line,args):
    res = re.search(r'(.*) \(.+(http|ws) received request from work queue: ({.*}) ip = (.*)', line)
    if res:
        time = res.group(1)
        req_type = res.group(2)
        request_str = res.group(3)
        ip = res.group(4)
        try:
            json_obj = json.loads(request_str)
        except:
            print(number_line, 'ERROR: cannot parse json string :',request_str)
            return
        if not "method" in json_obj and req_type == "http":
            print(number_line, 'ERROR: no method in request :',request_str)
            return
        sample(time,json_obj,req_type,ip)
        if "params" in json_obj and (json_obj["params"] == [] or json_obj["params"] == [None] or json_obj["params"] == None):
            json_obj["params"] = [{}]
            print(number_line, 'amended request: ' + str(json_obj))
        if not args.dry:
            send_http_request(json.dumps(json_obj),2)

network_map = {}
def filter_network(line):
    global network_map,last_network_timestamp
    if 'http session created' in line:
        network_map['http_new'] = network_map.get('http_new',0) + 1
    if 'http session closed' in line:
        network_map['http_closed'] = network_map.get('http_closed',0) + 1
    if '] session created' in line:
        network_map['ws_new'] = network_map.get('ws_new',0) + 1
    if '] session closed' in line:
        network_map['ws_closed'] = network_map.get('ws_closed',0) + 1
    
def check_interval(line,args):
    global last
    res = re.search(r'(.*) \(.+', line)
    if res:
        cur_time = datetime.strptime(res.group(1), '%Y-%m-%d %H:%M:%S.%f')
        if last != None:
            delta = cur_time - last
            if delta.total_seconds() > args.interval:
                print("From " + str(last) + " to " + str(cur_time) + ":")
                print_and_clear(args)
                last = cur_time
        else:
            last = cur_time
        


#methods states
methods_map = {}

args = parser()

logfile = args.log_file
start_line = args.start_line
end_line = args.end_line

with open(logfile) as f:
    number_line = 0
    for line in f:
        number_line += 1
        if number_line < start_line or (end_line != -1 and number_line > end_line):
            continue
        if args.cut:
            print(line)
            continue
        if args.interval != 0:
            check_interval(line,args)
        if args.request or args.ip:
            filter_request(line,args)
        if args.network:
            filter_network(line)
            
print("From " + str(last) + " to end:")
print_and_clear(args)

