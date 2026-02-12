import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend, Gauge } from 'k6/metrics';

// Custom metrics for SLO violation detection
export let slo_violations = new Counter('slo_violations');
export let cold_start_detected = new Counter('cold_start_detected');
export let response_time = new Trend('response_time');
export let error_rate = new Rate('errors');
export let current_phase = new Gauge('current_phase');

// Test endpoints - use CPU-intensive /fib endpoint
const HYBRID_ENDPOINT = __ENV.TARGET_URL || 'http://localhost:18082';
const FIB_N = __ENV.FIB_N || '35';  // CPU-intensive Fibonacci calculation

// SLO threshold (200ms p99)
const SLO_THRESHOLD_MS = 200;

// Aggressive spike pattern to trigger SCALE_OUT
// Phase A: Steady low load
// Phase B: Idle (forces cold-start)
// Phase C: High spike with CPU load (should saturate K8s and trigger scale-out)
const CYCLES = 3;

export let options = {
  scenarios: {
    // Cycle 1: Warmup and baseline
    steady_1: {
      executor: 'constant-arrival-rate',
      rate: 30,
      timeUnit: '1s',
      duration: '30s',
      preAllocatedVUs: 50,
      maxVUs: 100,
      startTime: '0s',
      tags: { phase: 'steady', cycle: '1' },
    },
    idle_1: {
      executor: 'constant-arrival-rate',
      rate: 1,
      timeUnit: '20s',
      duration: '20s',
      preAllocatedVUs: 1,
      maxVUs: 1,
      startTime: '30s',
      tags: { phase: 'idle', cycle: '1' },
    },
    spike_1: {
      executor: 'constant-arrival-rate',
      rate: 400,  // Aggressive spike
      timeUnit: '1s',
      duration: '25s',
      preAllocatedVUs: 300,
      maxVUs: 500,
      startTime: '50s',
      tags: { phase: 'spike', cycle: '1' },
    },
    // Cycle 2: Should see adaptive behavior
    steady_2: {
      executor: 'constant-arrival-rate',
      rate: 30,
      timeUnit: '1s',
      duration: '30s',
      preAllocatedVUs: 50,
      maxVUs: 100,
      startTime: '75s',
      tags: { phase: 'steady', cycle: '2' },
    },
    idle_2: {
      executor: 'constant-arrival-rate',
      rate: 1,
      timeUnit: '20s',
      duration: '20s',
      preAllocatedVUs: 1,
      maxVUs: 1,
      startTime: '105s',
      tags: { phase: 'idle', cycle: '2' },
    },
    spike_2: {
      executor: 'constant-arrival-rate',
      rate: 500,  // Even higher spike
      timeUnit: '1s',
      duration: '25s',
      preAllocatedVUs: 400,
      maxVUs: 600,
      startTime: '125s',
      tags: { phase: 'spike', cycle: '2' },
    },
    // Cycle 3: Peak stress
    steady_3: {
      executor: 'constant-arrival-rate',
      rate: 30,
      timeUnit: '1s',
      duration: '30s',
      preAllocatedVUs: 50,
      maxVUs: 100,
      startTime: '150s',
      tags: { phase: 'steady', cycle: '3' },
    },
    idle_3: {
      executor: 'constant-arrival-rate',
      rate: 1,
      timeUnit: '20s',
      duration: '20s',
      preAllocatedVUs: 1,
      maxVUs: 1,
      startTime: '180s',
      tags: { phase: 'idle', cycle: '3' },
    },
    spike_3: {
      executor: 'constant-arrival-rate',
      rate: 600,  // Maximum spike
      timeUnit: '1s',
      duration: '25s',
      preAllocatedVUs: 500,
      maxVUs: 700,
      startTime: '200s',
      tags: { phase: 'spike', cycle: '3' },
    },
  },
  thresholds: {
    'http_req_duration': ['p(95)<5000'],  // 5s p95 tolerance for stress test
    'http_req_duration{phase:steady}': ['p(99)<500'],
    'http_req_duration{phase:spike}': ['p(50)<2000'],  // Expect high latency under spike
    'http_req_failed': ['rate<0.3'],  // 30% error tolerance during extreme spikes
    'slo_violations': ['count>100'],  // Expect many violations to trigger scale-out
  },
};

export function setup() {
  console.log('\n🔥 STRESS TEST: Spike-with-Idle for SCALE_OUT Triggering');
  console.log('=========================================================');
  console.log(`Cycles: ${CYCLES}`);
  console.log('Pattern per cycle:');
  console.log('  Phase A: 30s @ 30 rps (steady warmup)');
  console.log('  Phase B: 20s @ idle (forces cold-start)');
  console.log('  Phase C: 25s @ 400-600 rps (aggressive spike)');
  console.log(`Endpoint: ${HYBRID_ENDPOINT}/fib?n=${FIB_N} (CPU-intensive)`);
  console.log(`SLO Threshold: p99 < ${SLO_THRESHOLD_MS}ms`);
  console.log('');
  
  // Verify endpoint is up
  let warmup = http.get(HYBRID_ENDPOINT + '/health');
  if (warmup.status !== 200) {
    console.log(`⚠️ Warning: Health check returned ${warmup.status}`);
  }
  
  // Warm up the fib endpoint
  let fibCheck = http.get(`${HYBRID_ENDPOINT}/fib?n=10`);
  console.log(`Fib endpoint check: ${fibCheck.status} (${fibCheck.timings.duration}ms)`);
  
  return { startTime: Date.now() };
}

export default function () {
  // Determine current phase from scenario tags
  let phase = __ENV.PHASE || 'unknown';
  
  // Skip actual requests during idle phase
  if (__ITER === 0 && phase === 'idle') {
    sleep(1);
    return;
  }
  
  // Use CPU-intensive /fib endpoint to saturate K8s
  let endpoint = `${HYBRID_ENDPOINT}/fib?n=${FIB_N}`;
  let response = http.get(endpoint, {
    timeout: '30s',  // Allow longer timeout for stress test
  });
  
  // Record response time
  let duration = response.timings.duration;
  response_time.add(duration);
  
  // Check for SLO violation
  if (duration > SLO_THRESHOLD_MS) {
    slo_violations.add(1);
  }
  
  // Detect cold start
  if (duration > 5000) {
    cold_start_detected.add(1);
  }
  
  // Standard checks
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response < 200ms (SLO)': (r) => r.timings.duration < SLO_THRESHOLD_MS,
    'response < 1s': (r) => r.timings.duration < 1000,
    'response < 5s': (r) => r.timings.duration < 5000,
  });
  
  error_rate.add(response.status !== 200);
  
  // Minimal sleep
  sleep(0.01);
}

export function teardown(data) {
  console.log('\n📊 Stress Test Results');
  console.log('======================');
  console.log(`Total duration: ${Math.round((Date.now() - data.startTime) / 1000)}s`);
  
  // Final health check
  let health = http.get(HYBRID_ENDPOINT + '/health');
  console.log(`\nPost-test health: ${health.status === 200 ? '✅ HEALTHY' : '❌ DEGRADED'}`);
  
  console.log('\n🔍 Expected Outcomes:');
  console.log('- High SLO violations during spike phases');
  console.log('- SCALE_OUT decisions triggered by algorithm');
  console.log('- Weight shift toward serverless during spikes');
  console.log('- Recovery to OPTIMIZE_COST after spike passes');
  
  console.log('\nCheck daemon status: curl http://localhost:9104/status');
  console.log('Check metrics: curl http://localhost:9104/metrics | grep scale_out');
}
