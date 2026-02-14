#!/bin/bash
# ==============================================================================
# nousflash DigitalOcean Droplet Deployment Script
# Simpler alternative to GCP Compute Engine.
# ==============================================================================
#
# PREREQUISITES:
#   1. Install doctl: https://docs.digitalocean.com/reference/doctl/how-to/install/
#   2. Authenticate: doctl auth init
#
# USAGE:
#   chmod +x digitalocean_deploy.sh
#   ./digitalocean_deploy.sh [--local-inference]
#
# Droplet sizes used:
#   API-only:         s-4vcpu-8gb    ($56/mo)
#   Local inference:  m-8vcpu-64gb   ($336/mo, 64GB RAM for Xortron)
# ==============================================================================

set -euo pipefail

DROPLET_NAME="nousflash-bot"
REGION="${DO_REGION:-nyc3}"
SSH_KEY_ID="${DO_SSH_KEY_ID:-}"      # Set via: doctl compute ssh-key list
REPO_URL="https://github.com/morongosteve/nousflash.git"

# Default: API mode
SIZE="s-4vcpu-8gb"
WITH_LOCAL_INFERENCE="false"

for arg in "$@"; do
  case $arg in
    --local-inference)
      SIZE="m-8vcpu-64gb"
      WITH_LOCAL_INFERENCE="true"
      echo ">>> Local inference mode: using $SIZE (64 GB RAM)"
      shift
      ;;
  esac
done

if [ -z "$SSH_KEY_ID" ]; then
  echo "Error: DO_SSH_KEY_ID not set."
  echo "List your keys with: doctl compute ssh-key list"
  echo "Then: export DO_SSH_KEY_ID=your_key_id"
  exit 1
fi

if [ ! -f "../agent/.env" ]; then
  echo "Error: agent/.env not found."
  echo "Copy agent/.env.example to agent/.env and fill in your credentials."
  exit 1
fi

echo "=============================================="
echo "Deploying nousflash to DigitalOcean"
echo "=============================================="
echo "Droplet: $DROPLET_NAME"
echo "Region:  $REGION"
echo "Size:    $SIZE"
echo "Mode:    $([ "$WITH_LOCAL_INFERENCE" = "true" ] && echo "Local inference" || echo "API inference")"
echo ""

echo ">>> Creating droplet..."
DROPLET_ID=$(doctl compute droplet create "$DROPLET_NAME" \
  --size "$SIZE" \
  --image debian-12-x64 \
  --region "$REGION" \
  --ssh-keys "$SSH_KEY_ID" \
  --no-header \
  --format ID \
  --wait)

echo ">>> Droplet $DROPLET_ID created. Fetching IP..."
sleep 10
DROPLET_IP=$(doctl compute droplet get "$DROPLET_ID" --no-header --format PublicIPv4)
echo ">>> IP: $DROPLET_IP"

echo ">>> Uploading .env..."
scp -o StrictHostKeyChecking=no ../agent/.env "root@$DROPLET_IP:/tmp/.env"

echo ">>> Bootstrapping..."
ssh -o StrictHostKeyChecking=no "root@$DROPLET_IP" bash -s << REMOTE
set -euo pipefail
apt-get update -qq
apt-get install -y -qq curl git

# Docker
curl -fsSL https://get.docker.com | sh
systemctl enable --now docker

# Clone repo
git clone --branch main $REPO_URL /opt/nousflash
cp /tmp/.env /opt/nousflash/agent/.env

if [ "$WITH_LOCAL_INFERENCE" = "true" ]; then
  echo "Downloading Xortron2025 model (~19.3 GB)..."
  mkdir -p /opt/nousflash/agent/local_inference/models
  curl -L -C - -o /opt/nousflash/agent/local_inference/models/Xortron2025-24B.Q6_K.gguf \
    https://huggingface.co/darkc0de/Xortron2025/resolve/main/Xortron2025-24B.Q6_K.gguf
fi

cd /opt/nousflash/agent
docker build --build-arg WITH_LOCAL_INFERENCE=$WITH_LOCAL_INFERENCE -t nousflash:latest .

docker run -d \
  --name nousflash \
  --restart always \
  --env-file .env \
  -v "\$(pwd)/data:/data" \
  nousflash:latest

docker logs --tail 20 nousflash
REMOTE

echo ""
echo "=============================================="
echo "Deployment complete!"
echo "  Droplet IP: $DROPLET_IP"
echo "  Logs: ssh root@$DROPLET_IP 'docker logs -f nousflash'"
echo "  Delete: doctl compute droplet delete $DROPLET_ID"
echo "=============================================="
