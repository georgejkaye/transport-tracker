import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from watcher.processor import process_all_script_files


class MyEventHandler(FileSystemEventHandler):
    def __init__(
        self,
        internal_scripts_path: Path,
        user_scripts_path: Path,
        python_source_root: Path,
        python_output_module: str,
    ):
        self.last_trigger_time = datetime.now()
        self.internal_scripts_path = internal_scripts_path
        self.user_scripts_path = user_scripts_path
        self.python_source_root = python_source_root
        self.python_output_module = python_output_module

    def process_script_files_if_appropriate(self):
        current_time = datetime.now()
        if (current_time - self.last_trigger_time) > timedelta(seconds=1):
            process_all_script_files(
                self.internal_scripts_path,
                self.user_scripts_path,
                self.python_source_root,
                self.python_output_module,
            )

    def on_created(self, event: FileSystemEvent):
        self.process_script_files_if_appropriate()

    def on_modified(self, event: FileSystemEvent):
        self.process_script_files_if_appropriate()

    def on_moved(self, event: FileSystemEvent):
        self.process_script_files_if_appropriate()


def main(
    internal_scripts_path: Path,
    user_scripts_path: Path,
    python_source_root: Path,
    output_code_module: str,
):
    event_handler = MyEventHandler(
        internal_scripts_path,
        user_scripts_path,
        python_source_root,
        output_code_module,
    )
    observer = Observer()
    observer.schedule(event_handler, str(user_scripts_path), recursive=True)

    process_all_script_files(
        internal_scripts_path,
        user_scripts_path,
        python_source_root,
        output_code_module,
    )

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
    internal_scripts_path = Path(sys.argv[1])
    user_scripts_path = Path(sys.argv[2])
    python_source_root = Path(sys.argv[3])
    output_code_module = sys.argv[4]
    main(
        internal_scripts_path,
        user_scripts_path,
        python_source_root,
        output_code_module,
    )
