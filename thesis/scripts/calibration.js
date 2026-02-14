/**
 * Workload Calibration Test
 * 
 * Used to find "Goldilocks" load where:
 * - S1 (K8s-only) shows stress but not total collapse
 * - S2 (Serverless-only) handles easily  
 * - S3/S4 (Hybrid) can demonstrate improvement
 * 
 * Configurable via RPS environment variable.
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

const errorRate = new Rate('errors');
const latencyTrend = new Trend('latency_ms');
const requestCounter = new Counter('total_requests');

// Get RPS from environment variable, default to 100
const targetRPS = parseInt(__ENV.RPS || '100');
const durationMinutes = parseInt(__ENV.DURATION || '3');

export const options = {
    scenarios: {
        calibration: {
            executor: 'constant-arrival-rate',
            rate: targetRPS,
            timeUnit: '1s',
            duration: `${durationMinutes}m`,
            preAllocatedVUs: Math.min(targetRPS * 2, 200),
            maxVUs: Math.min(targetRPS * 3, 300),
        },
    },
    thresholds: {
        http_req_duration: ['p(99)<500'],
        errors: ['rate<0.10'],
    },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:18082';
const ENDPOINT = __ENV.ENDPOINT || '/work?duration_ms=5';

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
    });
    
    errorRate.add(!success);
}

export function handleSummary(data) {
    const rps = __ENV.RPS || '100';
    const scenario = __ENV.SCENARIO || 'unknown';
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    
    // Calculate key metrics
    const p50 = data.metrics.http_req_duration?.['p(50)'] || 0;
    const p95 = data.metrics.http_req_duration?.['p(95)'] || 0;
    const p99 = data.metrics.http_req_duration?.['p(99)'] || 0;
    const errorRate = data.metrics.errors?.rate || 0;
    const totalRequests = data.metrics.http_reqs?.count || 0;
    const actualRPS = data.metrics.http_reqs?.rate || 0;
    
    // Determine stress level
    let stressLevel = 'healthy';
    if (p99 > 200) stressLevel = 'stressed';
    if (p99 > 500) stressLevel = 'severe';
    if (errorRate > 0.05) stressLevel = 'critical';
    
    const summary = {
        scenario: scenario,
        target_rps: parseInt(rps),
        actual_rps: actualRPS,
        duration_min: parseInt(durationMinutes),
        timestamp: new Date().toISOString(),
        metrics: {
            p50_latency_ms: p50,
            p95_latency_ms: p95,
            p99_latency_ms: p99,
            error_rate: errorRate,
            total_requests: totalRequests,
        },
        stress_level: stressLevel,
        recommended_for_experiments: stressLevel === 'stressed' || stressLevel === 'healthy',
    };
    
    return {
        [`results/calibration/calibration_${scenario}_${rps}rps_${timestamp}.json`]: JSON.stringify(data, null, 2),
        stdout: JSON.stringify(summary, null, 2),
    };
}
