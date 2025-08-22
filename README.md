# WordPress Development Environment for Digital Ocean

This is a Docker-based WordPress development environment that **exactly mirrors Digital Ocean's WordPress droplet**, ensuring seamless deployment.

## Features

- **Identical Stack to DO**: Ubuntu 22.04, Apache 2.4.52, PHP 8.3, MySQL 8.0.42
- **Custom Theme**: Ready-to-develop theme in `wp-content/themes/my-custom-theme/`
- **Custom Post Types Plugin**: Portfolio and Testimonials CPTs
- **One-Click Deployment**: Automated migration script to Digital Ocean
- **Environment-Aware Config**: wp-config.php works on both local and production

## Quick Start

1. **Start the development environment:**
```bash
docker-compose up -d
```

2. **Access your sites:**
- WordPress: http://localhost
- phpMyAdmin: http://localhost:8080

3. **Initial WordPress setup:**
- Go to http://localhost
- Follow the WordPress installation wizard
- Activate your custom theme: `My Custom Theme`
- Activate the plugin: `Custom Post Types`

## Development Workflow

### Working on Your Custom Theme
- Theme files: `wp-content/themes/my-custom-theme/`
- Changes are reflected immediately (no restart needed)

### Working on Custom Post Types
- Plugin files: `wp-content/plugins/custom-post-types/`
- After activation, you'll see Portfolio and Testimonials in the admin menu

## Deploying to Digital Ocean

### 1. Create a Digital Ocean Droplet
- Choose: WordPress on Ubuntu 22.04
- Select your preferred size (minimum 1GB RAM)
- Note your droplet's IP address

### 2. Run the Migration Script
```bash
./deploy-to-digitalocean.sh
```

The script will:
- Export your local database
- Package your wp-content
- Transfer everything to DO
- Configure the database
- Set proper permissions
- Generate security keys

### 3. Post-Deployment
After deployment:
1. Visit `http://YOUR_DROPLET_IP/wp-admin`
2. Update permalinks: Settings → Permalinks → Save
3. Set up SSL: `ssh root@YOUR_IP` then `certbot --apache`
4. Point your domain to the droplet IP

## File Structure
```
.
├── docker-compose.yml       # Docker configuration
├── Dockerfile              # Custom Apache/PHP image
├── wp-config.php          # Environment-aware config
├── .htaccess             # Apache rules
├── wp-content/
│   ├── themes/
│   │   └── my-custom-theme/    # Your custom theme
│   └── plugins/
│       └── custom-post-types/  # CPT plugin
└── deploy-to-digitalocean.sh   # Migration script
```

## Database Access

**Local Development:**
- Host: localhost:3306
- Database: wordpress
- User: wordpress
- Password: wordpress_password

**phpMyAdmin:** http://localhost:8080

## Troubleshooting

### Container won't start
```bash
docker-compose down -v  # Remove volumes
docker-compose up -d    # Start fresh
```

### Permission issues on Digital Ocean
```bash
ssh root@YOUR_IP
chown -R www-data:www-data /var/www/html
find /var/www/html -type d -exec chmod 755 {} \;
find /var/www/html -type f -exec chmod 644 {} \;
```

### Database connection errors after migration
Check `/var/www/html/wp-config.php` on your droplet and ensure the database credentials match.

## Security Notes

- Change all default passwords before production
- Update `wp-config.php` salts (done automatically during deployment)
- Enable firewall on Digital Ocean: `ufw allow 22,80,443/tcp && ufw enable`
- Keep WordPress, themes, and plugins updated

## Support

This setup ensures your local development environment is identical to Digital Ocean's WordPress droplet, making deployment seamless and predictable.