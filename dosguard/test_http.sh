#!/bin/bash

# send curl cmd to clio to test dosguard behavior 

max_requests=10

loop=$((max_requests-1))

for i in $( eval echo {0..$loop} ); do \
  out=$(curl 'localhost:51233' -sd '{ "method": "server_info", "params": [{}]}'| grep success)

  if [ -z "$out" ]; then
     echo "cmd not success =>$i"
     echo $out
     exit 1
  else
     echo "cmd success =>$i"
  fi
done

out=$(curl 'localhost:51233' -sd '{ "method": "server_info", "params": [{}]}'| grep over)
echo $out
if [ -z "$out" ]; then
    echo "dosguard request limit check fail"
    exit 1
else
    echo "dosguard request limit check ok"
fi
