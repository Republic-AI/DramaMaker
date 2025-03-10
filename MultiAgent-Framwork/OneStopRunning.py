import subprocess
import time
import os
import signal
import configparser

def load_config():
    config = configparser.ConfigParser()

    # Get the path of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.ini')

    # Log the config path to verify it is being loaded from the correct location
    print(f"Loading config from: {config_path}")

    # Read the config file
    config.read(config_path)

    # Print out the sections found in config file
    print(f"Sections found in config: {config.sections()}")

    # Check if the 'Paths' section exists
    if 'Paths' not in config:
        raise KeyError("'Paths' section not found in the config file.")

    conda_base = config['Paths']['conda_base']
    running_cwd = config['Paths']['running_cwd']
    socket_cwd = config['Paths']['socket_cwd']

    return conda_base, running_cwd, socket_cwd

def run_processes():
    # Load paths from config.ini
    conda_base, running_cwd, socket_cwd = load_config()

    # Construct the commands to activate the conda environment and run the scripts
    running_command = f"/bin/bash -c 'source {conda_base}/etc/profile.d/conda.sh && conda activate aitown && python3 Running.py'"
    socket_command = f"/bin/bash -c 'source {conda_base}/etc/profile.d/conda.sh && conda activate aitown && python3 Socket.py'"

    # Start Running.py first
    running_process = subprocess.Popen(running_command, shell=True, cwd=running_cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print("Started Running.py")

    # Wait for 2 seconds before starting Socket.py
    time.sleep(2)

    # Start Socket.py after the delay
    socket_process = subprocess.Popen(socket_command, shell=True, cwd=socket_cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print("Started Socket.py after 2 seconds delay")

    return running_process, socket_process


def print_output(process, name):
    # Print the output and errors of the process in real-time
    for line in iter(process.stdout.readline, b''):
        # Use errors='replace' to handle decoding errors gracefully
        print(f"[{name} OUTPUT]: {line.decode(errors='replace').strip()}")

def kill_processes(running_process, socket_process):
    # Terminate the Running.py process
    if running_process.poll() is None:  # If the process is still running
        os.kill(running_process.pid, signal.SIGTERM)
        print("Running.py terminated.")
    
    # Terminate the Socket.py process
    if socket_process.poll() is None:  # If the process is still running
        os.kill(socket_process.pid, signal.SIGTERM)
        print("Socket.py terminated.")

def main():
    # Start both Running.py and Socket.py
    print("Starting Running.py and Socket.py...")
    running_process, socket_process = run_processes()

    # Print output of both processes in real-time
    print("Streaming output from Running.py and Socket.py...")
    try:
        while True:  # Keep the processes running indefinitely
            running_line = running_process.stdout.readline()
            if running_line:
                print(f"[Running.py]: {running_line.decode(errors='replace').strip()}")
            socket_line = socket_process.stdout.readline()
            if socket_line:
                print(f"[Socket.py]: {socket_line.decode(errors='replace').strip()}")

            # Check if either process has terminated early
            if running_process.poll() is not None or socket_process.poll() is not None:
                print("One of the processes has terminated early.")
                break

    except KeyboardInterrupt:
        print("Interrupted by user.")

    # Time to forcefully kill both processes if they are still running
    print("Killing Running.py and Socket.py...")
    kill_processes(running_process, socket_process)

if __name__ == "__main__":
    main()
