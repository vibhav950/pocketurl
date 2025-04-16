#!/bin/zsh

# Cleanup script for Kubernetes resources

set -e

echo "Starting cleanup of Kubernetes resources..."

# delete the HPA first
kubectl delete hpa pocketurl-hpa --ignore-not-found

# delete the pocketurl deployment and service
kubectl delete deployment pocketurl --ignore-not-found
kubectl delete service pocketurl-service --ignore-not-found

# delete Redis deployment and service
kubectl delete deployment redis --ignore-not-found
kubectl delete service redis-service --ignore-not-found

# delete MySQL deployment and service
kubectl delete deployment mysql --ignore-not-found
kubectl delete service mysql-service --ignore-not-found

# delete configmap
kubectl delete configmap pocketurl-config --ignore-not-found

# delete secrets
# kubectl delete secret mysql-secrets --ignore-not-found

# don't delete the PVC
# kubectl delete pvc mysql-pvc --ignore-not-found

# don't delete the PV
# kubectl delete pv mysql-pv --ignore-not-found

echo "Cleaned up pocketurl k8s resources"