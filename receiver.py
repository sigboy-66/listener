# Module:       receiver.py
# Description:  Opens up a tcp socket on port config.tcp_port and logs each heartbeat to the log file specified
#               on the command line. The receiver exits upon the client closing the connection
#
# Usage:        python receiver <heartbeat-log-file>
import os
import socket
import sys
from datetime import datetime
from config import TCP_PORT, DEFAULT_LOG, LISTENER_IP

log_file = DEFAULT_LOG

# if log file on command line change the name/path of the heartbeat logfile
if len(sys.argv) == 2:
    log_file = sys.argv[1]

# remove logfile if it already exists
if os.path.exists(log_file):
    os.remove(log_file)

# open log for writing.
try:
    heartbeat_log = open(log_file, 'a')
except(IOError) as error:
    print(f"Error: Can't write to {log_file}: {error}")
    sys.exit(1)

#open a socket on port config.tcp_port
with heartbeat_log, socket.socket(socket.AF_INET, socket.SOCK_STREAM) as receiver_soc:
    receiver_soc.bind((LISTENER_IP, TCP_PORT))
    receiver_soc.listen()
    print(f"Listening on {TCP_PORT}")

    connection, address = receiver_soc.accept()
    with connection:
        print(f"Sender connected from {address}")
        # Loop until sender breaks connection
        while True:
            heartbeat = connection.recv(1024)
            if not heartbeat:
                print("Connection closed by the sender.")
                break
            message = heartbeat.decode()
            timestamp = datetime.now().isoformat()
            log_heartbeat = f"Received {timestamp} from {address[0]} - {message}\n"
            print(log_heartbeat.strip())
            heartbeat_log.write(log_heartbeat)
            heartbeat_log.flush()