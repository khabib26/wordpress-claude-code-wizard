#!/usr/bin/env python3
"""
Automated Digital Ocean Droplet Creator with WordPress Installation
Creates a Ubuntu droplet and installs WordPress automatically
"""

import requests
import json
import time
import sys
import os
import base64
from typing import Optional, Dict, Any
from pathlib import Path

# Try to load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class DODropletCreator:
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }
        self.base_url = 'https://api.digitalocean.com/v2'
        
    def create_droplet_with_wordpress(self, 
                                    name: str,
                                    region: str = 'nyc3',
                                    size: str = 's-1vcpu-1gb',
                                    mysql_root_pass: str = None,
                                    wp_db_pass: str = None) -> Dict[str, Any]:
        """Create a Ubuntu droplet and install WordPress via cloud-init"""
        
        if not mysql_root_pass:
            import secrets
            import string
            chars = string.ascii_letters + string.digits
            mysql_root_pass = ''.join(secrets.choice(chars) for _ in range(16))
            
        if not wp_db_pass:
            import secrets
            import string
            chars = string.ascii_letters + string.digits
            wp_db_pass = ''.join(secrets.choice(chars) for _ in range(16))
        
        # Cloud-init script to install WordPress
        user_data = f"""#!/bin/bash
# Update system
apt-get update
apt-get upgrade -y

# Install Apache, PHP, MySQL
export DEBIAN_FRONTEND=noninteractive

# Set MySQL root password
debconf-set-selections <<< "mysql-server mysql-server/root_password password {mysql_root_pass}"
debconf-set-selections <<< "mysql-server mysql-server/root_password_again password {mysql_root_pass}"

# Install LAMP stack
apt-get install -y apache2 mysql-server php php-mysql php-xml php-xmlrpc php-curl php-gd php-imagick php-cli php-mbstring php-zip php-intl libapache2-mod-php

# Configure MySQL
mysql -u root -p{mysql_root_pass} <<EOF
CREATE DATABASE wordpress;
CREATE USER 'wordpress'@'localhost' IDENTIFIED BY '{wp_db_pass}';
GRANT ALL PRIVILEGES ON wordpress.* TO 'wordpress'@'localhost';
FLUSH PRIVILEGES;
EOF

# Download and install WordPress
cd /tmp
wget https://wordpress.org/latest.tar.gz
tar xzvf latest.tar.gz
cp -R wordpress/* /var/www/html/
rm /var/www/html/index.html

# Configure WordPress
cp /var/www/html/wp-config-sample.php /var/www/html/wp-config.php
sed -i "s/database_name_here/wordpress/" /var/www/html/wp-config.php
sed -i "s/username_here/wordpress/" /var/www/html/wp-config.php
sed -i "s/password_here/{wp_db_pass}/" /var/www/html/wp-config.php

# Set salts
SALT=$(curl -L https://api.wordpress.org/secret-key/1.1/salt/)
STRING='put your unique phrase here'
printf '%s\\n' "g/$STRING/d" a "$SALT" . w | ed -s /var/www/html/wp-config.php

# Set permissions
chown -R www-data:www-data /var/www/html
find /var/www/html -type d -exec chmod 755 {{}} \\;
find /var/www/html -type f -exec chmod 644 {{}} \\;

# Enable Apache modules
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

# Set up firewall
ufw allow 22
ufw allow 80
ufw allow 443
ufw --force enable

# Create marker file
touch /root/.wordpress_ready

# Store credentials
cat > /root/wordpress_credentials.txt <<CREDS
MySQL Root Password: {mysql_root_pass}
WordPress DB Password: {wp_db_pass}
CREDS
"""
        
        droplet_data = {
            'name': name,
            'region': region,
            'size': size,
            'image': 'ubuntu-22-04-x64',  # Ubuntu 22.04
            'backups': False,
            'ipv6': True,
            'monitoring': True,
            'tags': ['wordpress', 'web'],
            'user_data': user_data
        }
        
        url = f"{self.base_url}/droplets"
        response = requests.post(url, headers=self.headers, json=droplet_data)
        
        if response.status_code == 202:
            droplet = response.json()['droplet']
            return {
                'droplet': droplet,
                'mysql_root_pass': mysql_root_pass,
                'wp_db_pass': wp_db_pass
            }
        else:
            raise Exception(f"Failed to create droplet: {response.text}")
    
    def wait_for_droplet(self, droplet_id: int, timeout: int = 300) -> Dict[str, Any]:
        """Wait for droplet to be active"""
        url = f"{self.base_url}/droplets/{droplet_id}"
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                droplet = response.json()['droplet']
                if droplet['status'] == 'active':
                    return droplet
            time.sleep(5)
            
        raise Exception(f"Droplet did not become active within {timeout} seconds")
    
    def get_droplet_ip(self, droplet_id: int) -> str:
        """Get the public IP of the droplet"""
        url = f"{self.base_url}/droplets/{droplet_id}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            droplet = response.json()['droplet']
            for network in droplet['networks']['v4']:
                if network['type'] == 'public':
                    return network['ip_address']
        return None
    
    def delete_droplet(self, droplet_id: int):
        """Delete a droplet"""
        url = f"{self.base_url}/droplets/{droplet_id}"
        response = requests.delete(url, headers=self.headers)
        return response.status_code == 204


def main():
    print("==============================================")
    print("Automated WordPress Droplet Creator")
    print("==============================================\n")
    
    # Get API token from environment
    api_token = os.getenv('DO_API_TOKEN')
    if not api_token:
        print("❌ DO_API_TOKEN not found")
        sys.exit(1)
    
    # Initialize creator
    creator = DODropletCreator(api_token)
    
    # Auto-generate names and passwords
    name = f"wordpress-{int(time.time())}"
    region = os.getenv('DROPLET_REGION', 'nyc3')
    size = os.getenv('DROPLET_SIZE', 's-1vcpu-1gb')
    
    print(f"Creating droplet: {name}")
    print(f"Region: {region}")
    print(f"Size: {size}")
    
    try:
        # Create droplet with WordPress
        result = creator.create_droplet_with_wordpress(
            name=name,
            region=region,
            size=size
        )
        
        droplet = result['droplet']
        droplet_id = droplet['id']
        mysql_root_pass = result['mysql_root_pass']
        wp_db_pass = result['wp_db_pass']
        
        print(f"Droplet created with ID: {droplet_id}")
        print("Waiting for droplet to become active...")
        
        # Wait for droplet
        active_droplet = creator.wait_for_droplet(droplet_id, timeout=300)
        ip_address = creator.get_droplet_ip(droplet_id)
        
        # Save credentials
        droplet_info = {
            'droplet_id': droplet_id,
            'droplet_name': name,
            'ip_address': ip_address,
            'mysql_root_pass': mysql_root_pass,
            'wp_db_pass': wp_db_pass,
            'region': region,
            'size': size
        }
        
        with open('.droplet_info', 'w') as f:
            json.dump(droplet_info, f, indent=2)
        
        print("\n==============================================")
        print("✅ WordPress Droplet Created Successfully!")
        print("==============================================")
        print(f"IP Address: {ip_address}")
        print(f"MySQL Root Pass: {mysql_root_pass}")
        print(f"WordPress DB Pass: {wp_db_pass}")
        print("\nWordPress will be ready in 3-5 minutes")
        print(f"Access at: http://{ip_address}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()