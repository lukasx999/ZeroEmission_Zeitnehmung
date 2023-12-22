#!/bin/bash

# webserver
/home/admin/01_RP-Zeitmessung/venv-webserver/bin/python /home/admin/01_RP-Zeitmessung/app.py &
echo "Webserver started"

sleep 5

# raw esp32 data
/home/admin/01_RP-Zeitmessung/venv-webserver/bin/python /home/admin/01_RP-Zeitmessung/raw_esp.py
echo "Raw_esp started"
