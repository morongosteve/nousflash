#!/bin/bash
# ==============================================================================
# nousflash GCP Compute Engine Deployment Script
# ==============================================================================
#
# IMPORTANT: "Google AI Studio" (aistudio.google.com) is for testing Gemini
# models — not for deploying custom apps. This script targets Google Compute
# Engine (GCE), which is the correct GCP service for a continuously-running
# Python process with high RAM requirements.
#
# PREREQUISITES:
#   1. Install Google Cloud CLI: https://cloud.google.com/sdk/docs/install
#   2. Authenticate: gcloud auth login
#   3. Set project: gcloud config set project YOUR_PROJECT_ID
#   4. Enable Compute Engine API: gcloud services enable compute.googleapis.com
#
# USAGE:
#   chmod +x gcp_deploy.sh
#   ./gcp_deploy.sh [--local-inference]
#
#   Flags:
#     --local-inference   Provision 52GB RAM VM and build llama.cpp for Xortron
#                         (default: 13GB RAM VM, API-based inference)
# ==============================================================================

set -euo pipefail

# --- Configuration ---
PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${GCP_REGION:-us-central1}"
ZONE="${GCP_ZONE:-us-central1-a}"
INSTANCE_NAME="nousflash-bot"
REPO_URL="https://github.com/morongosteve/nousflash.git"
REPO_BRANCH="main"

# Default: API inference (13 GB RAM, 4 vCPU)
MACHINE_TYPE="n2-standard-4"
DISK_SIZE="50GB"
WITH_LOCAL_INFERENCE="false"

# --- Parse flags ---
for arg in "$@"; do
  case $arg in
    --local-inference)
      # Local inference needs 21GB+ RAM + 20GB model storage
      # n2-highmem-8 = 64GB RAM, 8 vCPU
      MACHINE_TYPE="n2-highmem-8"
      DISK_SIZE="80GB"
      WITH_LOCAL_INFERENCE="true"
      echo ">>> Local inference mode: using $MACHINE_TYPE (64 GB RAM)"
      shift
      ;;
  esac
done

# --- Validate ---
if [ -z "$PROJECT_ID" ]; then
  echo "Error: GCP project not set."
  echo "Run: gcloud config set project YOUR_PROJECT_ID"
  exit 1
fi

if [ ! -f "../agent/.env" ]; then
  echo "Error: agent/.env not found."
  echo "Copy agent/.env.example to agent/.env and fill in your credentials."
  exit 1
fi

echo "=============================================="
echo "Deploying nousflash to GCP Compute Engine"
echo "=============================================="
echo "Project:  $PROJECT_ID"
echo "Zone:     $ZONE"
echo "Instance: $INSTANCE_NAME"
echo "Machine:  $MACHINE_TYPE"
echo "Disk:     $DISK_SIZE"
echo "Mode:     $([ "$WITH_LOCAL_INFERENCE" = "true" ] && echo "Local inference (Xortron2025)" || echo "API inference")"
echo ""

# --- Create VM ---
echo ">>> Creating Compute Engine VM..."
gcloud compute instances create "$INSTANCE_NAME" \
  --project="$PROJECT_ID" \
  --zone="$ZONE" \
  --machine-type="$MACHINE_TYPE" \
  --boot-disk-size="$DISK_SIZE" \
  --boot-disk-type="pd-balanced" \
  --image-family="debian-12" \
  --image-project="debian-cloud" \
  --tags="nousflash" \
  --metadata="enable-oslogin=true" \
  --scopes="default"

echo ">>> VM created. Waiting for SSH to become available..."
sleep 30

# --- Upload .env ---
echo ">>> Uploading .env to VM..."
gcloud compute scp ../agent/.env "$INSTANCE_NAME":/tmp/.env \
  --zone="$ZONE" \
  --project="$PROJECT_ID"

# --- Bootstrap VM ---
echo ">>> Running bootstrap script on VM..."
gcloud compute ssh "$INSTANCE_NAME" \
  --zone="$ZONE" \
  --project="$PROJECT_ID" \
  --command="bash -s" << REMOTE_SCRIPT
set -euo pipefail

echo "--- Installing Docker ---"
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker \$USER
sudo systemctl enable docker
sudo systemctl start docker

echo "--- Cloning repository ---"
git clone --branch $REPO_BRANCH $REPO_URL /opt/nousflash
cd /opt/nousflash

echo "--- Moving .env into place ---"
sudo cp /tmp/.env agent/.env
sudo rm -f /tmp/.env

echo "--- Downloading Xortron2025 model (if local inference mode) ---"
if [ "$WITH_LOCAL_INFERENCE" = "true" ]; then
  echo "Downloading Xortron2025-24B model (~19.3 GB)..."
  mkdir -p agent/local_inference/models
  curl -L -C - -o agent/local_inference/models/Xortron2025-24B.Q6_K.gguf \
    https://huggingface.co/darkc0de/Xortron2025/resolve/main/Xortron2025-24B.Q6_K.gguf
  echo "Model downloaded."
fi

echo "--- Building Docker image ---"
cd agent
sudo docker build \
  --build-arg WITH_LOCAL_INFERENCE=$WITH_LOCAL_INFERENCE \
  -t nousflash:latest .

echo "--- Starting container ---"
sudo docker run -d \
  --name nousflash \
  --restart always \
  --env-file .env \
  -v "\$(pwd)/data:/data" \
  $([ "$WITH_LOCAL_INFERENCE" = "true" ] && echo '-v "$(pwd)/local_inference/models:/app/local_inference/models"' || echo '') \
  nousflash:latest

echo "--- Done! ---"
sudo docker logs --tail 20 nousflash
REMOTE_SCRIPT

echo ""
echo "=============================================="
echo "Deployment complete!"
echo "=============================================="
echo ""
echo "Useful commands:"
echo ""
echo "  View logs:"
echo "    gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command='sudo docker logs -f nousflash'"
echo ""
echo "  SSH into VM:"
echo "    gcloud compute ssh $INSTANCE_NAME --zone=$ZONE"
echo ""
echo "  Stop bot:"
echo "    gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command='sudo docker stop nousflash'"
echo ""
echo "  Delete VM (stops billing):"
echo "    gcloud compute instances delete $INSTANCE_NAME --zone=$ZONE --project=$PROJECT_ID"
echo ""
