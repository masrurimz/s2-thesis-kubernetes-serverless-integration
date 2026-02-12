import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Custom metrics for hybrid system analysis
export let requests = new Counter('http_reqs');
export let k3s_responses = new Counter('k3s_responses');
export let knative_responses = new Counter('knative_responses');
export let error_rate = new Rate('errors');
export let response_time = new Trend('response_time');

// Test configuration for steady load
export let options = {
  stages: [
    { duration: '30s', target: 50 }, // Ramp up to 50 RPS
    { duration: '2m', target: 50 },  // Stay at 50 RPS for 2 minutes
    { duration: '30s', target: 0 },  // Ramp down
  ],
  thresholds: {
    // Sprint 1 performance requirements
    'http_req_duration': ['p(95)<500'], // 95th percentile < 500ms (relaxed for cold-starts)
    'http_req_duration{scenario:default}': ['p(99)<2000'], // 99th percentile < 2s (relaxed for cold-starts)
    'http_req_failed': ['rate<0.02'], // Error rate < 2%
    'http_reqs': ['rate>=45'], // At least 45 RPS sustained
  },
};

// Test endpoints - use environment variables for flexibility
const HYBRID_ENDPOINT = __ENV.TARGET_URL || 'http://localhost:18082';
const HAPROXY_STATS = __ENV.HAPROXY_STATS_URL || 'http://localhost:18404/stats';

export default function () {
  // Test hybrid endpoint (primary test) - use /health endpoint
  let hybridResponse = http.get(HYBRID_ENDPOINT + '/health');
  
  // Record metrics
  check(hybridResponse, {
    'status is 200': (r) => r.status === 200,
    'response time < 150ms': (r) => r.timings.duration < 150,
    'response time < 300ms': (r) => r.timings.duration < 300,
  });

  // Determine which backend served the request
  if (hybridResponse.body && hybridResponse.body.includes('K3s Cluster')) {
    k3s_responses.add(1);
  } else if (hybridResponse.body && hybridResponse.body.includes('Knative Serverless')) {
    knative_responses.add(1);
  }

  // Record response time and errors
  response_time.add(hybridResponse.timings.duration);
  error_rate.add(hybridResponse.status !== 200);

  // Sleep to maintain steady rate
  sleep(0.5);
}

export function teardown(data) {
  console.log('\n📊 Steady Load Test Results:');
  console.log('============================');
  
  // Performance summary will be shown by k6 automatically
  console.log('✅ Test completed successfully');
  console.log('📈 Check metrics above for performance analysis');
  console.log('🔍 Traffic distribution analysis available in HAProxy stats');
}
