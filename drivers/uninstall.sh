name=$1
service=SH_$name
ROOT=$PWD/drivers/$name
sudo systemctl stop $service
sudo systemctl disable $service
sudo rm /lib/systemd/system/$service.service
sudo rm -r $ROOT

sudo systemctl daemon-reload
sudo systemctl reset-failed
