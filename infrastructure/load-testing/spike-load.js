import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Custom metrics for spike load analysis
export let requests = new Counter('http_reqs');
export let k3s_responses = new Counter('k3s_responses');
export let knative_responses = new Counter('knative_responses');
export let error_rate = new Rate('errors');
export let response_time = new Trend('response_time');
export let spike_performance = new Trend('spike_response_time');

// Test configuration for traffic spike simulation
export let options = {
  stages: [
    { duration: '1m', target: 50 },   // Baseline: 50 RPS
    { duration: '30s', target: 200 }, // Spike: Ramp to 200 RPS
    { duration: '2m', target: 200 },  // Spike: Sustain 200 RPS
    { duration: '30s', target: 50 },  // Recovery: Back to 50 RPS
    { duration: '1m', target: 50 },   // Baseline: Sustain 50 RPS
    { duration: '30s', target: 0 },   // Ramp down
  ],
  thresholds: {
    // Sprint 1 spike load requirements
    'http_req_duration': ['p(95)<1000'], // 95th percentile < 1s during spike (relaxed)
    'http_req_duration{scenario:default}': ['p(99)<3000'], // 99th percentile < 3s (relaxed)
    'http_req_failed': ['rate<0.05'], // Error rate < 5% during spike
    'http_reqs': ['rate>=45'], // Minimum throughput maintained
  },
};

// Test endpoints
const HYBRID_ENDPOINT = 'http://localhost:18082';
const HAPROXY_STATS = 'http://localhost:18404/stats';

export default function () {
  // Test hybrid endpoint with spike load
  let hybridResponse = http.get(HYBRID_ENDPOINT);
  
  // Enhanced checks for spike conditions
  let isSpike = __VU > 50; // Consider high VU count as spike condition
  
  check(hybridResponse, {
    'status is 200': (r) => r.status === 200,
    'response time < 300ms': (r) => r.timings.duration < 300,
    'response time < 500ms during spike': (r) => !isSpike || r.timings.duration < 500,
    'no connection errors': (r) => r.status !== 0,
  });

  // Track backend distribution during spike
  if (hybridResponse.body && hybridResponse.body.includes('K3s Cluster')) {
    k3s_responses.add(1);
  } else if (hybridResponse.body && hybridResponse.body.includes('Knative Serverless')) {
    knative_responses.add(1);
  }

  // Record metrics with spike context
  response_time.add(hybridResponse.timings.duration);
  if (isSpike) {
    spike_performance.add(hybridResponse.timings.duration);
  }
  error_rate.add(hybridResponse.status !== 200);

  // Minimal sleep to allow high RPS
  sleep(0.1);
}

export function setup() {
  console.log('\n🚀 Starting Spike Load Test');
  console.log('===========================');
  console.log('Pattern: 50 → 200 → 50 RPS');
  console.log('Duration: ~6 minutes total');
  console.log('Target: Test system resilience under traffic spikes\n');
}

export function teardown(data) {
  console.log('\n📊 Spike Load Test Results:');
  console.log('===========================');
  
  // Allow time for system recovery
  sleep(5);
  
  // Check system health after spike
  let healthCheck = http.get(HYBRID_ENDPOINT);
  let statsCheck = http.get(HAPROXY_STATS);
  
  console.log('🔍 Post-spike health check:');
  if (healthCheck.status === 200) {
    console.log('✅ Hybrid endpoint: HEALTHY');
  } else {
    console.log('❌ Hybrid endpoint: DEGRADED');
  }
  
  if (statsCheck.status === 200) {
    console.log('✅ HAProxy stats: ACCESSIBLE');
  } else {
    console.log('❌ HAProxy stats: INACCESSIBLE');
  }
  
  console.log('\n📈 Spike test analysis:');
  console.log('- Check p95/p99 response times above');
  console.log('- Verify error rate stayed below 5%');
  console.log('- Review HAProxy stats for backend behavior');
  console.log('- Validate system recovered to baseline performance');
}
