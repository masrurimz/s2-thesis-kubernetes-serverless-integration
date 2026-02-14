/**
 * Dynamic Burst Load Test - Multi-phase ramp/burst for PREDICTIVE triggering
 *
 * Workload profile designed to create repeated "healthy → surge" windows
 * that give the GRU predictor time to observe trends and issue PREDICTIVE actions.
 *
 * Phase B used steady 100 RPS which never triggered PREDICTIVE because there was
 * no ramp pattern for the GRU to predict. Phase A1's ramp test (20→100 RPS) DID
 * trigger PREDICTIVE. This script creates multiple such windows.
 *
 * Cycle pattern (repeated twice, ~5 min total):
 *   Phase 1: Baseline  (60s @ 30 RPS)  — healthy, no violations
 *   Phase 2: Ramp up   (30s @ 30→150 RPS) — GRU prediction window
 *   Phase 3: Burst     (60s @ 150 RPS)  — sustained peak load
 *   Phase 4: Cool down (30s @ 150→30 RPS) — recovery
 *
 * Cycle 1: 0s–180s, Cycle 2: 180s–360s (6 min total)
 */

import http from 'k6/http';
import { check } from 'k6';
import { Rate, Trend, Counter, Gauge } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const latencyTrend = new Trend('latency_ms');
const requestCounter = new Counter('total_requests');
const sloViolations = new Counter('slo_violations');
const currentPhase = new Gauge('current_phase');

// SLO threshold (p99 < 200ms)
const SLO_THRESHOLD_MS = 200;

export const options = {
    scenarios: {
        // ── Cycle 1 ──────────────────────────────────────
        // Phase 1: Baseline (0s–60s @ 30 RPS)
        c1_baseline: {
            executor: 'constant-arrival-rate',
            rate: 30,
            timeUnit: '1s',
            duration: '60s',
            preAllocatedVUs: 20,
            maxVUs: 50,
            startTime: '0s',
            tags: { phase: 'baseline', cycle: '1' },
        },
        // Phase 2: Ramp up (60s–90s @ 30→150 RPS)
        c1_ramp_up: {
            executor: 'ramping-arrival-rate',
            startRate: 30,
            timeUnit: '1s',
            preAllocatedVUs: 50,
            maxVUs: 200,
            stages: [
                { target: 150, duration: '30s' },
            ],
            startTime: '60s',
            tags: { phase: 'ramp_up', cycle: '1' },
        },
        // Phase 3: Burst peak (90s–150s @ 150 RPS)
        c1_burst: {
            executor: 'constant-arrival-rate',
            rate: 150,
            timeUnit: '1s',
            duration: '60s',
            preAllocatedVUs: 100,
            maxVUs: 200,
            startTime: '90s',
            tags: { phase: 'burst', cycle: '1' },
        },
        // Phase 4: Cool down (150s–180s @ 150→30 RPS)
        c1_cool_down: {
            executor: 'ramping-arrival-rate',
            startRate: 150,
            timeUnit: '1s',
            preAllocatedVUs: 50,
            maxVUs: 200,
            stages: [
                { target: 30, duration: '30s' },
            ],
            startTime: '150s',
            tags: { phase: 'cool_down', cycle: '1' },
        },

        // ── Cycle 2 ──────────────────────────────────────
        // Phase 1: Baseline (180s–240s @ 30 RPS)
        c2_baseline: {
            executor: 'constant-arrival-rate',
            rate: 30,
            timeUnit: '1s',
            duration: '60s',
            preAllocatedVUs: 20,
            maxVUs: 50,
            startTime: '180s',
            tags: { phase: 'baseline', cycle: '2' },
        },
        // Phase 2: Ramp up (240s–270s @ 30→150 RPS)
        c2_ramp_up: {
            executor: 'ramping-arrival-rate',
            startRate: 30,
            timeUnit: '1s',
            preAllocatedVUs: 50,
            maxVUs: 200,
            stages: [
                { target: 150, duration: '30s' },
            ],
            startTime: '240s',
            tags: { phase: 'ramp_up', cycle: '2' },
        },
        // Phase 3: Burst peak (270s–330s @ 150 RPS)
        c2_burst: {
            executor: 'constant-arrival-rate',
            rate: 150,
            timeUnit: '1s',
            duration: '60s',
            preAllocatedVUs: 100,
            maxVUs: 200,
            startTime: '270s',
            tags: { phase: 'burst', cycle: '2' },
        },
        // Phase 4: Cool down (330s–360s @ 150→30 RPS)
        c2_cool_down: {
            executor: 'ramping-arrival-rate',
            startRate: 150,
            timeUnit: '1s',
            preAllocatedVUs: 50,
            maxVUs: 200,
            stages: [
                { target: 30, duration: '30s' },
            ],
            startTime: '330s',
            tags: { phase: 'cool_down', cycle: '2' },
        },
    },
    thresholds: {
        'http_req_duration': ['p(95)<2000'],                     // Relaxed overall
        'http_req_duration{phase:baseline}': ['p(99)<200'],      // Baseline must meet SLO
        'http_req_duration{phase:burst}': ['p(50)<500'],         // Median stays reasonable
        'http_req_failed': ['rate<0.10'],                        // <10% error tolerance
        'slo_violations': ['count>0'],                           // Expect violations during bursts
    },
};

const BASE_URL = __ENV.BASE_URL || __ENV.TARGET_URL || 'http://localhost:18082';
const ENDPOINT = __ENV.ENDPOINT || '/work?duration_ms=5';

export function setup() {
    console.log('\n🔬 Dynamic Burst Load Test for Phase C');
    console.log('========================================');
    console.log('Cycle pattern (×2):');
    console.log('  Phase 1: 60s @ 30 RPS  (baseline)');
    console.log('  Phase 2: 30s @ 30→150 RPS (ramp — GRU prediction window)');
    console.log('  Phase 3: 60s @ 150 RPS (burst peak)');
    console.log('  Phase 4: 30s @ 150→30 RPS (cool down)');
    console.log(`Total duration: ~6 minutes`);
    console.log(`SLO threshold: p99 < ${SLO_THRESHOLD_MS}ms`);
    console.log(`Target: ${BASE_URL}${ENDPOINT}`);
    console.log('');

    // Verify endpoint is reachable
    const warmup = http.get(`${BASE_URL}/work?duration_ms=5`);
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
    requestCounter.add(1);

    if (duration > SLO_THRESHOLD_MS) {
        sloViolations.add(1);
    }

    const success = check(res, {
        'status is 200': (r) => r.status === 200,
        'response < 200ms (SLO)': (r) => r.timings.duration < SLO_THRESHOLD_MS,
        'response < 1s': (r) => r.timings.duration < 1000,
    });

    errorRate.add(!success);
}

export function teardown(data) {
    const elapsed = Math.round((Date.now() - data.startTime) / 1000);
    console.log('\n📊 Dynamic Burst Test Complete');
    console.log('================================');
    console.log(`Total duration: ${elapsed}s`);

    const health = http.get(`${BASE_URL}/work?duration_ms=5`);
    console.log(`Post-test health: ${health.status === 200 ? '✅ HEALTHY' : '❌ DEGRADED'}`);

    console.log('\n🔍 Analysis guidance:');
    console.log('- Compare p99 during ramp_up and burst phases (S3 vs S4)');
    console.log('- H2 validated if: S4 issues PREDICTIVE during ramp_up phases');
    console.log('- Check daemon decision_counts for PREDICTIVE > 0 in S4');
    console.log('- Prometheus: routing_daemon_decision_action_total{action="PREDICTIVE"}');
}

export function handleSummary(data) {
    const scenario = __ENV.SCENARIO || 'unknown';
    const run = __ENV.RUN_ID || '0';
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');

    const p50 = data.metrics.http_req_duration?.['p(50)'] || 0;
    const p95 = data.metrics.http_req_duration?.['p(95)'] || 0;
    const p99 = data.metrics.http_req_duration?.['p(99)'] || 0;
    const errRate = data.metrics.errors?.rate || 0;
    const totalRequests = data.metrics.http_reqs?.count || 0;
    const actualRPS = data.metrics.http_reqs?.rate || 0;

    const summary = {
        scenario: scenario,
        run_id: parseInt(run),
        workload: 'dynamic_burst',
        timestamp: new Date().toISOString(),
        duration_sec: 360,
        metrics: {
            p50_latency_ms: p50,
            p95_latency_ms: p95,
            p99_latency_ms: p99,
            error_rate: errRate,
            total_requests: totalRequests,
            actual_rps: actualRPS,
            slo_violations: data.metrics.slo_violations?.count || 0,
        },
    };

    const outDir = __ENV.RESULTS_DIR || 'results/load-tests';

    return {
        [`${outDir}/dynamic_burst_${scenario}_run${run}_${timestamp}.json`]: JSON.stringify(data, null, 2),
        stdout: JSON.stringify(summary, null, 2),
    };
}
