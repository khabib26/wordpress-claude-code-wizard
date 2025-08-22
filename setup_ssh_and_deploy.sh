#!/bin/bash

# Setup SSH keys and deploy WordPress to Digital Ocean
set -e

echo "================================================"
echo "WordPress Automated Deployment Setup"
echo "================================================"

# Generate SSH key if it doesn't exist
SSH_KEY_PATH="$HOME/.ssh/wordpress_deploy"
if [ ! -f "$SSH_KEY_PATH" ]; then
    echo "Generating SSH key..."
    ssh-keygen -t ed25519 -f "$SSH_KEY_PATH" -N "" -C "wordpress-deploy"
    echo "✅ SSH key generated at $SSH_KEY_PATH"
fi

# Read the public key
PUBLIC_KEY=$(cat "$SSH_KEY_PATH.pub")

# Add SSH key to Digital Ocean via API
echo "Adding SSH key to Digital Ocean..."
python3 << EOF
import requests
import json
import os

# Load API token
api_token = os.getenv('DO_API_TOKEN')
if not api_token:
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('DO_API_TOKEN='):
                api_token = line.split('=')[1].strip()
                break

headers = {
    'Authorization': f'Bearer {api_token}',
    'Content-Type': 'application/json'
}

# Check if key already exists
response = requests.get('https://api.digitalocean.com/v2/account/keys', headers=headers)
ssh_keys = response.json().get('ssh_keys', [])

public_key = """$PUBLIC_KEY"""
key_name = "wordpress-deploy-key"

# Find existing key
key_id = None
for key in ssh_keys:
    if key['name'] == key_name:
        key_id = key['id']
        print(f"SSH key already exists with ID: {key_id}")
        break

# Add key if it doesn't exist
if not key_id:
    data = {
        'name': key_name,
        'public_key': public_key
    }
    response = requests.post('https://api.digitalocean.com/v2/account/keys', headers=headers, json=data)
    if response.status_code == 201:
        key_id = response.json()['ssh_key']['id']
        print(f"✅ SSH key added with ID: {key_id}")
    else:
        print(f"❌ Failed to add SSH key: {response.text}")
        exit(1)

# Save key ID
with open('.ssh_key_id', 'w') as f:
    f.write(str(key_id))
EOF

echo ""
echo "================================================"
echo "SSH Setup Complete!"
echo "================================================"
echo ""
echo "Now you can create droplets with SSH access:"
echo "1. Run: python3 create_droplet_with_ssh.py"
echo "2. The droplet will have your SSH key pre-installed"
echo "3. Migration will work automatically"
echo ""
echo "SSH Key: $SSH_KEY_PATH"