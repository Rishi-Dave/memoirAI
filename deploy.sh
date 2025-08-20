#!/bin/bash
echo "🚀 Deploying to EC2..."

EC2_IP="35.171.88.166"
KEY_PATH="../aws/rishidavekey.pem"

# Upload only the app directory
scp -i $KEY_PATH -r ./app ubuntu@$EC2_IP:~/memoir-ai/

# Restart service on EC2
ssh -i $KEY_PATH ubuntu@$EC2_IP << 'EOF'
  cd ~/memoir-ai
  source venv/bin/activate
  pip install -r requirements.txt
  sudo systemctl restart memoir-server
EOF

echo "✅ Deployment complete!"