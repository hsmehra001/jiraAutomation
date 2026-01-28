# Jira Automation Web UI

A web application that provides browser-based access to Jira automation workflows for processing subtasks and creating standard development subtasks.

## Features

- **Task Processing**: Automatically process assigned subtasks (Open → In Progress → Completed) with work logging
- **Subtask Creation**: Create standard development subtasks under a parent story
- **Web Interface**: Clean, responsive UI accessible from any browser
- **Configurable**: Environment-based configuration for different deployments

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Network access to your Jira server

## Installation

1. Clone or download this project

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables (optional, defaults are provided):
```bash
export JIRA_SERVER=https://your-jira-server.com
export CUSTOM_FIELD_ID=customfield_10111
export CUSTOM_FIELD_VALUE="Your Value"
export DEFAULT_ESTIMATE=2h
export FLASK_HOST=0.0.0.0
export FLASK_PORT=5000
export DEBUG=False
```

## Configuration

The application uses environment variables for configuration:

- `JIRA_SERVER`: Your Jira server URL
- `CUSTOM_FIELD_ID`: Custom field ID for subtask creation
- `CUSTOM_FIELD_VALUE`: Value for the custom field
- `DEFAULT_ESTIMATE`: Default time estimate for subtasks
- `FLASK_HOST`: Host to bind the server (0.0.0.0 for all interfaces)
- `FLASK_PORT`: Port to run the server on (default: 5000)
- `DEBUG`: Enable debug mode (True/False)

Note: Jira PAT is now required for each request and must be provided by the user through the web interface.

## Running the Application

### Development Mode

```bash
python app.py
```

The application will be available at `http://localhost:5000`

### Production Mode

Using Gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Usage

### Process Tasks

1. Navigate to the "Process Tasks" page
2. Enter a Jira story key (e.g., PROJ-123)
3. Enter your Jira Personal Access Token (PAT)
4. Click "Process Tasks"
5. View the results showing actions taken for each subtask

### Create Subtasks

1. Navigate to the "Create Subtasks" page
2. Enter a Jira story key (e.g., PROJ-123)
3. Enter your Jira Personal Access Token (PAT)
4. Click "Create Subtasks"
5. View the list of created subtasks

## Deployment

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)

### Quick Deployment Options

#### Using systemd (Linux)

1. Create a systemd service file at `/etc/systemd/system/jira-automation.service`:

```ini
[Unit]
Description=Jira Automation Web UI
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/path/to/jira-automation-web-ui
Environment="PATH=/usr/bin"
ExecStart=/usr/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

2. Enable and start the service:

```bash
sudo systemctl enable jira-automation
sudo systemctl start jira-automation
```

### Using Docker

Build the image:

```bash
docker build -t jira-automation-web-ui .
```

Run the container:

```bash
docker run -d -p 5000:5000 \
  -e JIRA_SERVER=https://your-jira-server.com \
  -e CUSTOM_FIELD_ID=customfield_10111 \
  -e CUSTOM_FIELD_VALUE="Your Value" \
  -e DEFAULT_ESTIMATE=2h \
  -e FLASK_HOST=0.0.0.0 \
  -e FLASK_PORT=5000 \
  -e DEBUG=False \
  jira-automation-web-ui
```

### Using Nginx (Reverse Proxy for HTTPS)

Configure Nginx to proxy requests:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=services --cov=app --cov-report=html
```

For detailed testing instructions, see [TESTING.md](TESTING.md)

## Troubleshooting

### Port Already in Use

If port 5000 is already in use, set the `FLASK_PORT` environment variable to a different port:

```bash
export FLASK_PORT=8080
python app.py
```

Or specify it directly when running the application:

```bash
FLASK_PORT=8080 python app.py
```

### Authentication Errors

- Verify your Jira PAT is valid and not expired
- Ensure the PAT has appropriate permissions for the operations
- Check that the Jira server URL is correct

### Connection Errors

- Verify network connectivity to the Jira server
- Check firewall rules allow outbound connections
- Ensure the Jira server URL includes the protocol (https://)

### Subtask Creation Fails

- Verify the custom field ID exists in your Jira instance
- Check that the custom field value is valid
- Ensure you have permission to create subtasks in the project

## Security Notes

- Use HTTPS in production (via Nginx reverse proxy)
- Keep your Jira PAT secure and rotate regularly
- Consider implementing rate limiting for production use
- Don't store sensitive environment variables in plaintext in production

## License

MIT License
# jiraAutomation
