git clone --recurse-submodules https://github.com/NVIDIA/Isaac-GR00T
cd Isaac-GR00T

curl -LsSf https://astral.sh/uv/install.sh | sh

sudo apt-get update && sudo apt-get install -y ffmpeg

uv sync --python 3.12

# Non-groot dependencies
uv add fastapi uvicorn requests boto3

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
