import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Custom metrics
export let slo_violations = new Counter('slo_violations');
export let response_time = new Trend('response_time');
export let error_rate = new Rate('errors');

const TARGET_URL = __ENV.TARGET_URL || 'http://localhost:18082';
const FIB_N = __ENV.FIB_N || '30';  // n=30 ~10ms per request, saturates at 100+ concurrent
const SLO_THRESHOLD_MS = 200;

// Stress test designed to trigger SLO violations
// Uses CPU-intensive /fib endpoint to saturate K8s backend
export let options = {
  scenarios: {
    // Warmup: establish baseline
    warmup: {
      executor: 'constant-arrival-rate',
      rate: 10,
      timeUnit: '1s',
      duration: '20s',
      preAllocatedVUs: 20,
      maxVUs: 50,
      startTime: '0s',
      tags: { phase: 'warmup' },
    },
    // Spike: overwhelm K8s with CPU-intensive requests
    spike: {
      executor: 'constant-arrival-rate',
      rate: 100, // 100 RPS of CPU-intensive fib(35) requests
      timeUnit: '1s',
      duration: '60s',
      preAllocatedVUs: 200,
      maxVUs: 500,
      startTime: '20s',
      tags: { phase: 'spike' },
    },
    // Cooldown: observe recovery
    cooldown: {
      executor: 'constant-arrival-rate',
      rate: 20,
      timeUnit: '1s',
      duration: '30s',
      preAllocatedVUs: 30,
      maxVUs: 50,
      startTime: '80s',
      tags: { phase: 'cooldown' },
    },
  },
  thresholds: {
    'http_req_duration{phase:warmup}': ['p(99)<500'],
    'http_req_duration{phase:spike}': ['p(99)<5000'], // Expect high latency during spike
    'slo_violations': ['count>10'], // We WANT violations
  },
};

export function setup() {
  console.log('\n🔥 SLO Violation Stress Test');
  console.log('============================');
  console.log(`Target: ${TARGET_URL}`);
  console.log(`Endpoint: /fib?n=${FIB_N} (CPU-intensive, saturates at 100+ concurrent)`);
  console.log('Goal: Trigger SCALE_OUT decisions by exceeding SLO threshold');
  console.log('');
  console.log('Phase A (0-20s): Warmup @ 10 RPS');
  console.log('Phase B (20-80s): Spike @ 100 RPS (should saturate K8s)');
  console.log('Phase C (80-110s): Cooldown @ 20 RPS');
  console.log('');
  
  // Verify endpoint works
  let warmup = http.get(TARGET_URL + '/work?duration_ms=5');
  if (warmup.status !== 200) {
    console.log(`⚠️ Health check failed: ${warmup.status}`);
  }
  
  return { startTime: Date.now() };
}

export default function () {
  // Use CPU-intensive endpoint
  let endpoint = TARGET_URL + '/fib?n=' + FIB_N;
  let response = http.get(endpoint);
  
  let duration = response.timings.duration;
  response_time.add(duration);
  
  // Track SLO violations (p99 > 200ms)
  if (duration > SLO_THRESHOLD_MS) {
    slo_violations.add(1);
  }
  
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response < 200ms (SLO)': (r) => r.timings.duration < SLO_THRESHOLD_MS,
    'response < 1s': (r) => r.timings.duration < 1000,
    'response < 5s': (r) => r.timings.duration < 5000,
  });
  
  error_rate.add(response.status !== 200);
}

export function teardown(data) {
  console.log('\n📊 Stress Test Results');
  console.log('======================');
  console.log(`Duration: ${Math.round((Date.now() - data.startTime) / 1000)}s`);
  console.log('\n🔍 Check routing daemon logs for SCALE_OUT decisions');
  console.log('Expected: High p99 latency during spike triggers Algorithm 1 SCALE_OUT');
}
