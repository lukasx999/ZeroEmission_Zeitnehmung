#!/usr/bin/env bash
set -euxo pipefail

# Upload backend code to RPi

user=admin
ip=10.0.0.242
remote=${user}@${ip}

rsync -r ./01_RP-Zeitmessung/ ${remote}:/var/www/01_RP-Zeitmessung
ssh $remote "sudo systemctl restart apache2"
