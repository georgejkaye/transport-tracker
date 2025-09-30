import os
import subprocess
import sys
import time
from datetime import datetime, timedelta

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

db_host = os.environ["DB_HOST"]
db_name = os.environ["DB_NAME"]
db_user = os.environ["DB_USER"]

with open(os.environ["DB_PASSWORD"]) as f:
    db_password = f.read().rstrip()

last_trigger_time = datetime.now()


def get_db_scripts_files(code_dir: str) -> list[str]:
    code_files: list[str] = []
    for root, _, files in os.walk(code_dir):
        for filename in files:
            code_files.append(os.path.join(root, filename))
    return code_files


def run_in_script_file(script_file: str):
    env = dict(os.environ)
    env["PGPASSWORD"] = db_password
    try:
        subprocess.check_output(
            [
                "psql",
                "-h",
                db_host,
                "-d",
                db_name,
                "-U",
                db_user,
                "-f",
                script_file,
                "-q",
            ],
            stderr=subprocess.STDOUT,
            env=env,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error while running in {script_file}", flush=True)
        error_output = e.output.decode("utf-8")
        print(error_output, flush=True)
    else:
        pass
    print()


def run_in_scripts(code_dir: str):
    global last_trigger_time
    current_time = datetime.now()
    if (current_time - last_trigger_time) > timedelta(seconds=1):
        files = get_db_scripts_files(code_dir)
        for file in files:
            run_in_script_file(file)
        last_trigger_time = datetime.now()


class MyEventHandler(FileSystemEventHandler):
    def __init__(self, path: str):
        self.path = path

    def on_created(self, event: FileSystemEvent):
        run_in_scripts(self.path)

    def on_modified(self, event: FileSystemEvent):
        run_in_scripts(self.path)

    def on_moved(self, event: FileSystemEvent):
        run_in_scripts(self.path)


def main(path: str):
    event_handler = MyEventHandler(path)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)

    # Start the observe
    observer.start()
    print(f"Watching script files in: {path}", flush=True)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main(sys.argv[1])
