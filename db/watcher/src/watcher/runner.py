import os
import subprocess
from pathlib import Path
from typing import Mapping

db_host = os.environ["DB_HOST"]
db_name = os.environ["DB_NAME"]
db_user = os.environ["DB_USER"]

with open(os.environ["DB_PASSWORD"]) as f:
    db_password = f.read().rstrip()


def run_in_script_file(script_file: Path):
    print(f"Running in {script_file}")
    env: Mapping[str, str] = dict(os.environ)
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
                str(script_file),
                "-q",
            ],
            stderr=subprocess.STDOUT,
            env=env,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error while running in {script_file}", flush=True)
        error_output = e.output.decode("utf-8")
        print(error_output, flush=True)
        print()
    else:
        pass
