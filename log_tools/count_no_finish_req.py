
import re

req_count = {}

files = ['clio_2024-10-14_15-35-31.log', 'clio_2024-10-14_20-28-15.log', 'clio_2024-10-15_01-01-36.log']
dirpath = '/Users/cyan/tmp_code/memory_leak_2024/faraday/'
for file in files:
    with open(dirpath + file, 'r', encoding = "ISO-8859-1") as f:
        for line in f:
            if 'Received request from' in line:
                res = re.search(r'(\[\d*\])', line)
                if res:
                    session_id = res.group(1)
                    req_count[session_id] = req_count.get(session_id, 0) + 1

            if 'Request processing duration' in line or 'Could not create Web context' in line:
                res = re.search(r'(\[\d*\])', line)
                if res:
                    session_id = res.group(1)
                    if not session_id in req_count:
                        print(f"Request {session_id} not found in req_count")
                    req_count[session_id] = req_count.get(session_id, 0) - 1
                    if req_count[session_id] == 0:
                        req_count.pop(session_id)


print('unfinished requests in session:', req_count)
