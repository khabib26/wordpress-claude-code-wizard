#!/usr/bin/env python3
"""
Create Digital Ocean Droplet with SSH access and WordPress
"""

import requests
import json
import time
import sys
import os
from pathlib import Path

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def get_ssh_key_id():
    """Get the SSH key ID from file or API"""
    if os.path.exists('.ssh_key_id'):
        with open('.ssh_key_id', 'r') as f:
            return int(f.read().strip())
    return None

def create_wordpress_droplet():
    api_token = os.getenv('DO_API_TOKEN')
    if not api_token:
        print("❌ DO_API_TOKEN not found")
        sys.exit(1)
    
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    # Get SSH key ID
    ssh_key_id = get_ssh_key_id()
    if not ssh_key_id:
        print("❌ No SSH key found. Run: ./setup_ssh_and_deploy.sh first")
        sys.exit(1)
    
    # Generate passwords
    import secrets
    import string
    chars = string.ascii_letters + string.digits
    mysql_root_pass = ''.join(secrets.choice(chars) for _ in range(16))
    wp_db_pass = ''.join(secrets.choice(chars) for _ in range(16))
    
    # Droplet configuration
    name = f"wordpress-{int(time.time())}"
    region = os.getenv('DROPLET_REGION', 'nyc3')
    size = os.getenv('DROPLET_SIZE', 's-1vcpu-1gb')
    
    # User data script to install WordPress
    user_data = f"""#!/bin/bash
# Install WordPress on Ubuntu 22.04
export DEBIAN_FRONTEND=noninteractive

# Update system
apt-get update && apt-get upgrade -y

# Install Apache, PHP 8.3, MySQL
apt-get install -y software-properties-common
add-apt-repository -y ppa:ondrej/php
apt-get update

# Install packages
apt-get install -y apache2 mysql-server \\
    php8.3 php8.3-cli php8.3-common php8.3-mysql \\
    php8.3-xml php8.3-xmlrpc php8.3-curl php8.3-gd \\
    php8.3-imagick php8.3-mbstring php8.3-zip \\
    php8.3-intl php8.3-bz2 php8.3-bcmath php8.3-soap \\
    libapache2-mod-php8.3

# Configure MySQL
mysql <<EOF
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '{mysql_root_pass}';
CREATE DATABASE wordpress;
CREATE USER 'wordpress'@'localhost' IDENTIFIED BY '{wp_db_pass}';
GRANT ALL PRIVILEGES ON wordpress.* TO 'wordpress'@'localhost';
FLUSH PRIVILEGES;
EOF

# Download WordPress
cd /tmp
wget https://wordpress.org/wordpress-6.8.1.tar.gz
tar xzvf wordpress-6.8.1.tar.gz
cp -R wordpress/* /var/www/html/
rm -f /var/www/html/index.html

# Configure WordPress
cp /var/www/html/wp-config-sample.php /var/www/html/wp-config.php
sed -i "s/database_name_here/wordpress/" /var/www/html/wp-config.php
sed -i "s/username_here/wordpress/" /var/www/html/wp-config.php
sed -i "s/password_here/{wp_db_pass}/" /var/www/html/wp-config.php

# Set salts
curl -s https://api.wordpress.org/secret-key/1.1/salt/ >> /tmp/salts
sed -i "/AUTH_KEY/d; /SECURE_AUTH_KEY/d; /LOGGED_IN_KEY/d; /NONCE_KEY/d" /var/www/html/wp-config.php
sed -i "/AUTH_SALT/d; /SECURE_AUTH_SALT/d; /LOGGED_IN_SALT/d; /NONCE_SALT/d" /var/www/html/wp-config.php
sed -i "/define( 'DB_COLLATE'/r /tmp/salts" /var/www/html/wp-config.php

# Set permissions
chown -R www-data:www-data /var/www/html
find /var/www/html -type d -exec chmod 755 {{}} \\;
find /var/www/html -type f -exec chmod 644 {{}} \\;

# Enable Apache modules and restart
a2enmod rewrite
systemctl restart apache2

# Create .htaccess
cat > /var/www/html/.htaccess <<'HTACCESS'
# BEGIN WordPress
<IfModule mod_rewrite.c>
RewriteEngine On
RewriteBase /
RewriteRule ^index\\.php$ - [L]
RewriteCond %{{REQUEST_FILENAME}} !-f
RewriteCond %{{REQUEST_FILENAME}} !-d
RewriteRule . /index.php [L]
</IfModule>
# END WordPress
HTACCESS

chown www-data:www-data /var/www/html/.htaccess

# Mark as ready
touch /root/.wordpress_ready
echo "MySQL Root: {mysql_root_pass}" > /root/credentials.txt
echo "WP DB Pass: {wp_db_pass}" >> /root/credentials.txt
"""
    
    # Create droplet
    droplet_data = {
        'name': name,
        'region': region,
        'size': size,
        'image': 'ubuntu-22-04-x64',
        'ssh_keys': [ssh_key_id],  # Use SSH key
        'backups': False,
        'ipv6': True,
        'monitoring': True,
        'tags': ['wordpress', 'automated'],
        'user_data': user_data
    }
    
    print(f"Creating droplet: {name}")
    print(f"Region: {region}, Size: {size}")
    print(f"Using SSH key ID: {ssh_key_id}")
    
    response = requests.post('https://api.digitalocean.com/v2/droplets', 
                            headers=headers, json=droplet_data)
    
    if response.status_code != 202:
        print(f"❌ Failed to create droplet: {response.text}")
        sys.exit(1)
    
    droplet = response.json()['droplet']
    droplet_id = droplet['id']
    
    print(f"✅ Droplet created with ID: {droplet_id}")
    print("Waiting for droplet to become active...")
    
    # Wait for droplet to be active
    for _ in range(60):
        time.sleep(5)
        response = requests.get(f'https://api.digitalocean.com/v2/droplets/{droplet_id}', 
                              headers=headers)
        if response.status_code == 200:
            droplet = response.json()['droplet']
            if droplet['status'] == 'active':
                break
    
    # Get IP address
    ip_address = None
    for network in droplet['networks']['v4']:
        if network['type'] == 'public':
            ip_address = network['ip_address']
            break
    
    # Save droplet info
    droplet_info = {
        'droplet_id': droplet_id,
        'droplet_name': name,
        'ip_address': ip_address,
        'mysql_root_pass': mysql_root_pass,
        'wp_db_pass': wp_db_pass,
        'region': region,
        'size': size,
        'ssh_access': True
    }
    
    with open('.droplet_info', 'w') as f:
        json.dump(droplet_info, f, indent=2)
    
    print("\n================================================")
    print("✅ WordPress Droplet Created with SSH Access!")
    print("================================================")
    print(f"IP Address: {ip_address}")
    print(f"SSH Access: ssh -i ~/.ssh/wordpress_deploy root@{ip_address}")
    print(f"\nMySQL Root Pass: {mysql_root_pass}")
    print(f"WordPress DB Pass: {wp_db_pass}")
    print("\nWordPress will be ready in 2-3 minutes")
    print("\nNext: Run ./migrate_to_droplet.sh to migrate your local WordPress")

if __name__ == '__main__':
    create_wordpress_droplet()