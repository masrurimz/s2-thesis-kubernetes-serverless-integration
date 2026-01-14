/**
 * Endurance Load Test
 * 
 * Long-running test with varying load pattern.
 * Duration: 30 minutes with sine wave pattern
 */

import http from 'k6/http';
import { check } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

const errorRate = new Rate('errors');
const latencyTrend = new Trend('latency_ms');
const requestCount = new Counter('total_requests');

export const options = {
    scenarios: {
        endurance: {
            executor: 'ramping-arrival-rate',
            startRate: 100,
            timeUnit: '1s',
            preAllocatedVUs: 200,
            maxVUs: 400,
            stages: [
                // Sine wave pattern over 30 minutes
                { target: 100, duration: '2m' },
                { target: 200, duration: '3m' },
                { target: 150, duration: '2m' },
                { target: 50, duration: '3m' },
                { target: 100, duration: '2m' },
                { target: 200, duration: '3m' },
                { target: 150, duration: '2m' },
                { target: 50, duration: '3m' },
                { target: 100, duration: '2m' },
                { target: 200, duration: '3m' },
                { target: 100, duration: '5m' },
            ],
        },
    },
    thresholds: {
        http_req_duration: ['p(99)<200'],
        errors: ['rate<0.01'],
    },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8082';

export default function () {
    const start = Date.now();
    
    const res = http.get(`${BASE_URL}/`);
    
    latencyTrend.add(Date.now() - start);
    requestCount.add(1);
    
    const success = check(res, {
        'status is 200': (r) => r.status === 200,
        'response time < 200ms': (r) => r.timings.duration < 200,
    });
    
    errorRate.add(!success);
}

export function handleSummary(data) {
    return {
        'results/load-tests/endurance-summary.json': JSON.stringify(data, null, 2),
    };
}
