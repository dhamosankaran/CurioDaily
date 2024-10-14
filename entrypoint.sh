#!/bin/bash

if [ "$RUN_SCRIPT" = "DailyNewsRun" ]; then
    python /autonomous_newsletter/app/DailyJobs/DailyNewsRun.py
elif [ "$RUN_SCRIPT" = "DailyEmailRun" ]; then
    python /autonomous_newsletter/app/DailyJobs/DailyEmailRun.py
else
    # Default behavior: run the web application
    exec gunicorn --bind :$PORT --workers 1 --worker-class uvicorn.workers.UvicornWorker --threads 8 app.main:app
fi

