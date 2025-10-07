import time
from datetime import datetime, timedelta
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from watcher.processor import process_all_script_files

last_trigger_time = datetime.now()


def run_in_scripts(internal_scripts_path: Path, user_scripts_path: Path):
    global last_trigger_time
    current_time = datetime.now()
    if (current_time - last_trigger_time) > timedelta(seconds=1):
        process_all_script_files(internal_scripts_path, user_scripts_path)
        last_trigger_time = datetime.now()


class MyEventHandler(FileSystemEventHandler):
    def __init__(self, internal_scripts_path: Path, user_scripts_path: Path):
        self.internal_scripts_path = internal_scripts_path
        self.user_scripts_path = user_scripts_path

    def on_created(self, event: FileSystemEvent):
        run_in_scripts(self.internal_scripts_path, self.user_scripts_path)

    def on_modified(self, event: FileSystemEvent):
        run_in_scripts(self.internal_scripts_path, self.user_scripts_path)

    def on_moved(self, event: FileSystemEvent):
        run_in_scripts(self.internal_scripts_path, self.user_scripts_path)


def main(internal_scripts_path: Path, user_scripts_path: Path):
    event_handler = MyEventHandler(internal_scripts_path, user_scripts_path)
    observer = Observer()
    observer.schedule(event_handler, str(user_scripts_path), recursive=True)

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
    code_dir = Path("/home/george/docs/repos/train-tracker/db/code")
    dest_path = Path("/home/george/docs/repos/train-tracker/api/src")
    output_module = "api.dbgen"
    internal_path = Path(
        "/home/george/docs/repos/train-tracker/db/watcher/scripts"
    )
    process_all_script_files(dest_path, output_module, internal_path, code_dir)
