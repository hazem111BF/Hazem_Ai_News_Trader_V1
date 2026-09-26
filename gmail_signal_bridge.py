import os
import json
import hashlib
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SIGNAL_FILE = os.path.join(BASE_DIR, "latest_signal.json")
SENDER_FILE = os.path.join(BASE_DIR, "send_signal_email.py")
HASH_FILE = os.path.join(BASE_DIR, ".last_signal_hash")


def get_signal_hash():
    if not os.path.exists(SIGNAL_FILE):
        raise FileNotFoundError("latest_signal.json not found")

    with open(SIGNAL_FILE, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def send_email():
    result = subprocess.run(
        [sys.executable, SENDER_FILE],
        cwd=BASE_DIR,
        capture_output=True,
        text=True
    )

    print(result.stdout)

    if result.returncode != 0:
        print(result.stderr)
        return False

    return "SIGNAL EMAIL SENT SUCCESSFULLY" in result.stdout


def main():
    current_hash = get_signal_hash()

    previous_hash = None

    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r", encoding="utf-8") as f:
            previous_hash = f.read().strip()

    if current_hash == previous_hash:
        print("NO NEW SIGNAL - EMAIL NOT SENT")
        return

    print("NEW SIGNAL DETECTED")
    print("Sending Gmail alert...")

    if send_email():
        with open(HASH_FILE, "w", encoding="utf-8") as f:
            f.write(current_hash)

        print("GMAIL ALERT COMPLETED")
    else:
        print("GMAIL ALERT FAILED")


if __name__ == "__main__":
    main()