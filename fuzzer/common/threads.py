# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This is a function to capture the output of a process in real time and to apply a timeout without losing this output.
# It was initially designed for RFUZZ, where we dont necessarily have the control about the max duration of the fuzzing.

import subprocess
import threading

def capture_process_output(cmd, timeout=None):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, shell=True)

    # Flag to indicate if the process has finished
    process_finished = threading.Event()

    out_lines = []

    # Define a function to read process output
    def read_output():
        while not process_finished.is_set():
            output_line = process.stdout.readline()
            if output_line == '' and process.poll() is not None:
                break
            if output_line:
                out_lines.append(output_line)

    # Start a thread to read process output
    output_thread = threading.Thread(target=read_output)
    output_thread.start()

    # Wait for the process to finish or timeout
    try:
        process.wait(timeout=timeout)
    finally:
        process_finished.set()
        output_thread.join()

        # Terminate the process if it is still running
        if process.poll() is None:
            process.terminate()

        return out_lines
