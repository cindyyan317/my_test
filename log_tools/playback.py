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
from websockets.sync.client import connect


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def warning(log):
    print(bcolors.WARNING + log + bcolors.ENDC)

def fail(log):
    print(bcolors.FAIL + log + bcolors.ENDC)

def bold(log):
    print(bcolors.BOLD + log + bcolors.ENDC)

HOST = "127.0.0.1"

def send_http_request(line,retry = 0):
    if 'Request processing duration' in line:
        #avoid process long request
        return
    res = re.search(r'(.*) \(.+http received request from work queue: ({.*}) ip = (.*)', line)
    if res:
        time = res.group(1)
        request_str = res.group(2)
        ip = res.group(3)
        try:
            json_obj = json.loads(request_str)
        except:
            fail(number_line+ ' ERROR: cannot parse json string :'+request_str)
            return
        if not "method" in json_obj and req_type == "http":
            fail(number_line+ ' ERROR: no method in request :'+request_str)
            return
        sample(time,json_obj,req_type,ip)
        if "params" in json_obj and (json_obj["params"] == [] or json_obj["params"] == [None] or json_obj["params"] == None):
            json_obj["params"] = [{}]      
        while True:
            try:
                conn = http.client.HTTPConnection(HOST, 51233)
                conn.request("POST","/", body=json.dumps(json_obj))
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

session_map = {}
# TODO: ports not enough
def send_ws_request(line):
    global session_map
    #step 1: get the session id
    res = re.search(r'\[(\d+)\] session (created|closed)', line)
    if res:
        session_id = res.group(1)
        if res.group(2) == "created":
            session_map[session_id] = connect(f"ws://{HOST}:51233")
            print("created ws session: " + session_id)
        else:
            print("closed ws session: " + session_id)
            if not session_id in session_map:
                warning("session {} not found".format(session_id))
            else:
                session_map[session_id].close()
                del session_map[session_id]
        return
    res = re.search(r'([.+]) ws received request from work queue: ({.*}) ip = (.*)', line)
    if res:
        session = res.group(1)
        request_str = res.group(2)
        ip = res.group(3) 
    #step 2: find the session in map
        if not session in session_map:
            warning("session {} not found".format(session))
            session_map[session_id] = connect(f"ws://{HOST}:51233")        
    #step 3: send the request
        session_map[session_id].send(request_str)


def parser():
    parser = argparse.ArgumentParser(description='log helper')
    parser.add_argument('log_file', help='log file', type = str)
    parser.add_argument('start_line', help='start line', type = int)
    parser.add_argument('end_line', help='end line, -1 means the end of the file', type = int)
    parser.add_argument('--replay_http', help='replay http request', action='store_true')
    parser.add_argument('--replay_ws', help='replay ws request', action='store_true')
    parser.add_argument('--ip', help='print ip states', action='store_true')
    parser.add_argument('--network', help='print http/ws states', action='store_true')
    parser.add_argument('--request', help='print request states', action='store_true')
    parser.add_argument('--cut', help='print log', action='store_true')
    parser.add_argument('--interval', help='sample the states by interval (s)', type = int, required = False, default = 0)
    parser.add_argument('--sub', help='print subscription detail',action='store_true')
    parser.add_argument('--timespan', help='only process log during the time range ', type = str, required = False, nargs=2, default = ["",""])
    parser.add_argument('--replay_all', help='replay all requests', action='store_true')
    parser.add_argument('--cmds', help='commands to replay', type = str, required = False, nargs='*')
    return parser.parse_args()

last = None
types_ip = {}
subscribe_map = {}
subscriber_set = set()
def sample(time,req_json,req_type,ip):
    global methods_map,types_ip,args
    method = req_json["method"] if "method" in req_json else req_json["command"]
    methods_map[method] = methods_map.get(method,0) + 1
    types_ip_key = req_type + '_' +ip
    types_ip[types_ip_key] = types_ip.get(types_ip_key,0) + 1

def print_and_clear(args):
    global methods_map,types_ip,network_map,subscribe_map,subscriber_set
    if args.ip:
        bold("type_ip:request_count")
        pprint.pprint(types_ip)
    if args.network:
        bold("ws or http new/closed: count")
        pprint.pprint(network_map)
    if args.request:
        bold("method: count")
        pprint.pprint(methods_map)
    if args.sub:
        bold("subscribe: count")
        pprint.pprint(subscribe_map)
        print("subscriber: count:" + str(len(subscriber_set)))
    methods_map = {}
    types_ip = {}
    network_map = {}
    subscribe_map = {}
    subscriber_set = set()

def is_in_timespan(line,args):
    res = re.search(r'(.*?) \[0x.+', line)
    if res:
        cur_time = datetime.strptime(res.group(1), '%Y-%m-%d %H:%M:%S.%f')
        if args.timespan[0] != "" and cur_time < datetime.strptime(args.timespan[0], '%Y-%m-%d %H:%M:%S.%f'):
            return False,True
        if args.timespan[1] != "" and cur_time > datetime.strptime(args.timespan[1], '%Y-%m-%d %H:%M:%S.%f'):
            return False,False
    return True,True

def filter_request(line,args):
    if 'Request processing duration' in line:
        #avoid process long request
        return
    res = re.search(r'(.*) \[0x.+(http|ws) received request from work queue: ({.*}) ip = (.*)', line)
    if res:
        time = res.group(1)
        req_type = res.group(2)
        request_str = res.group(3)
        ip = res.group(4)
        try:
            json_obj = json.loads(request_str)
        except:
            fail(str(number_line)+ ' ERROR: cannot parse json string :'+request_str)
            return
        if not "method" in json_obj and req_type == "http":
            fail(str(number_line)+ ' ERROR: no method in request :'+request_str)
            return
        sample(time,json_obj,req_type,ip)

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
    res = re.search(r'(.*?) \[.+', line)
    if res:
        cur_time = datetime.strptime(res.group(1), '%Y-%m-%d %H:%M:%S.%f')
        if last != None:
            delta = cur_time - last
            if delta.total_seconds() > args.interval:
                warning("From " + str(last) + " to " + str(cur_time) + ":")
                print_and_clear(args)
                last = cur_time
        else:
            last = cur_time

def fileter_sub(line):
    global subscriber_set,subscribe_map
    if 'Request processing duration' in line:
        #avoid process long request
        return
    res = re.search(r'(.*) \[0x.+ws received request from work queue: ({.*}) ip = (.*)', line)
    if res:
        try:
            request_str = res.group(2)
            ip = res.group(3)
            json_obj = json.loads(request_str)
        except:
            print(number_line, 'ERROR: cannot parse json string :',request_str)
            return
        for key in ('command','method'):
            for ty in ('accounts','books','accounts_proposed','streams'):
                if key in json_obj and json_obj[key] == "subscribe":
                    subscriber_set.add(ip)
                    if ty in json_obj:
                        if len(json_obj[ty])>10000:
                            fail(res.group(1) +' WARNING: too many subscriptions: session id:'+res.group(2)+" accounts count: "+str(len(json_obj[ty])))
                        subscribe_map[ty] = subscribe_map.get(ty,0) + len(json_obj[ty])


def send_requests(line,cmds):
    if not 'received request from work queue' in line:
        return
    res = re.search(r'(\{.*\})', line)
    if res:
        request = res.group(1)
        request_json = json.loads(request)
        if not 'method' in request_json and 'command' not in request_json:
            print('Invalid request', request_json)
            return
        if 'command' in request_json:
            method = request_json.pop("command")
            params = [request_json]
            request_json = {"method":method,"params":params}
        if cmds == None or request_json['method'] in cmds:
            print("requests", line, '\n')
            try:
                conn = http.client.HTTPConnection(HOST, 51233)
                conn.request("POST","/", body=json.dumps(request_json))
                response = conn.getresponse()
                response = response.read().decode('utf-8')
                print("response",response)
                time.sleep(0.5)
            except OSError:
                print("ERROR: connection refused, retrying")
                time.sleep(1)
            
            
#methods states
methods_map = {}

args = parser()

logfile = args.log_file
start_line = args.start_line
end_line = args.end_line

with open(logfile,"r", encoding = "ISO-8859-1") as f:
    number_line = 0
    for line in f:
        number_line += 1
        if number_line < start_line:
            continue
        if (end_line != -1 and number_line > end_line):
            break
        within, continuing = is_in_timespan(line,args)
        if not continuing:
            break
        if not within:
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
        if args.sub:
            fileter_sub(line)
        if args.replay_http:
            send_http_request(line)
        if args.replay_ws:
            send_ws_request(line)
        if args.replay_all:
            send_requests(line,args.cmds)
            
if last:
    warning("From " + str(last) + " to end:")
print_and_clear(args)

