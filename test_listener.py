# Module:       test_listener.py
# Description:  Uses pytest to test the tcp sender receiver are fuctioning correctly. Test run are
#               1. Receiver logs heartbeat correctly.
#               2. All sender heartbeats are received
#               3. All sender heartbeat that are sent are timestamped the correct number of seconds apart
#               4. The reciever exits gracefully when no log path is given
#               5. Sender exits if no reciever is running
#               6. Receiver exits gracefully if it cant write to the specified log file
# Usage:        pytest -s --html=report.html --self-contained-html --log-file=pytestout.log test_listener.py

import subprocess
import time
import os
import pytest
from datetime import datetime
from config import heartbeat_interval, num_beats

receiver_exe = "receiver.py"
sender_exe = "sender.py"

def kill_processes(sender, receiver):
    """Kill the sender and receiver"""
    sender.terminate()
    sender.wait(timeout=5)
    receiver.terminate()
    receiver.wait(timeout=5)

def get_time_stamp(receiver_log_line):
    """
    :param receiver_log_line: log line from the reciever's log
    :return: iso time stamp of when the sender send the heartbeat
    """
    index = receiver_log_line.find("at ")
    time_stamp_index = index + 3
    time_stamp = receiver_log_line[time_stamp_index:].replace("\n", "")
    return time_stamp

def get_correct_pyhthon():
    """select python3 if not windows operating system"""
    if os.name != "nt":
        return "python3"
    else:
        return "python"

def test_heartbeat_logged_correctly():
    """Test basic heartbeat logging to file."""
    print("Testing heartbeat recorded correctly on receiver.")
    log_file = "listener1.log"
    receiver = subprocess.Popen(
        [get_correct_pyhthon(), receiver_exe, log_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Wait for receiver to be ready
    time.sleep(2.5)

    sender = subprocess.Popen(
        [get_correct_pyhthon(), sender_exe, "1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    time.sleep(heartbeat_interval + 2)  # Let at least one heartbeat be sent

    kill_processes(sender, receiver)

    with open(log_file) as f:
        contents = f.read()
        assert "HEARTBEAT" in contents
        assert "T" in contents  # ISO timestamp format

    os.remove(log_file)

def test_sender_receives_all_heartbeats():
    """Send 10 heart beats see if 10 are logged with heartbeat number"""
    global num_beats
    print(f"Testing receiver gets all {num_beats} heartbeats from the sender.")
    log_file = "listener2.log"

    receiver = subprocess.Popen(
        [get_correct_pyhthon(), receiver_exe, log_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    print("sleep 2.5 sec for receiver to be up")
    time.sleep(2.5)
    sender = subprocess.Popen(
        [get_correct_pyhthon(), sender_exe, str(num_beats)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    print("Waiting for sender to stop!!!")
    # wait for the sender to terminate
    while sender.poll() is None:
        print("Sender is still running")
        time.sleep(heartbeat_interval)
    print("Analyzing log file")
    count = 0
    # validate getting the packets in order
    with open(log_file, 'r') as file:
        for line in file:
            assert f"HEARTBEAT {count}" in line
            count += 1

    assert count == num_beats

    # make sure sender receiver dead before moving on
    kill_processes(sender, receiver)

    os.remove(log_file)


def test_receiver_heartbeats_received_timestamped_every_5_seconds_from_sender():
    """Validate a heart beat was received was time stamped every 5 seconds from the sender"""
    print(f"Testing the receiver gets the hearbeats stamped every {heartbeat_interval} seconds.")
    log_file = "listener3.log"
    global num_beats
    receiver = subprocess.Popen(
        [get_correct_pyhthon(), receiver_exe, log_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    time.sleep(2.5)
    sender = subprocess.Popen(
        [get_correct_pyhthon(), sender_exe, str(num_beats)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    print("Waiting for sender to stop!!!")
    # wait for the sender to terminate
    while sender.poll() is None:
        print("Sender is still running")
        time.sleep(heartbeat_interval)
    print("Analyzing log file")
    count = 0
    # Validate that the consecutive timestamps sent from the sender are 3 seconds apart
    with open(log_file, 'r') as file:
        for line in file:
            if count == 0:
                prev_timestamp = get_time_stamp(line)
            else:
                # calculate the time difference between timestamps send from the sender to 5 seconds
                curr_timestamp = get_time_stamp(line) # fetch the senders timestamp out of the receivers log
                time_delta = datetime.fromisoformat(curr_timestamp) - datetime.fromisoformat(prev_timestamp)
                print(f"Time dela is {time_delta.total_seconds()}")
                assert round(time_delta.total_seconds()) == heartbeat_interval
                prev_timestamp = curr_timestamp
            count += 1

    # make sure sender receiver dead before moving on
    kill_processes(sender, receiver)

    os.remove(log_file)

def test_missing_log_path_to_receiver():
    """Test receiver fails if log path is missing."""
    print("Testing graceful exit of receiver if no log file is provided on the command line.")
    result = subprocess.run(
        [get_correct_pyhthon(), receiver_exe],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    assert "Usage" in result.stdout or "Usage" in result.stderr


def test_sender_no_reciever():
    """Sender should fail to connect if receiver is down."""
    print("Testing sender exits if sender is not up.")
    result = subprocess.run(
        [get_correct_pyhthon(), sender_exe, "1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=5
       )
    assert "Connection refused" in result.stderr or "Failed to connect" in result.stderr or "ConnectionResetError" in result.stderr or result.returncode != 0

def test_log_write_permission_error():
    """Test receiver exits if gracefully if receiver cannot write to the heartbeat log"""
    print("Testing recever exits gracefully if it cannot write to the given log file.")
    if os.name != "nt":
        restricted_path = "/root/cannot_write.log"
    else:
        restricted_path = "C:\\Windows\\System32\\cannot_write.log"

    receiver = subprocess.Popen(
        [get_correct_pyhthon(), receiver_exe, restricted_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    time.sleep(1)
    return_code = receiver.poll()
    assert return_code is not None, "receiver did not exit as expected"
    out, err = receiver.communicate()
    assert "Permission" in err or "denied" in err or receiver.returncode != 0
    receiver.terminate()
    receiver.wait(timeout=5)

