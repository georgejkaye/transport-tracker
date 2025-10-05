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


def run_in_scripts(internal_scripts_path: str, user_scripts_path: str):
    global last_trigger_time
    current_time = datetime.now()
    if (current_time - last_trigger_time) > timedelta(seconds=1):
        internal_files = get_db_scripts_files(internal_scripts_path)
        for file in internal_files:
            run_in_script_file(file)
        user_files = get_db_scripts_files(user_scripts_path)
        for file in user_files:
            run_in_script_file(file)
        last_trigger_time = datetime.now()


class MyEventHandler(FileSystemEventHandler):
    def __init__(self, internal_scripts_path: str, user_scripts_path: str):
        self.internal_scripts_path = internal_scripts_path
        self.user_scripts_path = user_scripts_path

    def on_created(self, event: FileSystemEvent):
        run_in_scripts(self.internal_scripts_path, self.user_scripts_path)

    def on_modified(self, event: FileSystemEvent):
        run_in_scripts(self.internal_scripts_path, self.user_scripts_path)

    def on_moved(self, event: FileSystemEvent):
        run_in_scripts(self.internal_scripts_path, self.user_scripts_path)


def main(internal_scripts_path: str, user_scripts_path: str):
    event_handler = MyEventHandler(internal_scripts_path, user_scripts_path)
    observer = Observer()
    observer.schedule(event_handler, user_scripts_path, recursive=True)

    # Start the observe
    observer.start()
    print(f"Watching script files in: {user_scripts_path}", flush=True)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
