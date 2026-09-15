#!/usr/bin/env node
import crypto from 'node:crypto';
import { nRouter } from '../dist/index.mjs';

const mode = process.argv.includes('--weekly') ? 'weekly' : 'daily';
const limits = { daily: 1, weekly: 3 };
const maxCalls = limits[mode];
const allowed = new Set(
  (process.env.NROUTER_SCHEDULED_ENDPOINTS || 'chat,messages,responses,completions,embeddings')
    .split(',')
    .map((value) => value.trim())
    .filter(Boolean),
);
const paths = {
  chat: '/v1/chat/completions',
  messages: '/v1/messages',
  responses: '/v1/responses',
  completions: '/v1/completions',
  embeddings: '/v1/embeddings',
};

function fail(message) {
  console.error(`scheduled validation: ${message}`);
  process.exitCode = 1;
}

function requestId(error) {
  return error?.requestId ?? error?.request_id ??
    error?.headers?.get?.('x-nr-request-id') ??
    error?.response?.headers?.get?.('x-nr-request-id') ?? null;
}

function randomItem(items) {
  return items[crypto.randomInt(items.length)];
}

function requestBody(kind, model) {
  if (kind === 'chat' || kind === 'messages') {
    return { model, messages: [{ role: 'user', content: 'Scheduled SDK health check. Reply OK.' }], max_tokens: 8 };
  }
  if (kind === 'responses') return { model, input: 'Scheduled SDK health check. Reply OK.', max_output_tokens: 8 };
  if (kind === 'completions') return { model, prompt: 'Scheduled SDK health check. Reply OK.', max_tokens: 8 };
  return { model, input: 'scheduled sdk health check' };
}

if (!process.env.NROUTER_API_KEY) {
  fail('NROUTER_API_KEY repository secret is not configured');
} else {
  const client = new nRouter({
    apiKey: process.env.NROUTER_API_KEY,
    baseURL: process.env.NROUTER_BASE_URL || 'https://api.nrouter.ai/v1',
    maxRetries: 0,
    timeout: 30_000,
  });

  try {
    const catalogue = await client.nr.models.list();
    const candidates = [];
    for (const item of catalogue.data) {
      for (const [kind, path] of Object.entries(paths)) {
        if (allowed.has(kind) && item.nrouter_endpoints?.includes(path)) {
          candidates.push({ kind, path, model: item.id });
        }
      }
    }
    if (candidates.length === 0) {
      fail(`no advertised candidates for endpoints: ${[...allowed].join(', ')}`);
    } else {
      const remaining = [...candidates];
      const results = [];
      for (let attempt = 1; attempt <= maxCalls; attempt += 1) {
        const index = crypto.randomInt(remaining.length);
        const candidate = remaining.splice(index, 1)[0] || randomItem(candidates);
        const started = Date.now();
        try {
          const response = await client.nr.request(
            candidate.path.replace(/^\/v1/, ''),
            requestBody(candidate.kind, candidate.model),
          );
          const meta = client.nr.meta(response.headers);
          const result = {
            attempt,
            kind: candidate.kind,
            model: candidate.model,
            http: response.status,
            result: response.status >= 200 && response.status < 300 ? 'success' : 'failure',
            requestId: meta.requestId,
            costStatus: meta.costStatus,
            cost: meta.cost,
            latencyMs: Date.now() - started,
          };
          results.push(result);
          console.log(JSON.stringify(result));
        } catch (error) {
          const result = {
            attempt,
            kind: candidate.kind,
            model: candidate.model,
            http: error?.status ?? error?.response?.status ?? null,
            result: 'failure',
            requestId: requestId(error),
            errorClass: error?.name ?? 'Error',
            costStatus: error?.meta?.costStatus ?? null,
            cost: error?.meta?.cost ?? null,
            latencyMs: Date.now() - started,
          };
          results.push(result);
          console.log(JSON.stringify(result));
        }
      }
      const successes = results.filter((item) => item.result === 'success').length;
      console.log(JSON.stringify({ mode, catalogueModels: catalogue.data.length, candidateRoutes: candidates.length, attempted: results.length, successes, failures: results.length - successes, maxCalls }));
      if (successes === 0) process.exitCode = 1;
    }
  } catch (error) {
    fail(`catalogue request failed: ${error?.name ?? 'Error'}`);
  }
}
