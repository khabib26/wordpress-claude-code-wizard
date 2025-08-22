#!/bin/bash

# Direct WordPress Migration Script
set -e

echo "================================================"
echo "Migrating WordPress to Digital Ocean"
echo "================================================"

# Read droplet info
DROPLET_IP=$(python3 -c "import json; print(json.load(open('.droplet_info'))['ip_address'])")
MYSQL_ROOT_PASS=$(python3 -c "import json; print(json.load(open('.droplet_info'))['mysql_root_pass'])")
WP_DB_PASS=$(python3 -c "import json; print(json.load(open('.droplet_info'))['wp_db_pass'])")
SSH_KEY="$HOME/.ssh/wordpress_deploy"

echo "Migrating to: $DROPLET_IP"

# 1. Export local database
echo "1. Exporting local database..."
docker exec wp-mysql mysqldump -u wordpress -pwordpress_password wordpress > wordpress_backup.sql

# 2. Update URLs in database
echo "2. Updating URLs..."
sed -i.bak "s|http://localhost|http://$DROPLET_IP|g" wordpress_backup.sql

# 3. Package wp-content
echo "3. Packaging wp-content..."
tar -czf wp-content.tar.gz wp-content/

# 4. Transfer files
echo "4. Transferring files..."
scp -i $SSH_KEY -o StrictHostKeyChecking=no wp-content.tar.gz root@$DROPLET_IP:/tmp/
scp -i $SSH_KEY -o StrictHostKeyChecking=no wordpress_backup.sql root@$DROPLET_IP:/tmp/

# 5. Install on droplet
echo "5. Installing on droplet..."
ssh -i $SSH_KEY -o StrictHostKeyChecking=no root@$DROPLET_IP << ENDSSH
# Backup existing
cd /var/www/html
if [ -d "wp-content" ]; then
    mv wp-content wp-content.orig
fi

# Extract our wp-content
tar -xzf /tmp/wp-content.tar.gz

# Import database
mysql -u root -p$MYSQL_ROOT_PASS wordpress < /tmp/wordpress_backup.sql

# Update database URLs
mysql -u root -p$MYSQL_ROOT_PASS wordpress << EOSQL
UPDATE wp_options SET option_value = 'http://$DROPLET_IP' WHERE option_name = 'siteurl';
UPDATE wp_options SET option_value = 'http://$DROPLET_IP' WHERE option_name = 'home';
UPDATE wp_posts SET guid = REPLACE(guid, 'http://localhost', 'http://$DROPLET_IP');
UPDATE wp_posts SET post_content = REPLACE(post_content, 'http://localhost', 'http://$DROPLET_IP');
UPDATE wp_postmeta SET meta_value = REPLACE(meta_value, 'http://localhost', 'http://$DROPLET_IP');
EOSQL

# Set permissions
chown -R www-data:www-data /var/www/html
find /var/www/html -type d -exec chmod 755 {} \;
find /var/www/html -type f -exec chmod 644 {} \;

# Set permalinks and flush rewrite rules
cd /var/www/html
wp --allow-root rewrite structure '/%postname%/'
wp --allow-root rewrite flush

# Ensure .htaccess is writable and has correct rules
chmod 664 /var/www/html/.htaccess
cat > /var/www/html/.htaccess <<'HTACCESS'
# BEGIN WordPress
<IfModule mod_rewrite.c>
RewriteEngine On
RewriteBase /
RewriteRule ^index\.php$ - [L]
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule . /index.php [L]
</IfModule>
# END WordPress
HTACCESS
chown www-data:www-data /var/www/html/.htaccess

# Restart Apache
systemctl restart apache2

echo "Migration complete!"
ENDSSH

# Clean up
rm -f wp-content.tar.gz wordpress_backup.sql wordpress_backup.sql.bak

echo "================================================"
echo "✅ Migration Complete!"
echo "================================================"
echo "Your site with custom theme is now at: http://$DROPLET_IP"