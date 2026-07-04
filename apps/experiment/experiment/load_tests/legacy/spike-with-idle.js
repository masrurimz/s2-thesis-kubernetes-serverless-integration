import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend, Gauge } from 'k6/metrics';

// Custom metrics for SLO violation detection
export let slo_violations = new Counter('slo_violations');
export let cold_start_detected = new Counter('cold_start_detected');
export let response_time = new Trend('response_time');
export let error_rate = new Rate('errors');
export let current_phase = new Gauge('current_phase');

// Test endpoints
const HYBRID_ENDPOINT = __ENV.TARGET_URL || 'http://localhost:18082';
const HAPROXY_STATS = __ENV.HAPROXY_STATS_URL || 'http://localhost:18404/stats';

// SLO threshold (200ms p99)
const SLO_THRESHOLD_MS = 200;

// Cycle configuration: A → B → C pattern
// Phase A: Steady low load (no violation)
// Phase B: Idle period (forces cold-start on serverless)
// Phase C: Spike (breaks SLO, triggers Algorithm 1)
const CYCLES = 3;

export let options = {
  scenarios: {
    // Cycle 1
    steady_1: {
      executor: 'constant-arrival-rate',
      rate: 20,
      timeUnit: '1s',
      duration: '30s',
      preAllocatedVUs: 30,
      maxVUs: 50,
      startTime: '0s',
      tags: { phase: 'steady', cycle: '1' },
    },
    idle_1: {
      executor: 'constant-arrival-rate',
      rate: 1,
      timeUnit: '20s',  // 1 request per 20s = essentially idle
      duration: '20s',
      preAllocatedVUs: 1,
      maxVUs: 1,
      startTime: '30s',
      tags: { phase: 'idle', cycle: '1' },
    },
    spike_1: {
      executor: 'constant-arrival-rate',
      rate: 200,
      timeUnit: '1s',
      duration: '20s',
      preAllocatedVUs: 200,
      maxVUs: 300,
      startTime: '50s',
      tags: { phase: 'spike', cycle: '1' },
    },
    // Cycle 2
    steady_2: {
      executor: 'constant-arrival-rate',
      rate: 20,
      timeUnit: '1s',
      duration: '30s',
      preAllocatedVUs: 30,
      maxVUs: 50,
      startTime: '70s',
      tags: { phase: 'steady', cycle: '2' },
    },
    idle_2: {
      executor: 'constant-arrival-rate',
      rate: 1,
      timeUnit: '20s',
      duration: '20s',
      preAllocatedVUs: 1,
      maxVUs: 1,
      startTime: '100s',
      tags: { phase: 'idle', cycle: '2' },
    },
    spike_2: {
      executor: 'constant-arrival-rate',
      rate: 200,
      timeUnit: '1s',
      duration: '20s',
      preAllocatedVUs: 200,
      maxVUs: 300,
      startTime: '120s',
      tags: { phase: 'spike', cycle: '2' },
    },
    // Cycle 3
    steady_3: {
      executor: 'constant-arrival-rate',
      rate: 20,
      timeUnit: '1s',
      duration: '30s',
      preAllocatedVUs: 30,
      maxVUs: 50,
      startTime: '140s',
      tags: { phase: 'steady', cycle: '3' },
    },
    idle_3: {
      executor: 'constant-arrival-rate',
      rate: 1,
      timeUnit: '20s',
      duration: '20s',
      preAllocatedVUs: 1,
      maxVUs: 1,
      startTime: '170s',
      tags: { phase: 'idle', cycle: '3' },
    },
    spike_3: {
      executor: 'constant-arrival-rate',
      rate: 200,
      timeUnit: '1s',
      duration: '20s',
      preAllocatedVUs: 200,
      maxVUs: 300,
      startTime: '190s',
      tags: { phase: 'spike', cycle: '3' },
    },
  },
  thresholds: {
    // Track SLO violations - these are expected during spikes
    'http_req_duration': ['p(95)<2000'], // Relaxed p95 due to cold starts
    'http_req_duration{phase:steady}': ['p(99)<200'], // Steady should meet SLO
    'http_req_duration{phase:spike}': ['p(50)<500'], // Median should stay reasonable
    'http_req_failed': ['rate<0.1'], // 10% error tolerance during spikes
    'slo_violations': ['count>0'], // We WANT violations to prove hypothesis
  },
};

export function setup() {
  console.log('\n🔬 Spike-with-Idle Load Test for H1/H2 Validation');
  console.log('==================================================');
  console.log(`Cycles: ${CYCLES}`);
  console.log('Pattern per cycle:');
  console.log('  Phase A: 30s @ 20 rps (steady, SLO should pass)');
  console.log('  Phase B: 20s @ 0 rps (idle, forces cold-start)');
  console.log('  Phase C: 20s @ 200 rps (spike, expect SLO violation)');
  console.log(`SLO Threshold: p99 < ${SLO_THRESHOLD_MS}ms`);
  console.log(`Target: ${HYBRID_ENDPOINT}`);
  console.log('');
  
  // Verify endpoint is up
  let warmup = http.get(HYBRID_ENDPOINT + '/work?duration_ms=10');
  if (warmup.status !== 200) {
    console.log(`⚠️ Warning: Health check returned ${warmup.status}`);
  }
  
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
  
  // Make request to /work endpoint (or /fib?n=30 for CPU load)
  let endpoint = HYBRID_ENDPOINT + '/work?duration_ms=10';
  let response = http.get(endpoint);
  
  // Record response time
  let duration = response.timings.duration;
  response_time.add(duration);
  
  // Check for SLO violation (p99 > 200ms approximated by individual request)
  if (duration > SLO_THRESHOLD_MS) {
    slo_violations.add(1);
  }
  
  // Detect cold start (high latency > 5s typically indicates cold start)
  if (duration > 5000) {
    cold_start_detected.add(1);
  }
  
  // Standard checks
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response < 200ms (SLO)': (r) => r.timings.duration < SLO_THRESHOLD_MS,
    'response < 1s': (r) => r.timings.duration < 1000,
    'response < 5s (cold start)': (r) => r.timings.duration < 5000,
  });
  
  error_rate.add(response.status !== 200);
  
  // Minimal sleep for high RPS
  sleep(0.05);
}

export function teardown(data) {
  console.log('\n📊 Spike-with-Idle Test Results');
  console.log('================================');
  console.log(`Total duration: ${Math.round((Date.now() - data.startTime) / 1000)}s`);
  
  // Final health check
  let health = http.get(HYBRID_ENDPOINT + '/work?duration_ms=10');
  console.log(`\nPost-test health: ${health.status === 200 ? '✅ HEALTHY' : '❌ DEGRADED'}`);
  
  console.log('\n🔍 Analysis for H1/H2:');
  console.log('- Compare p99 during spike phases across scenarios (S1, S2, S3, S4)');
  console.log('- H1 validated if: S3/S4 p99 < S1/S2 p99 during spikes');
  console.log('- H2 validated if: S4 weight changes BEFORE Phase C starts');
  console.log('- Check routing daemon logs for predictive vs reactive decisions');
  
  console.log('\nPrometheus queries:');
  console.log('  p99: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[30s]))');
  console.log('  weights: routing_daemon_current_weight');
}
