#!/bin/bash
cd /home/ubuntu/besti
. .venv/bin/activate
exec .venv/bin/gunicorn --workers 8 --timeout 300 app:app
