import os

# tmpdir
if "CASCADE_ENV_SOURCED" not in os.environ:
    raise Exception("The Cascade environment must be sourced prior to running the Python recipes.")

PATH_TO_TMP = os.path.join(os.environ['CASCADE_DATADIR'])
os.makedirs(PATH_TO_TMP, exist_ok=True)

PATH_TO_FIGURES = os.environ['CASCADE_PATH_TO_FIGURES']
os.makedirs(PATH_TO_FIGURES, exist_ok=True)

DO_ASSERT = True
DO_EXPENSIVE_ASSERT = False # More expensive assertions

NO_REMOVE_TMPFILES = False # Used for debugging purposes.

RUN_TIMEOUT_SECONDS = 60*60*2 # A program is not supposed to run longer than this in RTL simulation.
