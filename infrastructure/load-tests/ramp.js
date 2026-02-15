/**
 * Ramp Load Test - For PREDICTIVE Action Triggering
 * 
 * Workload profile designed to trigger PREDICTIVE scaling:
 * 1. Baseline (60s @ 20 RPS) - Healthy state, no violations
 * 2. Ramp up (60s @ 20→100 RPS) - GRU should predict surge
 * 3. Peak (120s @ 100 RPS) - Violations occur if not pre-scaled
 * 
 * Total: 4 minutes
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const latencyTrend = new Trend('latency_ms');
const requestCounter = new Counter('total_requests');

export const options = {
    scenarios: {
        // Phase 1: Baseline - healthy state
        baseline: {
            executor: 'constant-arrival-rate',
            rate: 20,           // 20 RPS - should be healthy
            timeUnit: '1s',
            duration: '60s',
            preAllocatedVUs: 10,
            maxVUs: 20,
        },
        // Phase 2: Ramp - gradual increase (GRU prediction window)
        ramp: {
            executor: 'ramping-arrival-rate',
            startRate: 20,
            timeUnit: '1s',
            preAllocatedVUs: 20,
            maxVUs: 100,
            stages: [
                { target: 100, duration: '60s' },  // Ramp 20→100 RPS over 60s
            ],
        },
        // Phase 3: Peak - sustained high load
        peak: {
            executor: 'constant-arrival-rate',
            rate: 100,          // 100 RPS - should cause stress
            timeUnit: '1s',
            duration: '120s',
            preAllocatedVUs: 50,
            maxVUs: 100,
            startTime: '120s',  // Start after baseline + ramp
        },
    },
    thresholds: {
        http_req_duration: ['p(99)<500'],  // Relaxed threshold for this test
        errors: ['rate<0.10'],              // Error rate < 10%
    },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:18082';
const ENDPOINT = __ENV.ENDPOINT || '/fib?n=32';

export default function () {
    const start = Date.now();
    
    const res = http.get(`${BASE_URL}${ENDPOINT}`, {
        headers: {
            'Host': 'test-app.default.127.0.0.1.sslip.io',
        },
    });
    
    const latency = Date.now() - start;
    latencyTrend.add(latency);
    requestCounter.add(1);
    
    const success = check(res, {
        'status is 200': (r) => r.status === 200,
        'response time < 500ms': (r) => r.timings.duration < 500,
    });
    
    errorRate.add(!success);
}

export function handleSummary(data) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    return {
        [`results/load-tests/ramp-${timestamp}.json`]: JSON.stringify(data, null, 2),
        stdout: JSON.stringify({
            scenario: 'ramp',
            timestamp: new Date().toISOString(),
            metrics: {
                p99_latency: data.metrics.http_req_duration?.['p(99)'],
                p95_latency: data.metrics.http_req_duration?.['p(95)'],
                avg_latency: data.metrics.http_req_duration?.avg,
                error_rate: data.metrics.errors?.rate,
                total_requests: data.metrics.http_reqs?.count,
                rps: data.metrics.http_reqs?.rate,
            },
            checks: {
                passes: data.metrics.checks?.passes,
                fails: data.metrics.checks?.fails,
            },
        }, null, 2),
    };
}
