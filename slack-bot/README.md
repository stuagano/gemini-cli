# Gemini Enterprise Architect Slack Bot

A comprehensive Slack bot integration that brings AI agent capabilities directly into team communication workflows. This bot connects to the Gemini Enterprise Architect agent server and provides powerful code analysis, architecture guidance, and development assistance through Slack.

## Features

### 🤖 AI Agent Integration
- **Analyst Agent**: Code analysis and performance metrics
- **Architect Agent**: System design and architecture guidance  
- **Developer Agent**: Code generation and implementation assistance
- **QA Agent**: Testing strategies and quality assurance
- **Scout Agent**: Duplicate detection and code pattern analysis
- **PM Agent**: Project planning and task management
- **PO Agent**: Feature prioritization and product guidance

### ⚡ Slash Commands
- `/gemini-analyze [code/file]` - Quick code analysis
- `/gemini-review [PR-URL]` - Get agent review of pull requests
- `/gemini-ask [question]` - Ask any agent a question
- `/gemini-killer-demo [repo]` - Run scaling analysis
- `/gemini-scout [search]` - Find duplicates or patterns
- `/gemini-architect [requirements]` - Get architecture advice

### 🔔 Real-time Notifications
- Guardian validation alerts
- Scout duplicate detection
- Killer demo critical issue warnings
- Build status and deployment notifications
- Performance degradation alerts
- Security vulnerability notifications

### 🎛️ Interactive Components
- Rich message formatting with code blocks
- Interactive buttons for follow-up actions
- Modal forms for complex inputs
- File upload handling for code analysis

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Slack workspace with admin permissions
- Gemini Enterprise Architect agent server running

### 1. Create Slack App

1. Go to [Slack API Apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Name your app "Gemini Enterprise Architect" and select your workspace
4. Configure the following:

#### OAuth & Permissions
Add these Bot Token Scopes:
```
app_mentions:read
channels:read
chat:write
chat:write.public
commands
files:read
groups:read
im:read
im:write
mpim:read
reactions:read
reactions:write
team:read
users:read
users:read.email
users.profile:read
```

#### Slash Commands
Create these commands pointing to your bot URL:
- `/gemini-analyze` → `https://your-domain.com/slack/events`
- `/gemini-review` → `https://your-domain.com/slack/events`
- `/gemini-ask` → `https://your-domain.com/slack/events`
- `/gemini-killer-demo` → `https://your-domain.com/slack/events`
- `/gemini-scout` → `https://your-domain.com/slack/events`
- `/gemini-architect` → `https://your-domain.com/slack/events`

#### Event Subscriptions
- Request URL: `https://your-domain.com/slack/events`
- Subscribe to bot events: `app_mention`, `message.channels`, `message.groups`, `message.im`

#### Interactive Components
- Request URL: `https://your-domain.com/slack/events`

### 2. Setup Environment

```bash
# Clone and navigate to slack-bot directory
cd slack-bot

# Copy environment template
cp .env.example .env

# Edit .env with your Slack app credentials
vim .env
```

### 3. Deploy with Docker

```bash
# Development deployment
docker-compose up -d

# Production deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 4. Install to Workspace

1. Visit `http://your-domain.com/slack/install`
2. Click the installation URL
3. Authorize the bot in your Slack workspace

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SLACK_BOT_TOKEN` | Bot token from Slack app | Yes |
| `SLACK_SIGNING_SECRET` | Signing secret for request verification | Yes |
| `SLACK_CLIENT_ID` | Client ID for OAuth flow | Yes |
| `SLACK_CLIENT_SECRET` | Client secret for OAuth flow | Yes |
| `AGENT_SERVER_URL` | URL of the agent server | Yes |
| `REDIS_URL` | Redis URL for production rate limiting | No |
| `DATABASE_URL` | Database URL for persistent storage | No |

### Channel Subscriptions

Configure which channels receive notifications:

```bash
# Subscribe #alerts channel to Guardian notifications
curl -X POST "http://your-domain.com/api/v1/management/teams/{team_id}/channels/subscribe" \
  -H "Content-Type: application/json" \
  -d '{
    "channel_id": "C1234567890",
    "notification_types": ["guardian_alert", "security_vulnerability"]
  }'
```

### User Preferences

Users can customize their notification preferences:

```bash
# Update user preferences
curl -X PUT "http://your-domain.com/api/v1/management/teams/{team_id}/users/{user_id}/preferences" \
  -H "Content-Type: application/json" \
  -d '{
    "dm_notifications": true,
    "preferred_agents": ["analyst", "architect"],
    "notification_schedule": {
      "start_hour": 9,
      "end_hour": 17,
      "timezone": "UTC"
    }
  }'
```

## Usage Examples

### Code Analysis
```
/gemini-analyze
```
```python
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
```

### Pull Request Review
```
/gemini-review https://github.com/owner/repo/pull/123
```

### Architecture Guidance
```
/gemini-architect I need to design a microservices architecture for an e-commerce platform with user management, inventory, and payment processing
```

### Duplicate Detection
```
/gemini-scout find similar functions in the authentication module
```

## API Reference

### Management Endpoints

#### List Teams
```http
GET /api/v1/management/teams
```

#### Get Team Configuration
```http
GET /api/v1/management/teams/{team_id}
```

#### Subscribe Channel
```http
POST /api/v1/management/teams/{team_id}/channels/subscribe
```

#### Update User Preferences
```http
PUT /api/v1/management/teams/{team_id}/users/{user_id}/preferences
```

### Webhook Endpoints

#### Guardian Alerts
```http
POST /webhooks/guardian
```

#### Scout Findings
```http
POST /webhooks/scout
```

#### Build Notifications
```http
POST /webhooks/builds
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Slack App     │    │   Slack Bot     │    │  Agent Server   │
│                 │    │                 │    │                 │
│ • Slash Commands│◄──►│ • FastAPI       │◄──►│ • Enhanced      │
│ • Interactive   │    │ • OAuth Manager │    │   Agents        │
│   Components    │    │ • Rate Limiter  │    │ • Nexus Core    │
│ • Events        │    │ • Notifications │    │ • Scout Indexer │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Persistence   │
                       │                 │
                       │ • Redis Cache   │
                       │ • PostgreSQL    │
                       │ • File Storage  │
                       └─────────────────┘
```

## Development

### Local Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set up pre-commit hooks
pre-commit install

# Run tests
pytest

# Start development server
python -m uvicorn main:app --reload --port 3000
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_commands.py
```

### Code Quality

```bash
# Format code
black .
isort .

# Lint code
flake8
mypy .

# Security check
bandit -r .
```

## Monitoring

### Health Checks
- `/health` - Application health status
- `/metrics` - Prometheus metrics
- `/debug/config` - Configuration debug (dev only)

### Logging
Structured logging with correlation IDs for request tracing.

### Metrics
- Request rates and response times
- Error rates by type
- Agent usage statistics
- Team and user activity

## Security

### Request Validation
- Slack signature verification
- Rate limiting per team/user
- Input sanitization
- OAuth 2.0 flow

### Data Protection
- No persistent storage of sensitive data
- Encrypted configuration values
- Secure token handling

## Deployment

### Production Deployment

1. Use Docker Compose with production overrides
2. Configure external Redis and PostgreSQL
3. Set up SSL/TLS termination
4. Configure monitoring and alerting
5. Set up backup and disaster recovery

### Kubernetes Deployment

```yaml
# See k8s/ directory for complete manifests
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gemini-slack-bot
spec:
  replicas: 3
  selector:
    matchLabels:
      app: gemini-slack-bot
  template:
    spec:
      containers:
      - name: slack-bot
        image: gemini-slack-bot:latest
        ports:
        - containerPort: 3000
```

## Troubleshooting

### Common Issues

1. **Bot not responding to commands**
   - Check Slack app configuration
   - Verify request URL endpoints
   - Check application logs

2. **OAuth installation fails**
   - Verify redirect URI configuration
   - Check client ID and secret
   - Ensure HTTPS for production

3. **Agent server connection errors**
   - Verify AGENT_SERVER_URL
   - Check network connectivity
   - Review agent server logs

4. **Rate limiting issues**
   - Check rate limit configuration
   - Monitor Redis connectivity
   - Review usage patterns

### Support

- Check the [documentation](https://your-docs.com/slack-bot)
- Review [troubleshooting guide](https://your-docs.com/troubleshooting)
- Contact support: support@your-domain.com

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

Copyright (c) 2024 Gemini Enterprise Architect. All rights reserved.