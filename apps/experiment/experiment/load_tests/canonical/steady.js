/**
 * Steady Load Test
 * 
 * Constant load for baseline measurement.
 * Duration: 5 minutes at 100 RPS
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const latencyTrend = new Trend('latency_ms');

export const options = {
    scenarios: {
        steady: {
            executor: 'constant-arrival-rate',
            rate: 100,           // 100 RPS
            timeUnit: '1s',
            duration: '5m',
            preAllocatedVUs: 50,
            maxVUs: 100,
        },
    },
    thresholds: {
        http_req_duration: ['p(99)<200'],  // 99th percentile < 200ms
        errors: ['rate<0.01'],              // Error rate < 1%
    },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8082';

export default function () {
    const start = Date.now();
    
    const res = http.get(`${BASE_URL}/`);
    
    const latency = Date.now() - start;
    latencyTrend.add(latency);
    
    const success = check(res, {
        'status is 200': (r) => r.status === 200,
        'response time < 200ms': (r) => r.timings.duration < 200,
    });
    
    errorRate.add(!success);
}

export function handleSummary(data) {
    return {
        'results/load-tests/steady-summary.json': JSON.stringify(data, null, 2),
    };
}
