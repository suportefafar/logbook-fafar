"""Armazenamento local das submissões e da fila de sincronização."""
import datetime
import getpass
import json
import socket
import sqlite3
import uuid


def create_submission(answers, complete, trigger="manual"):
    limits = {"name": 255, "registration_number": 100, "activity": 5000}
    cleaned = {}
    for key, limit in limits.items():
        value = answers.get(key, "").strip()
        if len(value) > limit or (key != "activity" and ("\n" in value or "\r" in value)):
            raise ValueError("Campo inválido: " + key)
        if complete and not value:
            raise ValueError("Campo obrigatório: " + key)
        cleaned[key] = value
    def context(fn):
        try:
            return fn() or None
        except (OSError, KeyError):
            return None
    return {
        "client_submission_id": str(uuid.uuid4()),
        "form_key": "logbook", "form_version": 1,
        "completion_state": "complete" if complete else "partial",
        "recorded_at": datetime.datetime.now().astimezone().isoformat(),
        "trigger": trigger, "client_version": "0.1.0",
        "client_context": {"os_username": context(getpass.getuser), "hostname": context(socket.gethostname)},
        "answers": cleaned,
    }


class Storage:
    def __init__(self, path):
        self.path = str(path)
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS submissions (id TEXT PRIMARY KEY, body TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'pending', remote_id TEXT)")

    def save(self, submission):
        body = json.dumps(submission, ensure_ascii=False, separators=(",", ":"))
        with sqlite3.connect(self.path) as db:
            db.execute("INSERT INTO submissions (id, body) VALUES (?, ?)", (submission["client_submission_id"], body))

    def list(self):
        with sqlite3.connect(self.path) as db:
            return [(json.loads(body), state) for body, state in db.execute("SELECT body, state FROM submissions ORDER BY rowid DESC")]

    def pending(self):
        with sqlite3.connect(self.path) as db:
            return list(db.execute("SELECT id, body FROM submissions WHERE state = 'pending' ORDER BY rowid"))

    def mark_synced(self, submission_id, remote_id):
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE submissions SET state = 'synced', remote_id = ? WHERE id = ?", (remote_id, submission_id))
