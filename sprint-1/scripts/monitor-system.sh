#!/bin/bash
# Sprint 1 - Lightweight System Monitoring Script
# Self-contained monitoring for Day 3 validation

set -e

echo "📊 Sprint 1 System Monitoring Dashboard"
echo "========================================"
echo "Timestamp: $(date)"
echo ""

# Function to parse HAProxy CSV stats
parse_haproxy_stats() {
    # Get CSV stats from HAProxy
    local stats=$(curl -s "http://localhost:8404/stats?stats;csv")
    
    echo "🔧 HAProxy Backend Status:"
    echo "---------------------------"
    
    # Parse backend server lines (skip frontend and other lines)
    echo "$stats" | grep "servers," | while IFS=',' read -r pxname svname qcur qmax scur smax slim stot bin bout dreq dresp ereq econ eresp wretr wredis status weight act bck chkfail chkdown lastchg downtime qlimit rest; do
        case "$svname" in
            "k3s-cluster")
                echo "K3s Cluster:"
                echo "  Status: $status"
                echo "  Weight: $weight"
                echo "  Total Requests: $stot"
                echo "  Bytes In: $(numfmt --to=iec $bin 2>/dev/null || echo $bin)"
                echo "  Last Session: ${lastsess}s ago" 2>/dev/null || true
                echo ""
                ;;
            "serverless-sim")
                echo "Knative Serverless:"
                echo "  Status: $status"
                echo "  Weight: $weight"
                echo "  Total Requests: $stot"
                echo "  Bytes In: $(numfmt --to=iec $bin 2>/dev/null || echo $bin)"
                echo "  Last Session: ${lastsess}s ago" 2>/dev/null || true
                echo ""
                ;;
        esac
    done
}

# Function to calculate traffic distribution
calculate_distribution() {
    local stats=$(curl -s "http://localhost:8404/stats?stats;csv")
    
    local k3s_requests=$(echo "$stats" | grep "servers,k3s-cluster" | cut -d',' -f8)
    local serverless_requests=$(echo "$stats" | grep "servers,serverless-sim" | cut -d',' -f8)
    
    if [[ -n "$k3s_requests" && -n "$serverless_requests" && "$k3s_requests" != "" && "$serverless_requests" != "" ]]; then
        local total=$((k3s_requests + serverless_requests))
        
        if [[ $total -gt 0 ]]; then
            local k3s_percent=$((k3s_requests * 100 / total))
            local serverless_percent=$((serverless_requests * 100 / total))
            
            echo "🎯 Traffic Distribution:"
            echo "------------------------"
            echo "K3s Cluster: $k3s_requests requests (${k3s_percent}%)"
            echo "Serverless: $serverless_requests requests (${serverless_percent}%)"
            echo "Total: $total requests"
            
            # Validate distribution
            if [[ $k3s_percent -ge 70 && $k3s_percent -le 90 ]]; then
                echo "✅ Distribution: HEALTHY (within 80/20 ±10%)"
            else
                echo "⚠️ Distribution: WARNING (outside expected range)"
            fi
            echo ""
        else
            echo "🎯 Traffic Distribution: No traffic recorded yet"
            echo ""
        fi
    else
        echo "🎯 Traffic Distribution: Unable to parse stats"
        echo ""
    fi
}

# Function to check component health
check_components() {
    echo "🔍 Component Health Check:"
    echo "----------------------------"
    
    # Check each component
    components=(
        "K3s Backend:http://localhost:8080"
        "Knative Serverless:http://localhost:8081"
        "HAProxy Router:http://localhost:8082"
        "HAProxy Stats:http://localhost:8404/stats"
    )
    
    for component in "${components[@]}"; do
        name=$(echo "$component" | cut -d':' -f1)
        url=$(echo "$component" | cut -d':' -f2,3)
        
        echo -n "$name: "
        if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200"; then
            echo "✅ UP"
        else
            echo "❌ DOWN"
        fi
    done
    echo ""
}

# Function to show resource usage
show_resources() {
    echo "📋 Resource Utilization:"
    echo "-------------------------"
    
    # Docker container stats
    echo "Container Resources:"
    docker stats --no-stream --format "  {{.Container}}: {{.CPUPerc}} CPU, {{.MemUsage}}" \
        2>/dev/null | grep -E "(sprint1|haproxy|prometheus)" || echo "  No monitoring containers running"
    
    echo ""
    echo "System Resources:"
    echo "  Load Average: $(uptime | awk -F'load averages:' '{print $2}')"
    echo "  Memory: $(vm_stat | grep 'Pages free' | awk '{print $3}' | sed 's/\.//' | awk '{printf "%.1f GB free", $1 * 4096 / 1024 / 1024 / 1024}') (estimated)"
    echo ""
}

# Function to test traffic flow
test_traffic() {
    echo "🛑 Traffic Flow Test (10 requests):"
    echo "----------------------------------"
    
    local k3s_count=0
    local serverless_count=0
    local error_count=0
    
    for i in {1..10}; do
        response=$(curl -s "http://localhost:8082" 2>/dev/null || echo "ERROR")
        
        if echo "$response" | grep -q "K3s Cluster Backend"; then
            ((k3s_count++))
        elif echo "$response" | grep -q "Knative Serverless"; then
            ((serverless_count++))
        else
            ((error_count++))
        fi
        
        sleep 0.1  # Brief pause between requests
    done
    
    echo "Results:"
    echo "  K3s: $k3s_count/10 ($(($k3s_count * 10))%)"
    echo "  Serverless: $serverless_count/10 ($(($serverless_count * 10))%)"
    echo "  Errors: $error_count/10 ($(($error_count * 10))%)"
    
    if [[ $error_count -eq 0 ]]; then
        echo "✅ Traffic Flow: HEALTHY"
    else
        echo "⚠️ Traffic Flow: ISSUES DETECTED"
    fi
    echo ""
}

# Main monitoring loop
if [[ "$1" == "--watch" ]]; then
    echo "Starting continuous monitoring (Ctrl+C to stop)..."
    echo ""
    
    while true; do
        clear
        echo "📊 Sprint 1 System Monitoring Dashboard"
        echo "========================================"
        echo "Timestamp: $(date)"
        echo ""
        
        check_components
        parse_haproxy_stats
        calculate_distribution
        show_resources
        
        echo "Press Ctrl+C to stop monitoring..."
        sleep 30
    done
else
    # Single snapshot
    check_components
    parse_haproxy_stats
    calculate_distribution
    show_resources
    test_traffic
    
    echo "🚀 Run with --watch for continuous monitoring"
fi