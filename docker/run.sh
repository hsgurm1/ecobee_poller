#!/bin/bash
while true
do
   python3 /etc/poller.py
   tail -n 4 /var/log/ecobee.log
   printf "Next run in 5 min \n"
   sleep 300
done
