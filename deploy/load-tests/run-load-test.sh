#!/bin/bash
# Run k6 load tests
# Usage: ./run-load-test.sh [steady|spike|endurance] [base_url]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

TEST_TYPE=${1:-steady}
BASE_URL=${2:-http://localhost:8082}

# Ensure results directory exists
mkdir -p "$PROJECT_ROOT/results/load-tests"

echo "Running $TEST_TYPE load test against $BASE_URL"
echo "================================================"

# Check if k6 is installed
if ! command -v k6 &> /dev/null; then
    echo "k6 not found. Install with: brew install k6"
    exit 1
fi

# Run the test
cd "$PROJECT_ROOT"
k6 run --out json="results/load-tests/${TEST_TYPE}-metrics.json" \
    -e BASE_URL="$BASE_URL" \
    "deploy/load-tests/${TEST_TYPE}.js"

echo ""
echo "Results saved to results/load-tests/"
