# Module:       sender.py
# Description:  Sends number of heartbeats specified on the command line to receiver.py via a tcp socket. If not
#               specified on the command line the default is 1000. Each heartbeat is sent every config.HEARTBEAT_INTERVAL
#               number of seconds.
#
# Usage:        python sender.py <number-of-heartbeats-to-send>

import socket
import time
import sys
from datetime import datetime
from config import TCP_PORT, BEATS, RECEIVER_IP, HEARTBEAT_INTERVAL, MAX_BEATS
from time import thread_time_ns

receiver_ip = '127.0.0.1'  # receiver IP

# Change number of heartbeats to send if specified on the command line
if len(sys.argv) > 1:
    BEATS = int(sys.argv[1])
else:
    BEATS = MAX_BEATS

# Open tcp socket to the sender
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sender_soc:
    sender_soc.connect((RECEIVER_IP, TCP_PORT))
    print(f"Connected to receiver at {RECEIVER_IP}:{TCP_PORT}")
    # Send the specified number of heart beats
    for heartbeat_num in range(BEATS):
        #number and time stamp each heartbeat
        timestamp = datetime.now().isoformat()
        heartbeat = f"HEARTBEAT {heartbeat_num} at {timestamp}"
        sender_soc.sendall(heartbeat.encode())
        print(f"Sent: {heartbeat}")
        time.sleep(HEARTBEAT_INTERVAL)
