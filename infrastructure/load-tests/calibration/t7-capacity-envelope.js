/**
 * T7: Capacity Envelope Test
 *
 * Ramps from 50 → 300+ RPS in steps to find:
 * - SLO violation threshold (p99 > 200ms)
 * - Error threshold (error rate > 1%)
 * - Saturation ceiling
 *
 * Usage:
 *   k6 run infrastructure/load-tests/t7-capacity-envelope.js \
 *     -e ENDPOINT=/work?duration_ms=5
 *   k6 run infrastructure/load-tests/t7-capacity-envelope.js \
 *     -e ENDPOINT=/fib?n=25
 */

import http from 'k6/http';
import { check } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

const errorRate = new Rate('errors');
const latencyTrend = new Trend('latency_ms');
const sloViolations = new Counter('slo_violations');

const SLO_THRESHOLD_MS = 200;

export const options = {
    scenarios: {
        capacity_ramp: {
            executor: 'ramping-arrival-rate',
            startRate: 50,
            timeUnit: '1s',
            preAllocatedVUs: 300,
            maxVUs: 600,
            stages: [
                // Step 1: 50 RPS baseline (30s)
                { target: 50, duration: '30s' },
                // Step 2: Ramp to 100 (30s)
                { target: 100, duration: '30s' },
                // Step 3: Hold 100 (30s)
                { target: 100, duration: '30s' },
                // Step 4: Ramp to 150 (30s)
                { target: 150, duration: '30s' },
                // Step 5: Hold 150 (30s)
                { target: 150, duration: '30s' },
                // Step 6: Ramp to 200 (30s)
                { target: 200, duration: '30s' },
                // Step 7: Hold 200 (30s)
                { target: 200, duration: '30s' },
                // Step 8: Ramp to 250 (30s)
                { target: 250, duration: '30s' },
                // Step 9: Hold 250 (30s)
                { target: 250, duration: '30s' },
                // Step 10: Ramp to 300 (30s)
                { target: 300, duration: '30s' },
                // Step 11: Hold 300 (30s)
                { target: 300, duration: '30s' },
                // Step 12: Ramp to 400 (30s)
                { target: 400, duration: '30s' },
                // Step 13: Hold 400 (30s)
                { target: 400, duration: '30s' },
                // Step 14: Ramp to 500 (30s)
                { target: 500, duration: '30s' },
                // Step 15: Hold 500 (30s)
                { target: 500, duration: '30s' },
            ],
        },
    },
    thresholds: {
        'http_req_failed': ['rate<0.50'],
    },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:18082';
const ENDPOINT = __ENV.ENDPOINT || '/work?duration_ms=10';

export function setup() {
    console.log('\n🔬 T7: Capacity Envelope Test');
    console.log('================================');
    console.log(`Endpoint: ${BASE_URL}${ENDPOINT}`);
    console.log('Ramp: 50 → 100 → 150 → 200 → 250 → 300 → 400 → 500 RPS');
    console.log('Duration: 7.5 minutes (15 × 30s stages)');
    console.log('');

    const warmup = http.get(`${BASE_URL}/work?duration_ms=10`);
    if (warmup.status !== 200) {
        console.log(`⚠️ Warning: Health check returned ${warmup.status}`);
    }

    return { startTime: Date.now() };
}

export default function () {
    const res = http.get(`${BASE_URL}${ENDPOINT}`, {
        headers: {
            'Host': 'test-app.default.127.0.0.1.sslip.io',
        },
    });

    const duration = res.timings.duration;
    latencyTrend.add(duration);

    if (duration > SLO_THRESHOLD_MS) {
        sloViolations.add(1);
    }

    const success = check(res, {
        'status is 200': (r) => r.status === 200,
        'response < 200ms (SLO)': (r) => r.timings.duration < SLO_THRESHOLD_MS,
    });

    errorRate.add(!success);
}

export function teardown(data) {
    const elapsed = Math.round((Date.now() - data.startTime) / 1000);
    console.log(`\n📊 T7 Complete — ${elapsed}s elapsed`);
}

export function handleSummary(data) {
    const endpoint = __ENV.ENDPOINT || '/work?duration_ms=10';
    const label = endpoint.includes('fib') ? 'fib' : 'health';
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');

    const summary = {
        test: 't7-capacity-envelope',
        endpoint: endpoint,
        timestamp: new Date().toISOString(),
        metrics: {
            p50_latency_ms: data.metrics.http_req_duration?.['p(50)'] || 0,
            p95_latency_ms: data.metrics.http_req_duration?.['p(95)'] || 0,
            p99_latency_ms: data.metrics.http_req_duration?.['p(99)'] || 0,
            avg_latency_ms: data.metrics.http_req_duration?.avg || 0,
            min_latency_ms: data.metrics.http_req_duration?.min || 0,
            max_latency_ms: data.metrics.http_req_duration?.max || 0,
            error_rate: data.metrics.http_req_failed?.rate || 0,
            total_requests: data.metrics.http_reqs?.count || 0,
            actual_rps: data.metrics.http_reqs?.rate || 0,
            slo_violations: data.metrics.slo_violations?.count || 0,
        },
    };

    return {
        [`results/experiments/validation/2026-02-13_t7-capacity-envelope/raw/t7_${label}_${timestamp}.json`]: JSON.stringify(data, null, 2),
        stdout: JSON.stringify(summary, null, 2),
    };
}
