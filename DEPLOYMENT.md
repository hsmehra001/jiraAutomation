# Deployment Guide

## Quick Start

### 1. Install Dependencies

```bash
cd jira-automation-web-ui
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Set environment variables
export JIRA_SERVER=https://jira.sirionlabs.tech
export CUSTOM_FIELD_ID=customfield_10111
export CUSTOM_FIELD_VALUE="Platform Comm Mgmt"
export DEFAULT_ESTIMATE=2h
export FLASK_HOST=0.0.0.0
export FLASK_PORT=5000
export DEBUG=False
```

Required configuration:
- `JIRA_SERVER`: Your Jira server URL (e.g., https://jira.sirionlabs.tech)

Note: Jira PAT is now required for each request and must be provided by the user through the web interface.

### 3. Run the Application

Development mode:
```bash
python app.py
```

Production mode with Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 4. Access the Application

Open your browser and navigate to:
```
http://localhost:5000
```

Or from another machine on the network:
```
http://<server-ip>:5000
```

## Production Deployment

### Option 1: Systemd Service (Linux)

1. Copy application to server:
```bash
sudo mkdir -p /opt/jira-automation-web-ui
sudo cp -r * /opt/jira-automation-web-ui/
cd /opt/jira-automation-web-ui
```

2. Install dependencies:
```bash
sudo pip3 install -r requirements.txt
```

3. Configure environment variables:
```bash
# Create a systemd environment file (you can use env.example as a reference)
sudo cp env.example /etc/systemd/system/jira-automation.env
sudo nano /etc/systemd/system/jira-automation.env

# The file should contain environment variables like these
JIRA_SERVER=https://jira.sirionlabs.tech
CUSTOM_FIELD_ID=customfield_10111
CUSTOM_FIELD_VALUE="Platform Comm Mgmt"
DEFAULT_ESTIMATE=2h
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
DEBUG=False
```

4. Install systemd service:
```bash
sudo cp jira-automation.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable jira-automation
sudo systemctl start jira-automation
```

5. Check status:
```bash
sudo systemctl status jira-automation
```

6. View logs:
```bash
sudo journalctl -u jira-automation -f
```

### Option 2: Docker

1. Build the image:
```bash
docker build -t jira-automation-web-ui .
```

2. Run the container:
```bash
docker run -d \
  --name jira-automation \
  -p 5000:5000 \
  -e JIRA_SERVER=https://jira.sirionlabs.tech \
  -e CUSTOM_FIELD_ID=customfield_10111 \
  -e CUSTOM_FIELD_VALUE="Platform Comm Mgmt" \
  -e DEFAULT_ESTIMATE=2h \
  -e FLASK_HOST=0.0.0.0 \
  -e FLASK_PORT=5000 \
  -e DEBUG=False \
  --restart unless-stopped \
  jira-automation-web-ui
```

3. View logs:
```bash
docker logs -f jira-automation
```

4. Stop/start container:
```bash
docker stop jira-automation
docker start jira-automation
```

### Option 3: Docker Compose

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  jira-automation:
    build: .
    ports:
      - "5000:5000"
    environment:
      - JIRA_SERVER=https://jira.sirionlabs.tech
      - CUSTOM_FIELD_ID=customfield_10111
      - CUSTOM_FIELD_VALUE=Platform Comm Mgmt
      - DEFAULT_ESTIMATE=2h
      - FLASK_HOST=0.0.0.0
      - FLASK_PORT=5000
      - DEBUG=False
    restart: unless-stopped
    volumes:
      - ./app.log:/app/app.log
```

Run:
```bash
docker-compose up -d
```

## HTTPS Setup with Nginx

1. Install Nginx:
```bash
sudo apt-get update
sudo apt-get install nginx
```

2. Configure Nginx:
```bash
sudo cp nginx.conf.example /etc/nginx/sites-available/jira-automation
sudo ln -s /etc/nginx/sites-available/jira-automation /etc/nginx/sites-enabled/
```

3. Edit the configuration:
```bash
sudo nano /etc/nginx/sites-available/jira-automation
```

Update:
- `server_name` with your domain
- SSL certificate paths

4. Test and reload:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

5. Get SSL certificate (Let's Encrypt):
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Troubleshooting

### Port Already in Use

Check what's using the port:
```bash
sudo lsof -i :5000
```

Kill the process or change the port in the environment variables:
```bash
export FLASK_PORT=8080
```

Or update the port in your systemd environment file or Docker configuration.

### Permission Denied

Ensure the application directory has correct permissions:
```bash
sudo chown -R www-data:www-data /opt/jira-automation-web-ui
```

### Jira Connection Errors

Test connectivity:
```bash
curl -I https://jira.sirionlabs.tech
```

Verify PAT is valid:
```bash
curl -H "Authorization: Bearer YOUR_PAT" https://jira.sirionlabs.tech/rest/api/2/myself
```

### Application Won't Start

Check logs:
```bash
# Systemd
sudo journalctl -u jira-automation -n 50

# Docker
docker logs jira-automation

# Direct
tail -f app.log
```

Validate configuration:
```bash
python -c "from config import Config; print(Config.validate())"
```

## Security Best Practices

1. **Use HTTPS in production** - Always use Nginx with SSL
2. **Secure environment variables** - For systemd, restrict access to environment files:
   ```bash
   sudo chmod 600 /etc/systemd/system/jira-automation.env
   ```
3. **Rotate PAT regularly** - Instruct users to update their Jira tokens periodically
4. **Firewall rules** - Restrict access to trusted IPs:
   ```bash
   sudo ufw allow from 192.168.1.0/24 to any port 5000
   ```
5. **Keep dependencies updated**:
   ```bash
   pip list --outdated
   pip install --upgrade -r requirements.txt
   ```

## Monitoring

### Health Check

```bash
curl http://localhost:5000/api/health
```

### Log Monitoring

Set up log rotation:
```bash
sudo nano /etc/logrotate.d/jira-automation
```

Add:
```
/opt/jira-automation-web-ui/app.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

### Resource Monitoring

Monitor with htop:
```bash
sudo apt-get install htop
htop
```

## Backup

Backup configuration:
```bash
# For systemd deployment
sudo cp /etc/systemd/system/jira-automation.env jira-automation.env.backup

# Backup code and configuration files
tar -czf jira-automation-backup-$(date +%Y%m%d).tar.gz \
  config.py \
  README.md \
  jira-automation.service
```

## Updating

1. Stop the service:
```bash
sudo systemctl stop jira-automation
```

2. Backup current version:
```bash
sudo cp -r /opt/jira-automation-web-ui /opt/jira-automation-web-ui.backup
```

3. Update files:
```bash
sudo cp -r new-version/* /opt/jira-automation-web-ui/
```

4. Update dependencies:
```bash
cd /opt/jira-automation-web-ui
sudo pip3 install -r requirements.txt --upgrade
```

5. Restart service:
```bash
sudo systemctl start jira-automation
```

6. Verify:
```bash
curl http://localhost:5000/api/health
```
