# Module:       test_listener.py
# Description:  Uses pytest to test the tcp sender receiver are functioning correctly. Test run are
#               1. Receiver logs heartbeat correctly.
#               2. All sender heartbeats are received
#               3. All sender heartbeat that are sent are timestamped the correct number of seconds apart
#               4. The reciever exits gracefully when no log path is given
#               5. Sender exits if no reciever is running
#               6. Receiver exits gracefully if it cant write to the specified log file
#
# Usage:        pytest --html=report.html --self-contained-html --log-file=pytestout.log test_listener.py

import subprocess
import time
import os
import pytest
from datetime import datetime
from config import HEARTBEAT_INTERVAL, BEATS, DEFAULT_LOG

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

def wait_for_process_to_complete(monitoring_proc, process_name):
    """checks ever HEARTBEAT_INTERVAL till the given process proc finishes if not wait 2x times BEATS sent and kill them"""
    wait_count = 0
    print(f"Waiting for {process_name} to complete")
    while monitoring_proc.poll() is None:
        print(f"{process_name} is still running")
        time.sleep(HEARTBEAT_INTERVAL)
        if wait_count == BEATS * 2:
            print(f"The {process_name} is taking to long killing the process")
            monitoring_proc.terminate()
            monitoring_proc.wait(timeout=5)
            break
        wait_count += 1

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

    time.sleep(HEARTBEAT_INTERVAL + 2)  # Let at least one heartbeat be sent

    kill_processes(sender, receiver)

    with open(log_file) as f:
        contents = f.read()
        assert "HEARTBEAT" in contents
        assert "T" in contents  # ISO timestamp format

    os.remove(log_file)

def test_sender_receives_all_heartbeats():
    """Send 10 heart beats see if 10 are logged with heartbeat number"""
    print(f"Testing receiver gets all {BEATS} heartbeats from the sender.")
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
        [get_correct_pyhthon(), sender_exe, str(BEATS)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # wait for sender to stop
    wait_for_process_to_complete(sender, "sender")

    print("Analyzing log file")
    count = 0
    # validate getting the packets in order
    with open(log_file, 'r') as file:
        for line in file:
            assert f"HEARTBEAT {count}" in line
            count += 1

    assert count == BEATS

    # make sure sender receiver dead before moving on
    kill_processes(sender, receiver)

    os.remove(log_file)


def test_receiver_heartbeats_received_timestamped_every_5_seconds_from_sender():
    """Validate a heart beat was received was time stamped every 5 seconds from the sender"""
    print(f"Testing the receiver gets the heartbeats stamped every {HEARTBEAT_INTERVAL} seconds.")
    log_file = "listener3.log"

    receiver = subprocess.Popen(
        [get_correct_pyhthon(), receiver_exe, log_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    time.sleep(2.5)
    sender = subprocess.Popen(
        [get_correct_pyhthon(), sender_exe, str(BEATS)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    #wait for the sender to terminate
    wait_for_process_to_complete(sender, "sender")

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
                assert round(time_delta.total_seconds()) == HEARTBEAT_INTERVAL
                prev_timestamp = curr_timestamp
            count += 1

    # make sure sender receiver dead before moving on
    kill_processes(sender, receiver)

    os.remove(log_file)

def test_missing_log_path_to_receiver_use_default_log_file():
    """Test receiver fails if log path is missing."""
    print("Testing if default log file created if no log file is provided on the command line.")
    # remove default log if it exists already
    if os.path.exists(DEFAULT_LOG):
        os.remove(DEFAULT_LOG)

    receiver = subprocess.Popen(
        [get_correct_pyhthon(), receiver_exe],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    # wait for sender to come up
    time.sleep(2.5)
    sender = subprocess.Popen(
        [get_correct_pyhthon(), sender_exe, "1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    wait_for_process_to_complete(sender, "sender")


    assert os.path.exists(DEFAULT_LOG)
    os.remove(DEFAULT_LOG)

def test_sender_no_receiver():
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

