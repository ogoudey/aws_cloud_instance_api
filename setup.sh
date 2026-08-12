# install python venv

sudo apt update & sudo apt install -y python3.12-venv

python3 -m venv venv
. venv/bin/activate
pip install fastapi uvicorn requests boto3

sudo tee /etc/systemd/system/fastapi.service > /dev/null << 'EOF'
[Unit]
Description=Uvicorn Application Server
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/api
ExecStart=/home/ubuntu/api/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable fastapi.service
sudo systemctl start fastapi.service
