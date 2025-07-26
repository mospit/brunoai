#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${GCP_PROJECT_ID:-"your-gcp-project-id"}
REGION=${GCP_REGION:-"us-central1"}

echo -e "${GREEN}Setting up GCP Secret Manager secrets for Bruno AI...${NC}"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"

# Ensure we're authenticated and have the right project
echo -e "${YELLOW}Checking GCP authentication...${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${YELLOW}Enabling required GCP APIs...${NC}"
gcloud services enable secretmanager.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable apigateway.googleapis.com
gcloud services enable servicecontrol.googleapis.com
gcloud services enable servicemanagement.googleapis.com

# Function to create secret if it doesn't exist
create_secret() {
    local secret_name=$1
    local description=$2
    
    echo -e "${YELLOW}Creating secret: $secret_name${NC}"
    
    if gcloud secrets describe $secret_name >/dev/null 2>&1; then
        echo -e "${GREEN}Secret $secret_name already exists${NC}"
    else
        gcloud secrets create $secret_name \
            --replication-policy="automatic" \
            --labels="app=bruno-ai,environment=production" \
            || echo -e "${RED}Failed to create secret $secret_name${NC}"
        echo -e "${GREEN}Created secret $secret_name${NC}"
    fi
}

# Function to add secret version (interactive prompt for value)
add_secret_version() {
    local secret_name=$1
    local prompt_text=$2
    
    echo -e "${YELLOW}$prompt_text${NC}"
    echo "Enter value for $secret_name (leave empty to skip):"
    read -s secret_value
    
    if [ ! -z "$secret_value" ]; then
        echo "$secret_value" | gcloud secrets versions add $secret_name --data-file=-
        echo -e "${GREEN}Added version to $secret_name${NC}"
    else
        echo -e "${YELLOW}Skipped $secret_name${NC}"
    fi
}

# Create all required secrets
echo -e "${GREEN}Creating GCP secrets...${NC}"

# Database secrets
create_secret "bruno-ai-db-url" "PostgreSQL database connection URL"
create_secret "bruno-ai-redis-url" "Redis connection URL"

# JWT and app secrets
create_secret "bruno-ai-jwt-secret" "JWT signing secret"
create_secret "bruno-ai-app-secret" "Application secret key"

# GCP service account credentials
create_secret "bruno-ai-gcp-credentials" "GCP service account JSON credentials"

# Third-party API keys
create_secret "bruno-ai-instacart-key" "Instacart API key"
create_secret "bruno-ai-mem0-key" "Mem0 API key"
create_secret "bruno-ai-voxtral-key" "Voxtral STT API key"
create_secret "bruno-ai-tts-key" "Text-to-Speech API key"

# AI/ML API keys
create_secret "bruno-ai-openai-key" "OpenAI API key"
create_secret "bruno-ai-anthropic-key" "Anthropic API key"

echo -e "${GREEN}All secrets created successfully!${NC}"

# Prompt for secret values (optional)
echo -e "${YELLOW}Would you like to add secret values now? (y/n)${NC}"
read -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}Adding secret values...${NC}"
    
    add_secret_version "bruno-ai-db-url" "Database URL (postgresql://user:pass@host:port/db)"
    add_secret_version "bruno-ai-jwt-secret" "JWT secret (generate a secure random string)"
    add_secret_version "bruno-ai-app-secret" "App secret key (generate a secure random string)"
    add_secret_version "bruno-ai-openai-key" "OpenAI API key"
    
    echo -e "${YELLOW}You can add more secret values later using:${NC}"
    echo "gcloud secrets versions add SECRET_NAME --data-file=-"
fi

# Create service account for Cloud Run
echo -e "${GREEN}Creating service account for Cloud Run...${NC}"
SERVICE_ACCOUNT="bruno-ai-backend-sa"

if gcloud iam service-accounts describe "${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" >/dev/null 2>&1; then
    echo -e "${GREEN}Service account $SERVICE_ACCOUNT already exists${NC}"
else
    gcloud iam service-accounts create $SERVICE_ACCOUNT \
        --display-name="Bruno AI Backend Service Account" \
        --description="Service account for Bruno AI Cloud Run backend"
    echo -e "${GREEN}Created service account $SERVICE_ACCOUNT${NC}"
fi

# Grant necessary permissions
echo -e "${GREEN}Granting permissions to service account...${NC}"

# Secret Manager permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Cloud SQL permissions (if using Cloud SQL)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"

# Storage permissions (for OpenAPI spec and logs)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

echo -e "${GREEN}Setup complete!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Add secret values using: gcloud secrets versions add SECRET_NAME --data-file=-"
echo "2. Build and deploy your Cloud Run service"
echo "3. Configure API Gateway with the generated OpenAPI spec"
echo "4. Set up HTTPS load balancer"
