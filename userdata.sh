#!/bin/bash

# Install required packages
yum update -y
yum install -y docker aws-cli jq python3-pip

# Install specific Python packages with correct versions
pip3 install --upgrade pip
pip3 install urllib3==2.1.0 requests==2.31.0 certifi==2024.2.2

# Start Docker service
systemctl start docker
systemctl enable docker

# Create application directory
mkdir -p /opt/cocolancer
chmod 755 /opt/cocolancer

# Create update script
cat > /opt/cocolancer/update-container.sh << 'EOF'
#!/bin/bash

# Login to ECR
aws ecr get-login-password --region your-region | docker login --username AWS --password-stdin your-account-id.dkr.ecr.your-region.amazonaws.com

# Pull the latest image
docker pull your-account-id.dkr.ecr.your-region.amazonaws.com/your-repo-name:latest

# Stop and remove the current container
docker stop cocolancer || true
docker rm cocolancer || true

# Start a new container with the latest image and proper environment variables
docker run -d \
  --name cocolancer \
  --restart unless-stopped \
  -p 80:80 \
  -v /opt/cocolancer/config:/app/config \
  -v /opt/cocolancer/.env:/app/.env \
  -e PYTHONWARNINGS="ignore::urllib3.exceptions.NotOpenSSLWarning" \
  your-account-id.dkr.ecr.your-region.amazonaws.com/your-repo-name:latest
EOF

# Make update script executable
chmod +x /opt/cocolancer/update-container.sh

# Initial container setup
/opt/cocolancer/update-container.sh 