#!/bin/bash
set -e;
cd ~/dict_server
source venv/bin/activate
python3 -m uvicorn main:app --host 127.0.0.1 --port 8866