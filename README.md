

# Systemd

```
sudo systemctl link /home/pi/Projects/cricket_stat/cricket.service
sudo systemctl enable cricket.service
sudo systemctl status cricket.service
sudo systemctl start cricket.service
```

```
journalctl -u cricket.service
```
