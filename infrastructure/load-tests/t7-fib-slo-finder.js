/**
 * T7c: SLO Threshold Finder — /fib?n=25
 * Fine-grained ramp 10-200 RPS to find exact SLO violation point.
 */

import http from 'k6/http';
import { check } from 'k6';
import { Rate, Counter } from 'k6/metrics';

const errorRate = new Rate('errors');
const sloViolations = new Counter('slo_violations');
const SLO_THRESHOLD_MS = 200;

export const options = {
    scenarios: {
        slo_finder: {
            executor: 'ramping-arrival-rate',
            startRate: 10,
            timeUnit: '1s',
            preAllocatedVUs: 100,
            maxVUs: 500,
            stages: [
                // Gentle ramp with holds at each level
                { target: 10, duration: '20s' },
                { target: 20, duration: '10s' },
                { target: 20, duration: '20s' },
                { target: 30, duration: '10s' },
                { target: 30, duration: '20s' },
                { target: 50, duration: '10s' },
                { target: 50, duration: '20s' },
                { target: 75, duration: '10s' },
                { target: 75, duration: '20s' },
                { target: 100, duration: '10s' },
                { target: 100, duration: '20s' },
                { target: 125, duration: '10s' },
                { target: 125, duration: '20s' },
                { target: 150, duration: '10s' },
                { target: 150, duration: '20s' },
                { target: 175, duration: '10s' },
                { target: 175, duration: '20s' },
                { target: 200, duration: '10s' },
                { target: 200, duration: '20s' },
            ],
        },
    },
    thresholds: {
        'http_req_failed': ['rate<0.50'],
    },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:18082';

export function setup() {
    console.log('\n🔬 T7c: /fib SLO Threshold Finder');
    console.log('Ramp: 10 → 20 → 30 → 50 → 75 → 100 → 125 → 150 → 175 → 200 RPS');
    console.log('Duration: ~5 min with holds at each level');
    const warmup = http.get(`${BASE_URL}/work?duration_ms=5`);
    return { startTime: Date.now() };
}

export default function () {
    const res = http.get(`${BASE_URL}/fib?n=25`, {
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
        [`results/experiments/validation/2026-02-13_t7-capacity-envelope/raw/t7c_fib_slo_${ts}.json`]: JSON.stringify(data, null, 2),
        stdout: JSON.stringify({
            test: 't7c-fib-slo-finder',
            p50: data.metrics.http_req_duration?.values?.['p(50)'] || 0,
            p95: data.metrics.http_req_duration?.values?.['p(95)'] || 0,
            p99: data.metrics.http_req_duration?.values?.['p(99)'] || 0,
            avg: data.metrics.http_req_duration?.values?.avg || 0,
            max: data.metrics.http_req_duration?.values?.max || 0,
            error_rate: data.metrics.http_req_failed?.values?.rate || 0,
            total_reqs: data.metrics.http_reqs?.values?.count || 0,
            rps: data.metrics.http_reqs?.values?.rate || 0,
            slo_violations: data.metrics.slo_violations?.values?.count || 0,
            dropped: data.metrics.dropped_iterations?.values?.count || 0,
        }, null, 2),
    };
}
