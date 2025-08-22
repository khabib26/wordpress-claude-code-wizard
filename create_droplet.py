#!/usr/bin/env python3
"""
Digital Ocean WordPress Droplet Creator
Creates a WordPress droplet and prepares it for migration
"""

import requests
import json
import time
import sys
import os
from typing import Optional, Dict, Any
from pathlib import Path

# Try to load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Note: python-dotenv not installed. Using environment variables only.")
    pass

class DODropletCreator:
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }
        self.base_url = 'https://api.digitalocean.com/v2'
        
    def get_wordpress_image(self) -> Optional[str]:
        """Get the latest WordPress marketplace image"""
        url = f"{self.base_url}/images"
        params = {'type': 'application', 'per_page': 200}
        
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            images = response.json()['images']
            # Look for WordPress image
            for image in images:
                if 'wordpress' in image['slug'].lower():
                    return image['slug']
        return None
    
    def create_wordpress_droplet(self, 
                                name: str,
                                region: str = 'nyc3',
                                size: str = 's-1vcpu-1gb',
                                ssh_keys: list = None,
                                user_data: str = None) -> Dict[str, Any]:
        """Create a WordPress droplet"""
        
        # Get WordPress image
        wp_image = self.get_wordpress_image()
        if not wp_image:
            # Fallback to known WordPress image slug
            wp_image = 'wordpress-20-04'
            
        droplet_data = {
            'name': name,
            'region': region,
            'size': size,
            'image': wp_image,
            'backups': False,
            'ipv6': True,
            'monitoring': True,
            'tags': ['wordpress', 'web']
        }
        
        if ssh_keys:
            droplet_data['ssh_keys'] = ssh_keys
            
        if user_data:
            droplet_data['user_data'] = user_data
            
        url = f"{self.base_url}/droplets"
        response = requests.post(url, headers=self.headers, json=droplet_data)
        
        if response.status_code == 202:
            return response.json()['droplet']
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
    
    def list_ssh_keys(self) -> list:
        """List available SSH keys"""
        url = f"{self.base_url}/account/keys"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()['ssh_keys']
        return []


def create_user_data_script(mysql_root_pass: str, wp_db_pass: str) -> str:
    """Create cloud-init script to configure WordPress"""
    return f"""#!/bin/bash
# Wait for WordPress to be installed
sleep 30

# Set MySQL passwords
mysql -u root <<EOF
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '{mysql_root_pass}';
CREATE DATABASE IF NOT EXISTS wordpress;
CREATE USER IF NOT EXISTS 'wordpress'@'localhost' IDENTIFIED BY '{wp_db_pass}';
GRANT ALL PRIVILEGES ON wordpress.* TO 'wordpress'@'localhost';
FLUSH PRIVILEGES;
EOF

# Update wp-config.php with database credentials
if [ -f /var/www/html/wp-config.php ]; then
    sed -i "s/define( 'DB_PASSWORD', '.*' );/define( 'DB_PASSWORD', '{wp_db_pass}' );/" /var/www/html/wp-config.php
fi

# Set proper permissions
chown -R www-data:www-data /var/www/html
find /var/www/html -type d -exec chmod 755 {{}} \\;
find /var/www/html -type f -exec chmod 644 {{}} \\;

# Enable .htaccess
a2enmod rewrite
systemctl restart apache2

# Create marker file
touch /root/.wordpress_configured
"""


def main():
    print("==============================================")
    print("Digital Ocean WordPress Droplet Creator")
    print("==============================================\n")
    
    # Get API token from environment
    api_token = os.getenv('DO_API_TOKEN')
    if not api_token:
        print("❌ DO_API_TOKEN not found in environment variables or .env file")
        print("\nPlease either:")
        print("1. Copy .env.example to .env and add your API token")
        print("2. Set DO_API_TOKEN environment variable")
        print("3. Enter it now manually\n")
        api_token = input("Enter your Digital Ocean API token: ").strip()
        if not api_token:
            print("API token is required!")
            sys.exit(1)
    
    # Initialize creator
    creator = DODropletCreator(api_token)
    
    # Get droplet details
    name = input("Enter droplet name (e.g., my-wordpress-site): ").strip()
    if not name:
        name = f"wordpress-{int(time.time())}"
    
    # Get region from env or ask
    default_region = os.getenv('DROPLET_REGION', 'nyc3')
    print("\nAvailable regions:")
    print("1. nyc1 - New York 1")
    print("2. nyc3 - New York 3") 
    print("3. sfo3 - San Francisco 3")
    print("4. ams3 - Amsterdam 3")
    print("5. lon1 - London 1")
    print("6. fra1 - Frankfurt 1")
    print("7. sgp1 - Singapore 1")
    print("8. tor1 - Toronto 1")
    
    regions = {
        "1": "nyc1", "2": "nyc3", "3": "sfo3", "4": "ams3",
        "5": "lon1", "6": "fra1", "7": "sgp1", "8": "tor1"
    }
    
    # Find default choice
    default_choice = "2"
    for k, v in regions.items():
        if v == default_region:
            default_choice = k
            break
    
    region_choice = input(f"\nSelect region (1-8, default={default_choice} for {default_region}): ").strip() or default_choice
    region = regions.get(region_choice, default_region)
    
    # Get size from env or ask
    default_size = os.getenv('DROPLET_SIZE', 's-1vcpu-1gb')
    print("\nAvailable sizes:")
    print("1. s-1vcpu-1gb - $6/month (1GB RAM, 1 CPU)")
    print("2. s-1vcpu-2gb - $12/month (2GB RAM, 1 CPU)")
    print("3. s-2vcpu-2gb - $18/month (2GB RAM, 2 CPUs)")
    print("4. s-2vcpu-4gb - $24/month (4GB RAM, 2 CPUs)")
    
    sizes = {
        "1": "s-1vcpu-1gb",
        "2": "s-1vcpu-2gb", 
        "3": "s-2vcpu-2gb",
        "4": "s-2vcpu-4gb"
    }
    
    # Find default choice for size
    default_size_choice = "1"
    for k, v in sizes.items():
        if v == default_size:
            default_size_choice = k
            break
    
    size_choice = input(f"\nSelect size (1-4, default={default_size_choice}): ").strip() or default_size_choice
    size = sizes.get(size_choice, default_size)
    
    # Database passwords from env or generate
    mysql_root_pass = os.getenv('MYSQL_ROOT_PASSWORD')
    if not mysql_root_pass:
        mysql_root_pass = input("\nEnter MySQL root password (or press Enter to generate): ").strip()
        if not mysql_root_pass:
            import secrets
            import string
            chars = string.ascii_letters + string.digits
            mysql_root_pass = ''.join(secrets.choice(chars) for _ in range(16))
    else:
        print(f"\nUsing MySQL root password from .env file")
        
    wp_db_pass = os.getenv('WP_DB_PASSWORD')
    if not wp_db_pass:
        wp_db_pass = input("Enter WordPress DB password (or press Enter to generate): ").strip()
        if not wp_db_pass:
            import secrets
            import string
            chars = string.ascii_letters + string.digits
            wp_db_pass = ''.join(secrets.choice(chars) for _ in range(16))
    else:
        print(f"Using WordPress DB password from .env file")
    
    # Check for SSH keys
    print("\nChecking for SSH keys...")
    ssh_keys = creator.list_ssh_keys()
    ssh_key_ids = []
    
    if ssh_keys:
        print("Available SSH keys:")
        for i, key in enumerate(ssh_keys, 1):
            print(f"{i}. {key['name']} ({key['fingerprint'][:20]}...)")
        
        key_choice = input("\nSelect SSH key (number, or press Enter to use password): ").strip()
        if key_choice and key_choice.isdigit():
            idx = int(key_choice) - 1
            if 0 <= idx < len(ssh_keys):
                ssh_key_ids = [ssh_keys[idx]['id']]
    
    # Create user data script
    user_data = create_user_data_script(mysql_root_pass, wp_db_pass)
    
    # Create droplet
    print(f"\nCreating WordPress droplet '{name}' in {region}...")
    try:
        droplet = creator.create_wordpress_droplet(
            name=name,
            region=region,
            size=size,
            ssh_keys=ssh_key_ids,
            user_data=user_data
        )
        
        droplet_id = droplet['id']
        print(f"Droplet created with ID: {droplet_id}")
        
        # Wait for droplet to be active
        print("Waiting for droplet to become active (this may take 2-3 minutes)...")
        active_droplet = creator.wait_for_droplet(droplet_id)
        
        # Get IP address
        ip_address = creator.get_droplet_ip(droplet_id)
        
        print("\n==============================================")
        print("✅ WordPress Droplet Created Successfully!")
        print("==============================================")
        print(f"Droplet Name: {name}")
        print(f"IP Address: {ip_address}")
        print(f"Region: {region}")
        print(f"Size: {size}")
        print(f"\nMySQL Root Password: {mysql_root_pass}")
        print(f"WordPress DB Password: {wp_db_pass}")
        
        # Save credentials to file
        with open('.droplet_info', 'w') as f:
            json.dump({
                'droplet_id': droplet_id,
                'droplet_name': name,
                'ip_address': ip_address,
                'mysql_root_pass': mysql_root_pass,
                'wp_db_pass': wp_db_pass,
                'region': region,
                'size': size
            }, f, indent=2)
        
        print("\nCredentials saved to .droplet_info")
        print("\nNext steps:")
        print(f"1. Wait 2-3 minutes for WordPress to fully initialize")
        print(f"2. Run: ./migrate_to_droplet.sh")
        print(f"3. Access your site at: http://{ip_address}")
        
    except Exception as e:
        print(f"\n❌ Error creating droplet: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()