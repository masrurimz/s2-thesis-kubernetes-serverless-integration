/**
 * T7a: Capacity Envelope — /work?duration_ms=10 endpoint
 * Quick ramp to very high RPS to find ceiling of work endpoint.
 */

import http from 'k6/http';
import { check } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

const errorRate = new Rate('errors');
const sloViolations = new Counter('slo_violations');
const SLO_THRESHOLD_MS = 200;

export const options = {
    scenarios: {
        capacity_ramp: {
            executor: 'ramping-arrival-rate',
            startRate: 100,
            timeUnit: '1s',
            preAllocatedVUs: 500,
            maxVUs: 1500,
            stages: [
                { target: 100, duration: '15s' },
                { target: 200, duration: '15s' },
                { target: 200, duration: '15s' },
                { target: 500, duration: '15s' },
                { target: 500, duration: '15s' },
                { target: 1000, duration: '15s' },
                { target: 1000, duration: '15s' },
                { target: 1500, duration: '15s' },
                { target: 1500, duration: '15s' },
                { target: 2000, duration: '15s' },
                { target: 2000, duration: '15s' },
                { target: 3000, duration: '15s' },
                { target: 3000, duration: '15s' },
            ],
        },
    },
    thresholds: {
        'http_req_failed': ['rate<0.50'],
    },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:18082';

export function setup() {
    console.log('\n🔬 T7a: /work?duration_ms=10 Capacity Envelope');
    console.log('Ramp: 100 → 200 → 500 → 1000 → 1500 → 2000 → 3000 RPS');
    console.log('Duration: 3.25 min');
    const warmup = http.get(`${BASE_URL}/work?duration_ms=10`);
    return { startTime: Date.now() };
}

export default function () {
    const res = http.get(`${BASE_URL}/work?duration_ms=10`, {
        headers: { 'Host': 'test-app.default.127.0.0.1.sslip.io' },
    });
    if (res.timings.duration > SLO_THRESHOLD_MS) sloViolations.add(1);
    const success = check(res, {
        'status is 200': (r) => r.status === 200,
        'response < 200ms': (r) => r.timings.duration < SLO_THRESHOLD_MS,
    });
    errorRate.add(!success);
}

export function handleSummary(data) {
    const ts = new Date().toISOString().replace(/[:.]/g, '-');
    return {
        [`results/experiments/validation/2026-02-13_t7-capacity-envelope/raw/t7a_health_${ts}.json`]: JSON.stringify(data, null, 2),
        stdout: JSON.stringify({
            test: 't7a-health',
            p50: data.metrics.http_req_duration?.['p(50)'] || 0,
            p95: data.metrics.http_req_duration?.['p(95)'] || 0,
            p99: data.metrics.http_req_duration?.['p(99)'] || 0,
            avg: data.metrics.http_req_duration?.avg || 0,
            max: data.metrics.http_req_duration?.max || 0,
            error_rate: data.metrics.http_req_failed?.rate || 0,
            total_reqs: data.metrics.http_reqs?.count || 0,
            rps: data.metrics.http_reqs?.rate || 0,
            slo_violations: data.metrics.slo_violations?.count || 0,
        }, null, 2),
    };
}
