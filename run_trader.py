import os
import sys
import subprocess


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def run_script(script_name):
    print("=" * 65)
    print(f"RUNNING: {script_name}")
    print("=" * 65)

    result = subprocess.run(
        [sys.executable, "-u", script_name],
        cwd=BASE_DIR
    )

    if result.returncode != 0:
        print(f"ERROR: {script_name} failed with code {result.returncode}")
        return False

    return True


def main():
    print("=" * 65)
    print("HAZEM AI NEWS TRADER - FULL ALERT RUNNER")
    print("=" * 65)

    if not run_script("signal_engine.py"):
        print("SYSTEM STOPPED: SIGNAL ENGINE FAILED")
        return

    if not run_script("gmail_signal_bridge.py"):
        print("SYSTEM WARNING: GMAIL ALERT FAILED")
        return

    print("=" * 65)
    print("FULL RUN COMPLETED")
    print("ALERT-ONLY MODE - NO AUTOMATIC TRADE")
    print("=" * 65)


if __name__ == "__main__":
    main()