# Module:       sender.py
# Description:  Sends number of heartbeats specified on the command line to receiver.py via a tcp socket. If not
#               specified on the command line the default is 1000. Each heartbeat is sent every config.heartbeat_interval
#               number of seconds.
#
# Usage:        python sender.py <number-of-heartbeats-to-send>

import socket
import time
import sys
from datetime import datetime
from config import tcp_port, heartbeat_interval
from time import thread_time_ns

receiver_ip = '127.0.0.1'  # receiver IP
heartbeats_to_send = 1000  # default number of heartbeats to send

# Change number of heartbeats to send if specified on the command line
if len(sys.argv) > 1:
    heartbeats_to_send = int(sys.argv[1])

# Open tcp socket to the sender
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sender_soc:
    sender_soc.connect((receiver_ip, tcp_port))
    print(f"Connected to server at {receiver_ip}:{tcp_port}")
    # Send the specified number of heart beats
    for heartbeat_num in range(heartbeats_to_send):
        #number and time stamp each hearbeat
        timestamp = datetime.now().isoformat()
        heartbeat = f"HEARTBEAT {heartbeat_num} at {timestamp}"
        sender_soc.sendall(heartbeat.encode())
        print(f"Sent: {heartbeat}")
        time.sleep(heartbeat_interval)
