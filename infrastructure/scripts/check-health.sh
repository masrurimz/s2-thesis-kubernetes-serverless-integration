#!/bin/bash
# Sprint 1 - System Health Check Script
# LLM Implementation: Day 3 Monitoring

set -e

echo "🔍 Sprint 1 Hybrid System Health Check"
echo "======================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Health check functions
check_component() {
    local name="$1"
    local url="$2"
    local expected_code="${3:-200}"

    echo -n "Checking $name... "

    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "$expected_code"; then
        echo -e "${GREEN}✅ UP${NC}"
        return 0
    else
        echo -e "${RED}❌ DOWN${NC}"
        return 1
    fi
}

NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null || true)
if [[ -z "$NODE_IP" ]]; then
    NODE_IP="127.0.0.1"
fi

K3S_WARM_URL="http://${NODE_IP}:30080/health"
SERVERLESS_ACTIVATOR_URL="http://${NODE_IP}:30081/health"

check_serverless_component() {
    echo -n "Checking Serverless Activator... "

    if curl -s -o /dev/null -w "%{http_code}" "$SERVERLESS_ACTIVATOR_URL" | grep -q "200"; then
        echo -e "${GREEN}✅ UP${NC}"
        return 0
    else
        echo -e "${RED}❌ DOWN${NC}"
        return 1
    fi
}

check_metrics() {
    local service="$1"
    local query="$2"
    
    echo -n "Checking $service metrics... "
    
    if curl -s "http://localhost:9090/api/v1/query?query=$query" | jq -r '.status' | grep -q "success"; then
        echo -e "${GREEN}✅ OK${NC}"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        return 1
    fi
}

# Start health checks
echo "📋 Component Status:"
echo "-------------------"

# Core components
check_component "K3s Backend" "$K3S_WARM_URL" || K3S_FAIL=1
check_serverless_component || SERVERLESS_FAIL=1
check_component "HAProxy Router" "http://localhost:18082/health" || HAPROXY_FAIL=1
check_component "HAProxy Stats" "http://localhost:18404/stats" || STATS_FAIL=1

echo ""
echo "📊 HAProxy Backend Status:"
echo "--------------------------"

# Get HAProxy stats for backend validation
HAPROXY_STATS=$(curl -s "http://localhost:18404/stats;csv" 2>/dev/null)
if [[ -n "$HAPROXY_STATS" ]]; then
    K3S_STATUS=$(echo "$HAPROXY_STATS" | grep "servers,k3s-cluster" | cut -d',' -f18)
    KNATIVE_STATUS=$(echo "$HAPROXY_STATS" | grep "servers,serverless-sim" | cut -d',' -f18)
    
    echo -n "HAProxy K3s Backend... "
    if [[ "$K3S_STATUS" == "UP" ]]; then
        echo -e "${GREEN}✅ UP${NC}"
    else
        echo -e "${RED}❌ DOWN${NC}"
        HAPROXY_K3S_FAIL=1
    fi
    
    echo -n "HAProxy Knative Backend... "
    if [[ "$KNATIVE_STATUS" == "UP" ]]; then
        echo -e "${GREEN}✅ UP${NC}"
    else
        echo -e "${RED}❌ DOWN${NC}"
        HAPROXY_KNATIVE_FAIL=1
    fi
else
    echo -e "${RED}❌ Cannot retrieve HAProxy stats${NC}"
    HAPROXY_METRICS_FAIL=1
fi

echo ""
echo "🎯 Traffic Distribution:"
echo "-----------------------"

# Get traffic distribution from HAProxy stats
if [[ -n "$HAPROXY_STATS" ]]; then
    K3S_REQUESTS=$(echo "$HAPROXY_STATS" | grep "servers,k3s-cluster" | cut -d',' -f8)
    KNATIVE_REQUESTS=$(echo "$HAPROXY_STATS" | grep "servers,serverless-sim" | cut -d',' -f8)
    
    if [[ -n "$K3S_REQUESTS" ]] && [[ -n "$KNATIVE_REQUESTS" ]] && [[ "$K3S_REQUESTS" -gt 0 || "$KNATIVE_REQUESTS" -gt 0 ]]; then
        TOTAL_REQUESTS=$((K3S_REQUESTS + KNATIVE_REQUESTS))
        K3S_PERCENT=$((K3S_REQUESTS * 100 / TOTAL_REQUESTS))
        KNATIVE_PERCENT=$((KNATIVE_REQUESTS * 100 / TOTAL_REQUESTS))
        
        echo "K3s Cluster: ${K3S_REQUESTS} requests (${K3S_PERCENT}%)"
        echo "Serverless: ${KNATIVE_REQUESTS} requests (${KNATIVE_PERCENT}%)"
        
        # Check if within expected ranges (70-90% for K3s, 10-30% for serverless)
        if [[ $K3S_PERCENT -ge 70 && $K3S_PERCENT -le 90 ]]; then
            echo -e "Traffic Distribution: ${GREEN}✅ HEALTHY (within 80/20 ±10%)${NC}"
        else
            echo -e "Traffic Distribution: ${YELLOW}⚠️ WARNING (outside expected range)${NC}"
            TRAFFIC_DISTRIBUTION_WARN=1
        fi
    else
        echo "K3s Cluster: 0 requests"
        echo "Serverless: 0 requests"
        echo -e "Traffic Distribution: ${YELLOW}⚠️ NO TRAFFIC DATA${NC}"
        TRAFFIC_DISTRIBUTION_WARN=1
    fi
else
    echo -e "Traffic Distribution: ${RED}❌ NO DATA${NC}"
    TRAFFIC_DISTRIBUTION_FAIL=1
fi

echo ""
echo "🔧 Resource Utilization:"
echo "------------------------"

# Container resource usage
echo "Docker Containers:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null | grep -E "(sprint1|haproxy)" || echo "Sprint 1 containers not found"

echo ""
echo "📈 Current Performance:"
echo "----------------------"

# Test response time with a quick request
echo -n "Testing hybrid endpoint response time... "
RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" "http://localhost:18082/health" 2>/dev/null)
if [[ -n "$RESPONSE_TIME" ]]; then
    RESPONSE_MS=$(echo "$RESPONSE_TIME * 1000" | bc -l | cut -d'.' -f1)
    echo "${RESPONSE_MS}ms"
    
    if [[ $RESPONSE_MS -lt 200 ]]; then
        echo -e "Performance: ${GREEN}✅ EXCELLENT (<200ms)${NC}"
    elif [[ $RESPONSE_MS -lt 500 ]]; then
        echo -e "Performance: ${YELLOW}⚠️ ACCEPTABLE (200-500ms)${NC}"
        PERFORMANCE_WARN=1
    else
        echo -e "Performance: ${RED}❌ SLOW (>500ms)${NC}"
        PERFORMANCE_FAIL=1
    fi
else
    echo "Failed to test"
    echo -e "Performance: ${RED}❌ TEST FAILED${NC}"
    PERFORMANCE_FAIL=1
fi

echo ""
echo "📋 Overall System Status:"
echo "========================"

# Calculate overall health
FAILURES=0
WARNINGS=0

[[ -n "$K3S_FAIL" ]] && ((FAILURES++))
[[ -n "$SERVERLESS_FAIL" ]] && ((FAILURES++))
[[ -n "$HAPROXY_FAIL" ]] && ((FAILURES++))
[[ -n "$STATS_FAIL" ]] && ((FAILURES++))
[[ -n "$HAPROXY_METRICS_FAIL" ]] && ((FAILURES++))
[[ -n "$HAPROXY_K3S_FAIL" ]] && ((FAILURES++))
[[ -n "$HAPROXY_KNATIVE_FAIL" ]] && ((FAILURES++))
[[ -n "$TRAFFIC_DISTRIBUTION_FAIL" ]] && ((FAILURES++))
[[ -n "$PERFORMANCE_FAIL" ]] && ((FAILURES++))

[[ -n "$TRAFFIC_DISTRIBUTION_WARN" ]] && ((WARNINGS++))
[[ -n "$PERFORMANCE_WARN" ]] && ((WARNINGS++))

if [[ $FAILURES -eq 0 && $WARNINGS -eq 0 ]]; then
    echo -e "Status: ${GREEN}✅ ALL SYSTEMS HEALTHY${NC}"
    exit 0
elif [[ $FAILURES -eq 0 ]]; then
    echo -e "Status: ${YELLOW}⚠️ HEALTHY WITH WARNINGS ($WARNINGS warnings)${NC}"
    exit 1
else
    echo -e "Status: ${RED}❌ SYSTEM ISSUES DETECTED ($FAILURES failures, $WARNINGS warnings)${NC}"
    exit 2
fi
