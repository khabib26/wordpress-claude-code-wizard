#!/bin/bash

# WordPress to Digital Ocean Droplet Migration Script
# Automatically migrates local WordPress to newly created droplet

set -e

echo "================================================"
echo "WordPress to Digital Ocean Migration"
echo "================================================"

# Check if .droplet_info exists
if [ ! -f ".droplet_info" ]; then
    echo "❌ No droplet info found. Please run: python3 create_droplet.py first"
    exit 1
fi

# Read droplet info
DROPLET_IP=$(python3 -c "import json; print(json.load(open('.droplet_info'))['ip_address'])")
MYSQL_ROOT_PASS=$(python3 -c "import json; print(json.load(open('.droplet_info'))['mysql_root_pass'])")
WP_DB_PASS=$(python3 -c "import json; print(json.load(open('.droplet_info'))['wp_db_pass'])")
DROPLET_NAME=$(python3 -c "import json; print(json.load(open('.droplet_info'))['droplet_name'])")

echo "Found droplet: $DROPLET_NAME at $DROPLET_IP"
echo ""

# Test SSH connection
echo "Testing SSH connection..."
SSH_USER="root"
SSH_KEY="$HOME/.ssh/wordpress_deploy"
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if ssh -i $SSH_KEY -o ConnectTimeout=5 -o StrictHostKeyChecking=no $SSH_USER@$DROPLET_IP "echo 'SSH connection successful'" 2>/dev/null; then
        echo "✅ SSH connection established"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo "Waiting for droplet to be ready... ($RETRY_COUNT/$MAX_RETRIES)"
        sleep 10
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ Could not establish SSH connection after $MAX_RETRIES attempts"
    exit 1
fi

# Wait for WordPress to be configured
echo "Waiting for WordPress configuration to complete..."
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SSH_USER@$DROPLET_IP << 'ENDSSH'
while [ ! -f /root/.wordpress_configured ]; do
    echo "WordPress still configuring..."
    sleep 5
done
echo "WordPress configuration complete!"
ENDSSH

# Export local database
echo "1. Exporting local database..."
docker exec wp-mysql mysqldump -u wordpress -pwordpress_password wordpress > wordpress_backup.sql

# Update URLs in SQL dump to use droplet IP
echo "2. Updating URLs in database..."
sed -i.bak "s|http://localhost|http://$DROPLET_IP|g" wordpress_backup.sql

# Prepare files for transfer
echo "3. Preparing files for transfer..."
tar -czf wp-content.tar.gz wp-content/

# Backup existing WordPress on droplet
echo "4. Backing up existing WordPress on droplet..."
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SSH_USER@$DROPLET_IP << 'ENDSSH'
if [ -d "/var/www/html/wp-content" ]; then
    echo "Backing up existing WordPress..."
    tar -czf /root/wp-backup-$(date +%Y%m%d-%H%M%S).tar.gz -C /var/www/html wp-content
fi
ENDSSH

# Transfer files to droplet
echo "5. Transferring files to Digital Ocean..."
scp -i $SSH_KEY -o StrictHostKeyChecking=no wp-content.tar.gz $SSH_USER@$DROPLET_IP:/tmp/
scp -i $SSH_KEY -o StrictHostKeyChecking=no wordpress_backup.sql $SSH_USER@$DROPLET_IP:/tmp/

# Install on droplet
echo "6. Installing on Digital Ocean..."
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SSH_USER@$DROPLET_IP << ENDSSH
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

# Update wp-config.php
cat > /var/www/html/wp-config.php << 'EOFCONFIG'
<?php
define('DB_NAME', 'wordpress');
define('DB_USER', 'wordpress');
define('DB_PASSWORD', '$WP_DB_PASS');
define('DB_HOST', 'localhost');
define('DB_CHARSET', 'utf8mb4');
define('DB_COLLATE', '');

define('WP_HOME', 'http://$DROPLET_IP');
define('WP_SITEURL', 'http://$DROPLET_IP');

\$table_prefix = 'wp_';

define('WP_DEBUG', false);
define('FS_METHOD', 'direct');

if (!defined('ABSPATH')) {
    define('ABSPATH', dirname(__FILE__) . '/');
}

require_once(ABSPATH . 'wp-settings.php');
EOFCONFIG

# Replace variables in wp-config
sed -i "s|\$WP_DB_PASS|$WP_DB_PASS|g" /var/www/html/wp-config.php
sed -i "s|\$DROPLET_IP|$DROPLET_IP|g" /var/www/html/wp-config.php

# Generate new salts
SALT=\$(curl -s https://api.wordpress.org/secret-key/1.1/salt/)
echo "\$SALT" >> /tmp/salts.txt
sed -i "/\$table_prefix = 'wp_';/r /tmp/salts.txt" /var/www/html/wp-config.php

# Set proper permissions
chown -R www-data:www-data /var/www/html
find /var/www/html -type d -exec chmod 755 {} \;
find /var/www/html -type f -exec chmod 644 {} \;

# Update database URLs
mysql -u root -p$MYSQL_ROOT_PASS wordpress << EOFMYSQL
UPDATE wp_options SET option_value = 'http://$DROPLET_IP' WHERE option_name = 'siteurl';
UPDATE wp_options SET option_value = 'http://$DROPLET_IP' WHERE option_name = 'home';
EOFMYSQL

# Restart Apache
systemctl restart apache2

# Clean up
rm /tmp/wp-content.tar.gz
rm /tmp/wordpress_backup.sql
rm -f /tmp/salts.txt

echo "Migration completed successfully!"
ENDSSH

# Clean up local files
rm wp-content.tar.gz
rm wordpress_backup.sql
rm wordpress_backup.sql.bak

echo "================================================"
echo "✅ Migration Complete!"
echo "================================================"
echo ""
echo "Your WordPress site is now live at: http://$DROPLET_IP"
echo ""
echo "Admin panel: http://$DROPLET_IP/wp-admin"
echo ""
echo "Next steps:"
echo "1. Visit http://$DROPLET_IP/wp-admin to log in"
echo "2. Update permalinks: Settings → Permalinks → Save"
echo "3. Set up SSL: ssh root@$DROPLET_IP then run: certbot --apache"
echo "4. Point your domain to: $DROPLET_IP"
echo ""
echo "Droplet Details saved in: .droplet_info"