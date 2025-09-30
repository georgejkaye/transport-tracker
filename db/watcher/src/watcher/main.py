import os
import sys
import time
from datetime import datetime, timedelta

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

last_trigger_time = datetime.now()


def get_db_scripts_files(code_dir: str) -> list[str]:
    code_files: list[str] = []
    for root, _, files in os.walk(code_dir):
        for filename in files:
            code_files.append(os.path.join(root, filename))
    return code_files


def run_in_scripts(code_dir: str):
    global last_trigger_time
    current_time = datetime.now()
    if (current_time - last_trigger_time) > timedelta(seconds=1):
        print("ex")
        last_trigger_time = current_time
        files = get_db_scripts_files(code_dir)
        for file in files:
            print(file)


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

    # Start the observer
    observer.start()
    print(f"Monitoring directory: {path}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main(sys.argv[1])
