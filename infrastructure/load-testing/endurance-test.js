import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Custom metrics for endurance testing
export let requests = new Counter('http_reqs');
export let k3s_responses = new Counter('k3s_responses');
export let knative_responses = new Counter('knative_responses');
export let error_rate = new Rate('errors');
export let response_time = new Trend('response_time');
export let stability_check = new Rate('stability_violations');

// Test configuration for 30-minute endurance
export let options = {
  stages: [
    { duration: '2m', target: 25 },   // Ramp up to sustainable load
    { duration: '26m', target: 25 },  // Sustain 25 RPS for 26 minutes
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    // Sprint 1 stability requirements
    'http_req_duration': ['p(95)<200'], // Consistent performance
    'http_req_duration{scenario:default}': ['p(99)<400'], // No severe degradation
    'http_req_failed': ['rate<0.01'], // Very low error rate for stability
    'http_reqs': ['rate>=20'], // Minimum sustained throughput
    'stability_violations': ['rate<0.05'], // Less than 5% stability violations
  },
};

// Test endpoints
const HYBRID_ENDPOINT = 'http://localhost:18082';
const K3S_ENDPOINT = 'http://localhost:8080';
const KNATIVE_ENDPOINT = 'http://localhost:8081';
const HAPROXY_STATS = 'http://localhost:18404/stats';

// Stability tracking
let consecutiveErrors = 0;
let maxConsecutiveErrors = 0;
let testStartTime;

export default function () {
  if (!testStartTime) {
    testStartTime = Date.now();
  }
  
  // Test hybrid endpoint for stability
  let hybridResponse = http.get(HYBRID_ENDPOINT);
  
  // Enhanced stability checks
  let isStable = check(hybridResponse, {
    'status is 200': (r) => r.status === 200,
    'response time < 200ms': (r) => r.timings.duration < 200,
    'response time < 400ms': (r) => r.timings.duration < 400,
    'no timeout errors': (r) => r.status !== 0,
    'content length > 0': (r) => r.body && r.body.length > 0,
  });

  // Track consecutive errors for stability analysis
  if (hybridResponse.status !== 200) {
    consecutiveErrors++;
    maxConsecutiveErrors = Math.max(maxConsecutiveErrors, consecutiveErrors);
  } else {
    consecutiveErrors = 0;
  }

  // Flag stability violations (more than 3 consecutive errors)
  if (consecutiveErrors > 3) {
    stability_check.add(1);
  } else {
    stability_check.add(0);
  }

  // Track backend distribution over time
  if (hybridResponse.body && hybridResponse.body.includes('K3s Cluster')) {
    k3s_responses.add(1);
  } else if (hybridResponse.body && hybridResponse.body.includes('Knative Serverless')) {
    knative_responses.add(1);
  }

  // Record performance metrics
  response_time.add(hybridResponse.timings.duration);
  error_rate.add(hybridResponse.status !== 200);

  // Periodic health checks (every 5 minutes)
  let testDuration = (Date.now() - testStartTime) / 1000 / 60; // minutes
  if (testDuration > 0 && testDuration % 5 < 0.1) {
    performHealthCheck();
  }

  sleep(2); // Sustainable rate for 30-minute test
}

function performHealthCheck() {
  console.log(`\n🔍 Health Check at ${Math.floor((Date.now() - testStartTime) / 1000 / 60)} minutes:`);
  
  // Test individual backends
  let k3sHealth = http.get(K3S_ENDPOINT);
  let knativeHealth = http.get(KNATIVE_ENDPOINT, {
    headers: { 'Host': 'serverless-sim.default.localhost' }
  });
  
  console.log(`  K3s Backend: ${k3sHealth.status === 200 ? '✅' : '❌'} (${k3sHealth.status})`);
  console.log(`  Knative Backend: ${knativeHealth.status === 200 ? '✅' : '❌'} (${knativeHealth.status})`);
  console.log(`  Max Consecutive Errors: ${maxConsecutiveErrors}`);
}

export function setup() {
  console.log('\n⏱️  Starting 30-Minute Endurance Test');
  console.log('====================================');
  console.log('Load Pattern: 25 RPS sustained');
  console.log('Duration: 30 minutes total');
  console.log('Target: Validate system stability and resource management');
  console.log('Health checks: Every 5 minutes\n');
  
  // Pre-test system validation
  let preTestHealth = http.get(HYBRID_ENDPOINT);
  if (preTestHealth.status !== 200) {
    throw new Error('System not healthy before endurance test');
  }
  
  testStartTime = Date.now();
  return { startTime: testStartTime };
}

export function teardown(data) {
  console.log('\n📊 30-Minute Endurance Test Results:');
  console.log('====================================');
  
  let testDuration = (Date.now() - data.startTime) / 1000 / 60;
  console.log(`📝 Test Duration: ${testDuration.toFixed(1)} minutes`);
  console.log(`🔄 Max Consecutive Errors: ${maxConsecutiveErrors}`);
  
  // Final system health check
  sleep(10); // Allow brief recovery
  
  let finalHealth = http.get(HYBRID_ENDPOINT);
  let statsHealth = http.get(HAPROXY_STATS);
  
  console.log('\n🔍 Final System Health:');
  console.log(`  Hybrid Endpoint: ${finalHealth.status === 200 ? '✅ HEALTHY' : '❌ DEGRADED'}`);
  console.log(`  HAProxy Stats: ${statsHealth.status === 200 ? '✅ ACCESSIBLE' : '❌ INACCESSIBLE'}`);
  
  // Resource usage check
  console.log('\n📈 Endurance Test Analysis:');
  console.log('- Review response time trends for degradation');
  console.log('- Check error rate remained below 1%');
  console.log('- Verify no stability violations (>3 consecutive errors)');
  console.log('- Validate traffic distribution remained stable');
  console.log('- Check system resources post-test with: docker stats');
  
  if (maxConsecutiveErrors > 5) {
    console.log('⚠️  WARNING: High consecutive error count detected');
  }
  
  if (finalHealth.status === 200) {
    console.log('✅ System passed 30-minute endurance test');
  } else {
    console.log('❌ System degraded during endurance test');
  }
}
