#!/usr/bin/env bash
cd `dirname $0`
exporter_home=`pwd`
sed -i "s@<exporter_home>@${exporter_home}@g"

systemctl stop p2peye_exporter
cp -f systemd/p2peye_exporter.service /usr/lib/systemd/system/
systemctl daemon-reload
rm -rf build dist/ __pycache__/ p2peye_exporter.spec
pyinstaller --onefile p2peye_exporter.py
systemctl start p2peye_exporter