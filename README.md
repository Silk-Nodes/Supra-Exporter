# Supra-Exporter
A simple promethus metrics exporter for Supra.

```bash
git clone https://github.com/Silk-Nodes/Supra-Exporter
pip3 install --user prometheus_client

# Run
cd Supra-Exporter
python3 supra-exporter.py
```

Metrics will now be exposed on port 8889 for you to pull into your external monitroing tools.

Create a simple systemd file.
```bash
sudo tee /etc/systemd/system/supra-exporter.service > /dev/null << EOF
[Unit]
Description=Supra Exporter
After=network-online.target

[Service]
User=$USER
ExecStart=$(which python3) $HOME/Supra-Exporter/supra-exporter.py
Restart=always
RestartSec=10
LimitNOFILE=infinity

[Install]
WantedBy=multi-user.target
EOF
```

```bash
sudo systemctl enable supra-exporter
sudo systemctl daemon-reload
sudo service supra-exporter start
```

```bash
# Confirm Metrics being exposed
curl -s localhost:8889/metrics/prometheus
```
