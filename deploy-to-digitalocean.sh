#!/bin/bash

# Digital Ocean WordPress Migration Script
# This script migrates your local WordPress to a Digital Ocean droplet

set -e

echo "================================================"
echo "WordPress to Digital Ocean Migration Script"
echo "================================================"

# Configuration
read -p "Enter your Digital Ocean droplet IP: " DROPLET_IP
read -p "Enter SSH user (usually 'root'): " SSH_USER
read -p "Enter MySQL root password on DO: " -s MYSQL_ROOT_PASS
echo
read -p "Enter WordPress database password for DO: " -s WP_DB_PASS
echo

# Export local database
echo "1. Exporting local database..."
docker exec wp-mysql mysqldump -u wordpress -pwordpress_password wordpress > wordpress_backup.sql

# Prepare files for transfer
echo "2. Preparing files for transfer..."
tar -czf wp-content.tar.gz wp-content/

# Connect to DO and backup existing installation
echo "3. Connecting to Digital Ocean droplet..."
ssh $SSH_USER@$DROPLET_IP << 'ENDSSH'
# Backup existing WordPress if it exists
if [ -d "/var/www/html/wp-content" ]; then
    echo "Backing up existing WordPress..."
    tar -czf /root/wp-backup-$(date +%Y%m%d-%H%M%S).tar.gz -C /var/www/html wp-content
    mysqldump -u root -p wordpress > /root/wp-db-backup-$(date +%Y%m%d-%H%M%S).sql
fi
ENDSSH

# Transfer files to DO
echo "4. Transferring files to Digital Ocean..."
scp wp-content.tar.gz $SSH_USER@$DROPLET_IP:/tmp/
scp wordpress_backup.sql $SSH_USER@$DROPLET_IP:/tmp/

# Install on DO
echo "5. Installing on Digital Ocean..."
ssh $SSH_USER@$DROPLET_IP << ENDSSH
# Stop Apache during migration
systemctl stop apache2

# Extract wp-content
cd /var/www/html
rm -rf wp-content.backup
if [ -d "wp-content" ]; then
    mv wp-content wp-content.backup
fi
tar -xzf /tmp/wp-content.tar.gz

# Import database
mysql -u root -p$MYSQL_ROOT_PASS wordpress < /tmp/wordpress_backup.sql

# Update wp-config.php with DO database credentials
sed -i "s/define('DB_PASSWORD', 'CHANGE_ON_DEPLOYMENT');/define('DB_PASSWORD', '$WP_DB_PASS');/" /var/www/html/wp-config.php
sed -i "s/define('DB_HOST', 'mysql:3306');/define('DB_HOST', 'localhost');/" /var/www/html/wp-config.php

# Set proper permissions
chown -R www-data:www-data /var/www/html
find /var/www/html -type d -exec chmod 755 {} \;
find /var/www/html -type f -exec chmod 644 {} \;

# Generate new salts
SALT=$(curl -s https://api.wordpress.org/secret-key/1.1/salt/)
printf '%s\n' "g/put your unique phrase here/d" a "$SALT" . w | ed -s /var/www/html/wp-config.php

# Restart Apache
systemctl start apache2

# Clean up
rm /tmp/wp-content.tar.gz
rm /tmp/wordpress_backup.sql

echo "Migration completed successfully!"
ENDSSH

# Clean up local files
rm wp-content.tar.gz
rm wordpress_backup.sql

echo "================================================"
echo "Migration Complete!"
echo "Your WordPress site is now live at: http://$DROPLET_IP"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Update your DNS records to point to $DROPLET_IP"
echo "2. Set up SSL with: sudo certbot --apache"
echo "3. Update WordPress URLs in admin panel if needed"