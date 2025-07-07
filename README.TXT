The Repo exists at https://github.com/sigboy-66/tc-listener.git

You must have git installed. Execute the following command to get the listener code

git clone https://github.com/sigboy-66/listener.git

Requirements: Environment must have git and python installed
Also must have pytest and pytest-html installed

pip install pytest
pip install pytest-html

DESCRIPTION:

The 2 python files that do the work are sender.py and receiver.py. The receiver.py script listens on port tcp_port
defined in config.py. It logs numbered and time stamped heartbeats from the sender.py into a log file specified on
the command line. If no log file is specified a default one is created in the directory it is executed fromIt can simply
be started by executing the following command line

python receiver.py <path-to-heartbeat-log>

The receiver must be started first. The sender.py sends the specified number of heartbeats on the command line over the
tcp socket. If no number is supplied it will default to 1000 heartbeats. The heartbeats are sent at a time interval
specified by HEARTBEAT_INTERVAL in config.py. The sender can be started by executing the following command line.

python sender.py <number-of-heartbeats-to-send

The suite of tests is run in test_listener.py. It uses pytest to run and compile a report on the tests run. DO NOT
start the receiver or sender when running the test suite, the test_listener.py will start them using the python
subprocess library.  The tests run are as follows

1. Receiver logs heartbeat correctly.
2. All sender heartbeats are received
3. All sender heartbeat that are sent are timestamped the correct number of seconds apart
4. The creates as default heartbeat.log in when no log path is given to the receiver
5. Sender exits if no receiver is running
6. Receiver exits gracefully if it cant write to the specified log file

To run the pytest tests on the sender and receiver execute the following on the command line:

pytest --html=report.html --self-contained-html test_listener.py


You can get the results in compiled report.html
Add the -s argument to pytest command for debug messages
It will take about 3-4 minutes to run.


