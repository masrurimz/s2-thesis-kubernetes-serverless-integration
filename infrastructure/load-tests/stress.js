/**
 * Stress Load Test
 * 
 * Creates capacity pressure by ramping to 1000+ req/s.
 * Designed to overwhelm throttled K8s pods (cpu=10m) while
 * demonstrating hybrid routing value.
 * 
 * Pattern: warm-up -> ramp to stress -> hold -> ramp down
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

const errorRate = new Rate('errors');
const latencyTrend = new Trend('latency_ms');
const successCounter = new Counter('success_total');
const failCounter = new Counter('fail_total');

export const options = {
    scenarios: {
        stress: {
            executor: 'ramping-arrival-rate',
            startRate: 50,
            timeUnit: '1s',
            preAllocatedVUs: 200,
            maxVUs: 1000,
            stages: [
                { target: 50, duration: '30s' },     // Warm-up (baseline)
                { target: 500, duration: '30s' },   // Ramp to moderate
                { target: 1000, duration: '30s' },  // Ramp to stress
                { target: 1000, duration: '1m' },   // Hold stress level
                { target: 500, duration: '30s' },   // Ramp down
                { target: 50, duration: '30s' },    // Recovery
            ],
        },
    },
    thresholds: {
        http_req_duration: ['p(95)<500', 'p(99)<1000'],
        errors: ['rate<0.10'],  // Allow 10% errors (realistic stress test)
    },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8082';

export default function () {
    const start = Date.now();
    
    const res = http.get(`${BASE_URL}/work?duration_ms=5`, {
        timeout: '5s',
    });
    
    const latency = Date.now() - start;
    latencyTrend.add(latency);
    
    const success = check(res, {
        'status is 200': (r) => r.status === 200,
        'latency < 500ms': (r) => latency < 500,
    });
    
    if (success) {
        successCounter.add(1);
    } else {
        failCounter.add(1);
    }
    
    errorRate.add(!success);
}

export function handleSummary(data) {
    const scenario = __ENV.SCENARIO || 'unknown';
    return {
        [`results/load-tests/stress-${scenario}-summary.json`]: JSON.stringify(data, null, 2),
        'stdout': textSummary(data),
    };
}

function textSummary(data) {
    const metrics = data.metrics;
    const httpDuration = metrics.http_req_duration || {};
    const errors = metrics.errors || {};
    
    return `
================================================================================
STRESS TEST RESULTS - ${__ENV.SCENARIO || 'unknown'}
================================================================================
Total Requests:     ${metrics.http_reqs?.values?.count || 0}
Success Rate:       ${((1 - (errors.values?.rate || 0)) * 100).toFixed(2)}%
Error Rate:         ${((errors.values?.rate || 0) * 100).toFixed(2)}%

Latency (ms):
  p50:              ${(httpDuration.values?.['p(50)'] || 0).toFixed(2)}
  p90:              ${(httpDuration.values?.['p(90)'] || 0).toFixed(2)}
  p95:              ${(httpDuration.values?.['p(95)'] || 0).toFixed(2)}
  p99:              ${(httpDuration.values?.['p(99)'] || 0).toFixed(2)}
  max:              ${(httpDuration.values?.max || 0).toFixed(2)}

Throughput:         ${(metrics.http_reqs?.values?.rate || 0).toFixed(2)} req/s
================================================================================
`;
}
