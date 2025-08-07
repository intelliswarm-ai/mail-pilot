# Docker Setup for Mail Pilot 🐳

This guide explains how to run Mail Pilot using Docker and Docker Compose.

## Prerequisites

1. **Docker and Docker Compose installed**
2. **Gmail API credentials** (`credentials.json` in parent directory)
3. **Environment configuration** (`.env` file in parent directory)

## Quick Start

### 1. Prepare Configuration Files

Place these files in the **parent directory** of mail-pilot:

```
parent-directory/
├── credentials.json    # Gmail API credentials
├── .env               # Configuration file
└── mail-pilot/        # Project directory
    ├── docker-compose.yml
    └── ...
```

### 2. Start the Services

```bash
# Start all services (mail-pilot + ollama)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 3. Initial Setup

The first time you run the container, you need to generate the Gmail token:

```bash
# Generate token.json for first-time setup
docker-compose exec mail-pilot python main.py --once
```

This will create `../token.json` which will be persisted for future runs.

## Services

### Mail Pilot Application
- **Port 5000**: Web interface
- **Port 8000**: Backend API
- **Command**: Runs web application by default

### Ollama (Local LLM)
- **Port 11434**: Ollama API
- **Model**: Downloads `mistral` automatically on first run

## Configuration

### Environment Variables in `.env`

```env
# Gmail settings (required)
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# Ollama settings (defaults work with docker-compose)
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL=mistral

# Scheduling (hours)
SUMMARY_INTERVAL=6

# Voice features
VOICE_ENABLED=true
VOICE_LANGUAGE=en
```

### Volume Mounts

- `../credentials.json` → `/app/credentials.json` (read-only)
- `../token.json` → `/app/token.json` (read-write)
- `../.env` → `/app/.env` (read-only)
- `./logs` → `/app/logs` (persistent logs)
- `./summaries` → `/app/summaries` (persistent summaries)

## Usage Options

### Web Interface (Default)
```bash
docker-compose up -d
# Access at http://localhost:5000
```

### Command Line Interface
```bash
# Run once manually
docker-compose exec mail-pilot python main.py --once

# Run with interactive menu
docker-compose exec mail-pilot python main.py --menu

# Run scheduled service
docker-compose exec mail-pilot python main.py
```

### Custom Commands
```bash
# Override the default command
docker-compose run --rm mail-pilot python main.py --status
```

## Troubleshooting

### Check Service Status
```bash
# View all containers
docker-compose ps

# Check logs
docker-compose logs mail-pilot
docker-compose logs ollama
```

### Download Ollama Model Manually
```bash
# Download mistral model
docker-compose exec ollama ollama pull mistral

# List available models
docker-compose exec ollama ollama list
```

### Rebuild After Code Changes
```bash
# Rebuild the mail-pilot image
docker-compose build mail-pilot

# Restart with new image
docker-compose up -d --force-recreate mail-pilot
```

### File Permissions
If you encounter permission issues:
```bash
# Fix ownership of log and summary directories
sudo chown -R $(whoami):$(whoami) logs summaries
```

## Production Considerations

1. **Security**: Use secrets management instead of `.env` files
2. **Persistence**: Ensure `ollama-data` volume is backed up
3. **Resources**: Allocate adequate CPU/RAM for Ollama model
4. **Monitoring**: Add health checks and logging
5. **Updates**: Pin specific image versions instead of `:latest`

## Development

### Local Development with Docker
```bash
# Mount source code for development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### Accessing Container Shell
```bash
# Access mail-pilot container
docker-compose exec mail-pilot bash

# Access ollama container
docker-compose exec ollama bash
```

## Network Architecture

```
┌─────────────┐     ┌──────────────┐
│ Mail Pilot  │────▶│ Ollama       │
│ (port 5000) │     │ (port 11434) │
└─────────────┘     └──────────────┘
       │
       ▼
┌─────────────┐     ┌──────────────┐
│ Gmail API   │     │ SMTP Server  │
│ (external)  │     │ (external)   │
└─────────────┘     └──────────────┘
```

Both services communicate over the `mail-pilot-network` Docker network.