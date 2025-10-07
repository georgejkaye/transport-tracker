#!/bin/sh

poetry run python \
    -u \
    src/watcher/main.py \
    /app/internal \
    /app/user \
    /app/output \
    $GENERATED_CODE_MODULE