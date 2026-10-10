#!/bin/bash
/usr/bin/avahi-publish -a -R htmp.local 192.168.31.10 &
PID1=$!
/usr/bin/avahi-publish -a -R htmpchat.local 192.168.31.10 &
PID2=$!

trap "kill -TERM $PID1 $PID2 2>/dev/null; exit 0" SIGINT SIGTERM
wait
