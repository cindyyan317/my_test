
# mm = {}

# with open("err_ip", "r") as file:
#     for line in file:
#         ip = line.split(":")[0]
#         count = line.split(":")[1]
#         mm[ip] = count
#         print (ip)

# ret = {}
# with open("err_ip2", "r") as file:
#     for line in file:
#         ip = line.split(":")[0]
#         count = int(line.split(":")[1][:-2])
#         if ip in mm:
#             print(ip + ":" + str(count))
#             ret[ip] = count

# with open("safe_ip", "r") as file:
#     for line in file:
#         ip = line.split(":")[0]
#         count = int(line.split(":")[1][:-2])
#         if ip in ret:
#             ret[ip] = 0

# x = dict(sorted(ret.items(), key=lambda item: item[1]))
# y = {}
# for key,val in x.items():
#     key = key[key.find("_")+1:-1]
#     print(key)
#     y[key] = val

# print (y)

# ret = {}
# with open("/Users/cyan/tmp_code/memory_leak_2024/faraday/clio_2024-10-15_01-01-36.log", "r", encoding = "ISO-8859-1") as file:
#     for line in file:
#         if '} ip =' in line:
#             ip = line.split(" ")[-1]
#             ip = ip[:-1]
#             if ip in y and y[ip] > 0:
#                 ret[ip] = line
                
# for i in ret:
#     print(i,ret[i])


cc = {}
for filename in ['','','']:
    with open(filename, 'r') as ff:
        for line in ff:
            #job begin
            if 'received request from work queue:' in line:
                ip = line.split(' ')[-1]
                if ip in cc:
                    cc[ip] += 1
                else:
                    cc[ip] -= 1
                    if cc[ip] == 0:
                        del cc[ip]
            else ''
            #job end
