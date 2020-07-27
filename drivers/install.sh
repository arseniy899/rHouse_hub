URL=$1
getName=$2
if [ "$3" != "" ]; then
	name=$3
else
    name=$2
fi
ROOT=$PWD/drivers/$name
service=SH_$name

sudo mkdir -m 777 $ROOT/
cd $ROOT
curl -sS $URL > install.zip
unzip -o install.zip
rm install.zip
sudo chmod -R 777 $ROOT

sudo cat > /lib/systemd/system/$service.service  <<EOF
[Unit]
Description=Smart House Driver: $name
After=multi-user.target
 
[Service]
Type=simple
ExecStart=/usr/bin/python3 $ROOT/main.py
Restart=always
RestartSec=3
 
[Install]
WantedBy=multi-user.target
EOF

sudo chmod 644 /lib/systemd/system/$service.service
sudo chmod +x $ROOT/main.py
sudo systemctl daemon-reload
sudo systemctl enable $service.service
sudo systemctl start $service.service