"""Interface local de registro e consulta do LogBook."""
import argparse
import os
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from logbook_storage import Storage, create_submission


def database_path():
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    directory = Path(base) / "logbook-fafar"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / "logbook.sqlite"


def form(storage, trigger):
    root = tk.Tk()
    root.title("Registro de uso")
    root.geometry("550x340")
    for row, label in enumerate(("Nome do Usuário", "Matrícula", "O que faz aqui?")):
        ttk.Label(root, text=label).grid(row=row, column=0, sticky="nw", padx=10, pady=10)
    name, registration = ttk.Entry(root, width=45), ttk.Entry(root, width=45)
    activity = tk.Text(root, width=45, height=7)
    for row, widget in enumerate((name, registration, activity)):
        widget.grid(row=row, column=1, sticky="ew", padx=10, pady=10)
    root.columnconfigure(1, weight=1)

    def save(complete):
        answers = {"name": name.get(), "registration_number": registration.get(), "activity": activity.get("1.0", "end-1c")}
        try:
            storage.save(create_submission(answers, complete, trigger))
        except Exception as error:
            messagebox.showerror("Não foi possível salvar", str(error), parent=root)
            return
        root.destroy()

    def close():
        if messagebox.askyesno("Fechar registro", "Salvar os dados preenchidos e fechar?", parent=root):
            save(False)

    ttk.Button(root, text="Registrar", command=lambda: save(True)).grid(row=3, column=1, pady=12)
    root.protocol("WM_DELETE_WINDOW", close)
    root.mainloop()


def history(storage):
    root = tk.Tk()
    root.title("LogBook — histórico local")
    root.geometry("900x400")
    columns = ("data", "nome", "matricula", "atividade", "situacao", "envio")
    table = ttk.Treeview(root, columns=columns, show="headings")
    for column, label in zip(columns, ("Data", "Nome", "Matrícula", "O que faz aqui?", "Situação", "Envio")):
        table.heading(column, text=label)
        table.column(column, width=140)
    table.pack(fill="both", expand=True)
    for submission, state in storage.list():
        answers = submission["answers"]
        table.insert("", "end", values=(submission["recorded_at"], answers.get("name"), answers.get("registration_number"), answers.get("activity"), submission["completion_state"], state))
    root.mainloop()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("form", "history"), nargs="?", default="history")
    parser.add_argument("--trigger", choices=("manual", "process_exit"), default="manual")
    args = parser.parse_args()
    storage = Storage(database_path())
    form(storage, args.trigger) if args.mode == "form" else history(storage)


if __name__ == "__main__":
    main()
