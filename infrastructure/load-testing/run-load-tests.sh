#!/bin/bash

# Sprint 1 Load Testing Automation Script
# Day 4 Implementation: Complete load testing framework

set -e

# Load centralized configuration
source "$(dirname "${BASH_SOURCE[0]}")/../load-config.sh"

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="../results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if k6 is installed
    if ! command -v k6 &> /dev/null; then
        log_error "k6 is not installed. Installing via Homebrew..."
        if command -v brew &> /dev/null; then
            brew install k6
        else
            log_error "Please install k6: https://k6.io/docs/getting-started/installation/"
            log_error "Or run: brew install k6"
            exit 1
        fi
    fi
    
    # Check if system is running
    if ! curl -s "${HAPROXY_URL}" > /dev/null; then
        log_error "Hybrid system not running at ${HAPROXY_URL}"
        log_error "Please start the system first: cd ../infrastructure/haproxy && docker-compose up -d"
        exit 1
    fi
    
    # Check if monitoring is available
    if ! curl -s "${HAPROXY_STATS_URL}" > /dev/null; then
        log_warning "HAProxy stats not accessible - some metrics may be limited"
    fi
    
    log_success "Prerequisites check passed"
}

create_results_dir() {
    mkdir -p "$RESULTS_DIR"
    log_info "Results will be saved to: $RESULTS_DIR"
}

run_system_baseline() {
    log_info "Recording system baseline before load testing..."
    
    # System health check
    cd "$SCRIPT_DIR/../scripts"
    echo "=== PRE-TEST SYSTEM STATUS ===" > "$RESULTS_DIR/load-test-baseline-$TIMESTAMP.txt"
    ./check-health.sh >> "$RESULTS_DIR/load-test-baseline-$TIMESTAMP.txt" 2>&1
    
    # Resource usage baseline
    echo -e "\n=== RESOURCE BASELINE ===" >> "$RESULTS_DIR/load-test-baseline-$TIMESTAMP.txt"
    docker stats --no-stream >> "$RESULTS_DIR/load-test-baseline-$TIMESTAMP.txt" 2>&1
    
    # Performance baseline
    echo -e "\n=== PERFORMANCE BASELINE ===" >> "$RESULTS_DIR/load-test-baseline-$TIMESTAMP.txt"
    for i in {1..5}; do
        echo "Request $i:" >> "$RESULTS_DIR/load-test-baseline-$TIMESTAMP.txt"
        time curl -s "${HAPROXY_URL}" > /dev/null 2>> "$RESULTS_DIR/load-test-baseline-$TIMESTAMP.txt"
    done
    
    log_success "Baseline recorded"
}

run_steady_load_test() {
    log_info "Running Steady Load Test (50 RPS for 3 minutes)..."
    
    cd "$SCRIPT_DIR"
    TARGET_URL="${HAPROXY_URL}" k6 run steady-load.js \
        --out json="$RESULTS_DIR/steady-load-results-$TIMESTAMP.json" \
        --summary-export="$RESULTS_DIR/steady-load-summary-$TIMESTAMP.json" \
        2>&1 | tee "$RESULTS_DIR/steady-load-output-$TIMESTAMP.txt"
    
    local exit_code=${PIPESTATUS[0]}
    
    if [ $exit_code -eq 0 ]; then
        log_success "Steady Load Test completed successfully"
    else
        log_error "Steady Load Test failed with exit code $exit_code"
        return $exit_code
    fi
}

run_spike_load_test() {
    log_info "Running Spike Load Test (50→200→50 RPS over 6 minutes)..."
    
    # Wait for system recovery
    log_info "Waiting 30 seconds for system recovery..."
    sleep 30
    
    cd "$SCRIPT_DIR"
    TARGET_URL="${HAPROXY_URL}" k6 run spike-load.js \
        --out json="$RESULTS_DIR/spike-load-results-$TIMESTAMP.json" \
        --summary-export="$RESULTS_DIR/spike-load-summary-$TIMESTAMP.json" \
        2>&1 | tee "$RESULTS_DIR/spike-load-output-$TIMESTAMP.txt"
    
    local exit_code=${PIPESTATUS[0]}
    
    if [ $exit_code -eq 0 ]; then
        log_success "Spike Load Test completed successfully"
    else
        log_error "Spike Load Test failed with exit code $exit_code"
        return $exit_code
    fi
}

run_endurance_test() {
    log_info "Running Endurance Test (25 RPS for 30 minutes)..."
    log_warning "This test will take 30 minutes. Press Ctrl+C to cancel."
    
    # Wait for system recovery
    log_info "Waiting 60 seconds for system recovery..."
    sleep 60
    
    # Ask for confirmation
    if [[ "${RUN_ENDURANCE:-}" != "true" ]]; then
        read -p "Do you want to run the 30-minute endurance test? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_warning "Skipping endurance test"
            return 0
        fi
    fi
    
    cd "$SCRIPT_DIR"
    TARGET_URL="${HAPROXY_URL}" k6 run endurance-test.js \
        --out json="$RESULTS_DIR/endurance-results-$TIMESTAMP.json" \
        --summary-export="$RESULTS_DIR/endurance-summary-$TIMESTAMP.json" \
        2>&1 | tee "$RESULTS_DIR/endurance-output-$TIMESTAMP.txt"
    
    local exit_code=${PIPESTATUS[0]}
    
    if [ $exit_code -eq 0 ]; then
        log_success "Endurance Test completed successfully"
    else
        log_error "Endurance Test failed with exit code $exit_code"
        return $exit_code
    fi
}

record_post_test_status() {
    log_info "Recording post-test system status..."
    
    cd "$SCRIPT_DIR/../scripts"
    echo "=== POST-TEST SYSTEM STATUS ===" > "$RESULTS_DIR/load-test-final-$TIMESTAMP.txt"
    ./check-health.sh >> "$RESULTS_DIR/load-test-final-$TIMESTAMP.txt" 2>&1
    
    # Resource usage after tests
    echo -e "\n=== FINAL RESOURCE USAGE ===" >> "$RESULTS_DIR/load-test-final-$TIMESTAMP.txt"
    docker stats --no-stream >> "$RESULTS_DIR/load-test-final-$TIMESTAMP.txt" 2>&1
    
    # HAProxy stats
    echo -e "\n=== FINAL HAPROXY STATS ===" >> "$RESULTS_DIR/load-test-final-$TIMESTAMP.txt"
    curl -s "${HAPROXY_STATS_URL};csv" >> "$RESULTS_DIR/load-test-final-$TIMESTAMP.txt" 2>&1 || echo "HAProxy stats not available"
    
    log_success "Post-test status recorded"
}

generate_summary_report() {
    log_info "Generating load test summary report..."
    
    local report_file="$RESULTS_DIR/load-test-summary-$TIMESTAMP.md"
    
    cat > "$report_file" << EOF
# Sprint 1 Load Testing Results

**Date**: $(date)  
**Duration**: Started at $(echo $TIMESTAMP | cut -c1-8)_$(echo $TIMESTAMP | cut -c9-14)

## Test Summary

### Tests Executed

- ✅ **Steady Load Test**: 50 RPS sustained load
- ✅ **Spike Load Test**: 50→200→50 RPS traffic spike
- $([ -f "$RESULTS_DIR/endurance-output-$TIMESTAMP.txt" ] && echo "✅ **Endurance Test**: 25 RPS for 30 minutes" || echo "⏭️ **Endurance Test**: Skipped")

### Performance Results

#### Steady Load Test
- Check: \`$RESULTS_DIR/steady-load-summary-$TIMESTAMP.json\`
- Output: \`$RESULTS_DIR/steady-load-output-$TIMESTAMP.txt\`

#### Spike Load Test  
- Check: \`$RESULTS_DIR/spike-load-summary-$TIMESTAMP.json\`
- Output: \`$RESULTS_DIR/spike-load-output-$TIMESTAMP.txt\`

#### Endurance Test
$([ -f "$RESULTS_DIR/endurance-output-$TIMESTAMP.txt" ] && echo "- Check: \`$RESULTS_DIR/endurance-summary-$TIMESTAMP.json\`" || echo "- Not executed")
$([ -f "$RESULTS_DIR/endurance-output-$TIMESTAMP.txt" ] && echo "- Output: \`$RESULTS_DIR/endurance-output-$TIMESTAMP.txt\`" || echo "")

### System Analysis

- **Baseline**: \`$RESULTS_DIR/load-test-baseline-$TIMESTAMP.txt\`
- **Final Status**: \`$RESULTS_DIR/load-test-final-$TIMESTAMP.txt\`

### Sprint 1 Success Criteria

- [ ] Response times: p95 < 150ms (normal), p95 < 300ms (spike)
- [ ] Error rate < 2% under all load conditions  
- [ ] System stability maintained during 30-minute test
- [ ] Traffic distribution remains within 70-90% K3s range
- [ ] Resource usage stays within 6GB RAM constraints

**Review the individual result files above to validate these criteria.**

## Next Steps

1. Review performance metrics in JSON result files
2. Analyze traffic distribution in HAProxy stats
3. Validate resource usage remained within constraints  
4. Document any performance issues discovered
5. Proceed to Day 5: Final documentation and stability testing

EOF

    log_success "Summary report generated: $report_file"
}

# Main execution
main() {
    echo "🚀 Sprint 1 Load Testing Framework"
    echo "=================================="
    echo "Day 4 Implementation: Performance validation"
    echo ""
    
    check_prerequisites
    create_results_dir
    
    # Record baseline
    run_system_baseline
    
    # Execute load tests
    log_info "Starting load test sequence..."
    
    if run_steady_load_test; then
        log_success "✅ Steady load test passed"
    else
        log_error "❌ Steady load test failed"
        exit 1
    fi
    
    if run_spike_load_test; then
        log_success "✅ Spike load test passed"  
    else
        log_error "❌ Spike load test failed"
        exit 1
    fi
    
    # Endurance test (optional due to time)
    run_endurance_test
    
    # Record final state
    record_post_test_status
    
    # Generate report
    generate_summary_report
    
    echo ""
    log_success "🎉 Load testing framework implementation complete!"
    echo ""
    echo "📊 Results Summary:"
    echo "  - Baseline: $RESULTS_DIR/load-test-baseline-$TIMESTAMP.txt"
    echo "  - Steady Load: $RESULTS_DIR/steady-load-summary-$TIMESTAMP.json"
    echo "  - Spike Load: $RESULTS_DIR/spike-load-summary-$TIMESTAMP.json"
    if [ -f "$RESULTS_DIR/endurance-output-$TIMESTAMP.txt" ]; then
        echo "  - Endurance: $RESULTS_DIR/endurance-summary-$TIMESTAMP.json"
    fi
    echo "  - Summary Report: $RESULTS_DIR/load-test-summary-$TIMESTAMP.md"
    echo ""
    echo "📋 Next: Review results and proceed to Day 5 final documentation"
}

# Handle command line arguments
case "${1:-}" in
    --quick)
        log_info "Running quick tests only (no endurance test)"
        RUN_ENDURANCE="false"
        ;;
    --endurance-only)
        log_info "Running endurance test only"
        check_prerequisites
        create_results_dir
        run_endurance_test
        exit 0
        ;;
    --help)
        echo "Usage: $0 [--quick|--endurance-only|--help]"
        echo "  --quick: Run steady and spike tests only (skip 30-min endurance)"
        echo "  --endurance-only: Run only the 30-minute endurance test"
        echo "  --help: Show this help message"
        exit 0
        ;;
esac

# Run main function
main "$@"
