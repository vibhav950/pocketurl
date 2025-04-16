#!/bin/zsh

RED='\033[0;31m'
NC='\033[0m'
PURPLE='\033[0;35m'

set -e

# create directory for MySQL persistent volume (if required) minikube host
minikube ssh "sudo mkdir -p /mnt/data/mysql && sudo chmod 777 /mnt/data/mysql"

# ensure the metrics server is enabled for HPA
minikube addons enable metrics-server || echo "Note: metrics-server might already be enabled"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_ROOT"

# check if api directory exists
if [ ! -d "./api" ]; then
    echo -e "${RED}Error:${NC} 'api' directory not found!${NC}"
    exit 1
fi

# build and push the Docker image
echo -e "${PURPLE}Building Docker image...${NC}"
docker build -t pocketurl:latest ./api

# load the image into minikube
echo -e "${PURPLE}Loading image into Minikube...${NC}"
minikube image load pocketurl:latest

echo -e "${PURPLE}Creating ConfigMaps and Secrets...${NC}"
kubectl apply -f kubernetes/manifests/configmap.yaml
kubectl apply -f kubernetes/secrets/secrets.yaml

echo -e "${PURPLE}Creating Persistent Volumes...${NC}"
kubectl apply -f kubernetes/manifests/mysql-pv.yaml

echo -e "${PURPLE}Deploying MySQL...${NC}"
kubectl apply -f kubernetes/manifests/mysql.yaml

echo -e "${PURPLE}Waiting for MySQL to become ready...${NC}"
kubectl wait --for=condition=available deployment/mysql --timeout=3m || {
    echo -e "${RED}MySQL deployment failed to become ready within timeout${NC}"
    echo -e "MySQL pod status:"
    kubectl get pods -l app=mysql
    kubectl describe pods -l app=mysql
    kubectl logs -l app=mysql
    exit 1
}

echo -e "${PURPLE}Deploying Redis...${NC}"
kubectl apply -f kubernetes/manifests/redis.yaml

echo -e "${PURPLE}Waiting for Redis to become ready...${NC}"
kubectl wait --for=condition=available deployment/redis --timeout=2m || {
    echo -e "${RED}Redis deployment failed to become ready within timeout${NC}"
    echo -e "Redis pod status:"
    kubectl get pods -l app=redis
    kubectl describe pods -l app=redis
    kubectl logs -l app=redis
    exit 1
}

echo -e "${PURPLE}Deploying PocketURL service...${NC}"
kubectl apply -f kubernetes/manifests/pocketurl.yaml

echo -e "${PURPLE}Waiting for PocketURL to become ready...${NC}"
kubectl wait --for=condition=available deployment/pocketurl --timeout=2m || {
    echo -e "${RED}PocketURL deployment failed to become ready within timeout${NC}"
    echo -e "${RED}PocketURL pod status:${NC}"
    kubectl get pods -l app=pocketurl
    echo -e "${RED}Pod details:${NC}"
    kubectl describe pods -l app=pocketurl
    echo -e "${RED}Pod logs:${NC}"
    kubectl logs -l app=pocketurl --tail=50
    echo -e "${RED}This might be due to connectivity issues with MySQL or Redis.${NC}"
    echo -e "${RED}The deployment will proceed, but you may need to troubleshoot.${NC}"
}

# deploy HPA after main application is running
echo -e "${PURPLE}Deploying HPA...${NC}"
kubectl apply -f kubernetes/manifests/pocketurl-hpa.yaml

echo -e "${PURPLE}Access PocketURL at:${NC}"
minikube service pocketurl-service --url