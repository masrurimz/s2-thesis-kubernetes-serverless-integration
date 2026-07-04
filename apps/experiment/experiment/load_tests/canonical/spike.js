/**
 * Spike Load Test
 * 
 * Tests system response to sudden traffic spikes.
 * Pattern: baseline -> 10x spike -> baseline
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const errorRate = new Rate('errors');
const latencyTrend = new Trend('latency_ms');

export const options = {
    scenarios: {
        spike: {
            executor: 'ramping-arrival-rate',
            startRate: 50,
            timeUnit: '1s',
            preAllocatedVUs: 100,
            maxVUs: 500,
            stages: [
                { target: 50, duration: '1m' },    // Baseline
                { target: 500, duration: '30s' },  // Spike up
                { target: 500, duration: '1m' },   // Hold spike
                { target: 50, duration: '30s' },   // Spike down
                { target: 50, duration: '1m' },    // Recovery
            ],
        },
    },
    thresholds: {
        http_req_duration: ['p(95)<300', 'p(99)<500'],
        errors: ['rate<0.05'],  // Allow 5% errors during spike
    },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8082';

export default function () {
    const start = Date.now();
    
    const res = http.get(`${BASE_URL}/`);
    
    latencyTrend.add(Date.now() - start);
    
    const success = check(res, {
        'status is 200': (r) => r.status === 200,
    });
    
    errorRate.add(!success);
}

export function handleSummary(data) {
    return {
        'results/load-tests/spike-summary.json': JSON.stringify(data, null, 2),
    };
}
