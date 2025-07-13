#!/bin/bash

# Test script for Knative serverless simulation
# This script simplifies testing the Knative service with correct headers

KNATIVE_HOST="serverless-sim.default.localhost"
KNATIVE_PORT="8081"

echo "Testing Knative Serverless Backend..."
echo "==========================================="

echo "1. Main endpoint:"
curl -H "Host: ${KNATIVE_HOST}" http://localhost:${KNATIVE_PORT}

echo -e "\n2. Health endpoint:"
curl -H "Host: ${KNATIVE_HOST}" http://localhost:${KNATIVE_PORT}/health

echo -e "\n3. Current pods:"
kubectl get pods -l serving.knative.dev/service=serverless-sim

echo -e "\n4. Knative service status:"
kubectl get ksvc serverless-sim

echo -e "\nNote: Use 'curl -H \"Host: ${KNATIVE_HOST}\" http://localhost:${KNATIVE_PORT}' to test manually"