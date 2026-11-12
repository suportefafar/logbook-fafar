"""Monitor da sessão e sincronizador de submissões."""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

import psutil

from logbook import database_path
from logbook_storage import Storage


def synchronize(storage, url, token):
    if not url or not token:
        return
    for submission_id, body in storage.pending():
        request = urllib.request.Request(url, data=body.encode("utf-8"), method="POST", headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "Idempotency-Key": submission_id,
        })
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                result = json.load(response)
                data = result["data"]
                if response.status in (200, 201) and data["client_submission_id"] == submission_id and data.get("id"):
                    storage.mark_synced(submission_id, str(data["id"]))
        except (OSError, ValueError, KeyError, urllib.error.URLError):
            return


def running(name):
    for process in psutil.process_iter(["name"]):
        try:
            if (process.info["name"] or "").lower() == name.lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--process", required=True, help="Nome exato do processo monitorado")
    parser.add_argument("--url", default=os.environ.get("LOGBOOK_API_URL"))
    args = parser.parse_args()
    storage = Storage(database_path())
    observed = False
    last_sync = 0
    while True:
        current = running(args.process)
        if observed and not current:
            subprocess.Popen([sys.executable, os.path.join(os.path.dirname(__file__), "logbook.py"), "form", "--trigger", "process_exit"])
        observed = current
        if time.monotonic() - last_sync >= 30:
            synchronize(storage, args.url, os.environ.get("LOGBOOK_API_TOKEN"))
            last_sync = time.monotonic()
        time.sleep(2)


if __name__ == "__main__":
    main()
