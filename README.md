# WordPress Claude Code Wizard 🚀

Automated WordPress development and deployment pipeline for Digital Ocean. Develop locally with Docker, deploy to production with one command.

## Features

- **Identical Stack to DO**: Ubuntu 22.04, Apache 2.4.52, PHP 8.3, MySQL 8.0.42
- **Custom Theme**: Ready-to-develop theme in `wp-content/themes/my-custom-theme/`
- **Custom Post Types Plugin**: Portfolio and Testimonials CPTs
- **One-Click Deployment**: Automated migration script to Digital Ocean
- **Environment-Aware Config**: wp-config.php works on both local and production

- Try SEO Grove: [SEO Grove](https://seogrove.ai/pre-registration)  
- Join my Skool to say thanks: [My Skool](https://www.skool.com/iss-ai-automation-school-6342)


## Quick Start

### 1. Setup Environment
```bash
# Clone the repository
git clone https://github.com/IncomeStreamSurfer/wordpress-claude-code-wizard.git
cd wordpress-claude-code-wizard

# Copy and configure .env
cp .env.example .env
# Edit .env and add your Digital Ocean API token
```

### 2. Local Development
```bash
# Start WordPress locally
docker-compose up -d

# Access at http://localhost
# phpMyAdmin at http://localhost:8080
```

### 3. Deploy to Digital Ocean
```bash
# One-time SSH setup
./setup_ssh_and_deploy.sh

# Create droplet and deploy
python3 create_droplet_with_ssh.py

# Wait 5-10 minutes for installation
# Then migrate your local WordPress
./migrate_now.sh
```

## Development Workflow

### Working on Your Custom Theme
- Theme files: `wp-content/themes/my-custom-theme/`
- Changes are reflected immediately (no restart needed)

### Working on Custom Post Types
- Plugin files: `wp-content/plugins/custom-post-types/`
- After activation, you'll see Portfolio and Testimonials in the admin menu

## Post-Deployment

After deployment:
1. Your site is live at `http://YOUR_DROPLET_IP`
2. Point your domain's A record to the droplet IP
3. Set up SSL: 
   ```bash
   ssh -i ~/.ssh/wordpress_deploy root@YOUR_IP
   certbot --apache
   ```

## File Structure
```
.
├── docker-compose.yml              # Docker configuration
├── Dockerfile                      # Custom Apache/PHP image
├── wp-config.php                   # Environment-aware config
├── .htaccess                       # Apache rules
├── setup_ssh_and_deploy.sh         # SSH key setup
├── create_droplet_with_ssh.py      # Droplet creation
├── migrate_now.sh                  # Migration script
├── wp-content/
│   ├── themes/
│   │   └── my-custom-theme/        # Your custom theme
│   └── plugins/
│       └── custom-post-types/      # CPT plugin
└── .claude/                        # Claude's workflow memory
```

## Database Access

**Local Development:**
- Host: localhost:3306
- Database: wordpress
- User: wordpress
- Password: wordpress_password

**phpMyAdmin:** http://localhost:8080

## Requirements

- Docker & Docker Compose
- Python 3 with pip
- Digital Ocean account with API token
- 10-15 minutes for complete deployment

## Security Notes

- Change all default passwords before production
- Update `wp-config.php` salts (done automatically during deployment)
- Enable firewall on Digital Ocean: `ufw allow 22,80,443/tcp && ufw enable`
- Keep WordPress, themes, and plugins updated

## How It Works

1. **Docker** provides identical environment to production
2. **SSH keys** are automatically configured for passwordless access
3. **Cloud-init** installs WordPress on the droplet
4. **Migration script** transfers your themes, plugins, and content
5. **URL updates** are handled automatically

From local development to live production in minutes!
