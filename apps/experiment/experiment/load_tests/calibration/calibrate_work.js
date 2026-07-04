import http from 'k6/http';
import { check } from 'k6';
import { Trend, Counter } from 'k6/metrics';

const TARGET_URL = __ENV.TARGET_URL || 'http://localhost:18082';
const WORK_MS = __ENV.WORK_MS || '5';
const TARGET_RPS = parseInt(__ENV.TARGET_RPS || '30');
const DURATION = __ENV.DURATION || '30s';

export const options = {
  scenarios: {
    constant_rate: {
      executor: 'constant-arrival-rate',
      rate: TARGET_RPS,
      timeUnit: '1s',
      duration: DURATION,
      preAllocatedVUs: TARGET_RPS * 2,
      maxVUs: TARGET_RPS * 5,
    },
  },
  thresholds: {
    http_req_duration: ['p(99)<200'],
  },
};

export default function () {
  const res = http.get(`${TARGET_URL}/work?duration_ms=${WORK_MS}`);
  check(res, {
    'status is 200': (r) => r.status === 200,
  });
}

export function handleSummary(data) {
  const dur = data.metrics.http_req_duration;
  const reqs = data.metrics.http_reqs;
  const fails = data.metrics.http_req_failed;
  
  const p50 = dur ? (dur.values['p(50)'] || dur.values.med || 0) : 0;
  const p90 = dur ? (dur.values['p(90)'] || 0) : 0;
  const p95 = dur ? (dur.values['p(95)'] || 0) : 0;
  const p99 = dur ? (dur.values['p(99)'] || 0) : 0;

  const summary = {
    target_rps: TARGET_RPS,
    work_ms: parseInt(WORK_MS),
    actual_rps: reqs ? reqs.values.rate : 0,
    total_requests: reqs ? reqs.values.count : 0,
    p50_ms: p50,
    p90_ms: p90,
    p95_ms: p95,
    p99_ms: p99,
    max_ms: dur ? dur.values.max : 0,
    avg_ms: dur ? dur.values.avg : 0,
    min_ms: dur ? dur.values.min : 0,
    error_rate: fails ? fails.values.rate : 0,
    slo_pass: p99 > 0 ? p99 < 200 : p95 < 200,
  };

  return {
    stdout: JSON.stringify(summary, null, 2) + '\n',
  };
}
