# WordPress to Digital Ocean Automated Deployment Workflow

## Overview
This is a complete CI/CD pipeline for deploying local WordPress development to Digital Ocean droplets automatically. When users clone this repo, Claude can execute this entire workflow without manual intervention.

## Prerequisites Check
1. Docker and Docker Compose installed
2. Python 3 with pip
3. Digital Ocean API token in `.env` file

## Complete Automated Workflow

### Phase 1: Local WordPress Setup
```bash
# 1. Start local WordPress development environment
docker-compose up -d

# 2. Verify containers are running
docker ps | grep wp-
```

### Phase 2: SSH Key Setup (One-time)
```bash
# 1. Run SSH setup script
./setup_ssh_and_deploy.sh

# This script will:
# - Generate SSH keypair at ~/.ssh/wordpress_deploy
# - Upload public key to Digital Ocean via API
# - Save SSH key ID to .ssh_key_id file
```

### Phase 3: Create Digital Ocean Droplet
```bash
# 1. Run droplet creation with SSH access
python3 create_droplet_with_ssh.py

# This will:
# - Create Ubuntu 22.04 droplet
# - Install WordPress via cloud-init
# - Configure MySQL with generated passwords
# - Enable SSH access with your key
# - Save credentials to .droplet_info
```

### Phase 4: Wait for WordPress Installation
```bash
# Check cloud-init status (takes 5-10 minutes)
ssh -i ~/.ssh/wordpress_deploy root@$(cat .droplet_info | python3 -c "import json,sys; print(json.load(sys.stdin)['ip_address'])") "cloud-init status --wait"
```

### Phase 5: Migrate Local WordPress to Droplet
```bash
# Run migration script
./migrate_to_droplet.sh

# This will:
# - Export local WordPress database
# - Package wp-content directory
# - Transfer to droplet via SCP
# - Import database
# - Update wp-config.php
# - Set proper permissions
```

## File Structure Required
```
wordpress-deployment/
├── .env                          # DO_API_TOKEN=your_token_here
├── docker-compose.yml            # Local WordPress stack
├── Dockerfile                    # Custom WordPress image
├── wp-config.php                # Environment-aware config
├── .htaccess                    # Apache rules
├── wp-content/                  # Themes and plugins
│   ├── themes/
│   │   └── my-custom-theme/
│   └── plugins/
│       └── custom-post-types/
├── create_droplet_with_ssh.py   # Creates DO droplet with SSH
├── setup_ssh_and_deploy.sh      # SSH key setup
├── migrate_to_droplet.sh        # Migration script
└── .claude/                     # Claude's memory
    └── wordpress_deployment_workflow.md

```

## Environment Variables (.env)
```bash
DO_API_TOKEN=your_digital_ocean_api_token
DROPLET_REGION=nyc3              # Optional
DROPLET_SIZE=s-1vcpu-1gb        # Optional
MYSQL_ROOT_PASSWORD=             # Optional, auto-generated if empty
WP_DB_PASSWORD=                  # Optional, auto-generated if empty
```

## Key Scripts Explanation

### setup_ssh_and_deploy.sh
- Generates ED25519 SSH keypair
- Uploads to DO via API
- Stores key ID for droplet creation

### create_droplet_with_ssh.py
- Creates Ubuntu 22.04 droplet
- Includes SSH key for passwordless access
- Runs cloud-init script to install LAMP + WordPress
- Outputs JSON to .droplet_info

### migrate_to_droplet.sh
- Reads .droplet_info for connection details
- Uses SSH key for authentication
- Exports local database
- Transfers wp-content
- Updates configuration for production

## Automated Execution Commands

For a fresh clone from GitHub, execute in order:

```bash
# 1. Install Python dependencies
pip3 install python-dotenv requests

# 2. Copy and configure environment
cp .env.example .env
# Edit .env and add DO_API_TOKEN

# 3. Start local WordPress
docker-compose up -d

# 4. Setup SSH (one-time)
./setup_ssh_and_deploy.sh

# 5. Create and deploy
python3 create_droplet_with_ssh.py

# 6. Wait for installation (5-10 minutes)
sleep 300

# 7. Migrate WordPress
./migrate_to_droplet.sh
```

## Troubleshooting Commands

```bash
# Check droplet info
cat .droplet_info | python3 -m json.tool

# Check SSH access
ssh -i ~/.ssh/wordpress_deploy root@$(cat .droplet_info | python3 -c "import json,sys; print(json.load(sys.stdin)['ip_address'])") "echo 'SSH OK'"

# Check WordPress installation
curl -I http://$(cat .droplet_info | python3 -c "import json,sys; print(json.load(sys.stdin)['ip_address'])")

# View cloud-init logs
ssh -i ~/.ssh/wordpress_deploy root@$(cat .droplet_info | python3 -c "import json,sys; print(json.load(sys.stdin)['ip_address'])") "tail -50 /var/log/cloud-init-output.log"

# Delete droplet (cleanup)
python3 -c "
import requests, json, os
api_token = os.getenv('DO_API_TOKEN')
with open('.droplet_info') as f:
    droplet_id = json.load(f)['droplet_id']
headers = {'Authorization': f'Bearer {api_token}'}
requests.delete(f'https://api.digitalocean.com/v2/droplets/{droplet_id}', headers=headers)
"
```

## Success Indicators
1. Local WordPress accessible at http://localhost
2. SSH key registered with DO (check .ssh_key_id exists)
3. Droplet created (check .droplet_info exists)
4. WordPress accessible at http://DROPLET_IP
5. Migration completes without errors

## Time Estimates
- SSH setup: 10 seconds
- Droplet creation: 1-2 minutes
- WordPress installation: 5-10 minutes (due to apt upgrade)
- Migration: 1-2 minutes
- **Total: ~10-15 minutes**

## Notes for Claude
- Always check for .env file with DO_API_TOKEN
- Ensure Docker is running before migration
- Wait for cloud-init to complete before migrating
- Use SSH key authentication (-i ~/.ssh/wordpress_deploy)
- Read .droplet_info for connection details
- The workflow is idempotent - can be re-run safely