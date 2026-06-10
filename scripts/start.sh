#!/bin/bash
cd "$(dirname "$0")/../backend-py"
nohup python3 main.py > /tmp/gitstat.log 2>&1 &
echo "Backend PID: $!"
sleep 3
if lsof -i :12580 > /dev/null 2>&1; then
  echo "Server is running on port 12580"
  open -a "Google Chrome" http://127.0.0.1:12580
else
  echo "Server failed to start. Check /tmp/gitstat.log"
  cat /tmp/gitstat.log
fi