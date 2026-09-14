# Sub-skill: Customer Support Agent (@nrouter_ai/support-agent)

Skill `nrouter-sdk`, sub-skill `support-agent`. Open it when developing, configuring, or testing the public `@nrouter_ai/support-agent` package located at `agents/customer-support-agent/`.

The customer support agent is a streaming, in-process assistant library built directly on `@nrouter_ai/sdk`. It provides document-grounded retrieval over static markdown docs or index files, cosine similarity search, tools, confidence scoring, citation generation, PII masking, and SSE streaming.

## Core Properties

1. **Zero Database Dependency**: All retrieval happens in-memory over pre-computed chunk embeddings (typically loaded from a static `kb.json` index), eliminating database, vector extension, and microservice dependencies.
2. **SDK Dogfooding**: The only runtime dependency is `@nrouter_ai/sdk` (`nRouter` universal client).
3. **SSE Streaming Contract**: `chatSSE(req, context)` returns an asynchronous `ReadableStream` emitting standard Server-Sent Event lines (`confidence`, `citations`, `token`, `cost`, `done`) matching the `AskNRouterWidget` UI contract.
4. **Offline by Default**: Like the rest of `nrouter-sdk`, all default unit and contract tests run completely offline with zero network, zero gateway, and zero credentials.

## Package Structure

```
agents/customer-support-agent/
├── bin/
│   └── support-agent.mjs       # CLI tool for building KB indices
├── src/
│   ├── agent.ts                # createSupportAgent factory & agent core
│   ├── build.ts                # buildKnowledgeIndex pipeline
│   ├── client.ts               # SDK wrapper
│   ├── node.ts                 # Node.js file system helpers (readDocsDir, saveKnowledgeIndex, loadKnowledgeIndex)
│   ├── pii.ts                  # PII redaction and masking
│   ├── retrieval.ts            # Cosine similarity ranking
│   ├── sse.ts                  # SSE stream formatter
│   └── types.ts                # Request, response, and config types
├── test/                       # 24 test suites (offline)
└── package.json
```

## CLI Usage: Building Knowledge Base Index

```bash
npx @nrouter_ai/support-agent build-kb \
  --docs <docs-directory> \
  --base-url <nrouter-gateway-v1-url> \
  --api-key <nrouter-key> \
  --embedding-model text-embedding-3-small \
  --dimensions 768 \
  --out kb.json
```

## Host Application Integration

Any Node.js/Next.js/Express server imports `@nrouter_ai/support-agent` in-process:

```typescript
import { createSupportAgent } from '@nrouter_ai/support-agent';
import { loadKnowledgeIndex } from '@nrouter_ai/support-agent/node';

const knowledge = await loadKnowledgeIndex('./data/support-agent-kb.json');
const agent = createSupportAgent({
  apiKey: process.env.NROUTER_SUPPORT_AGENT_KEY,
  baseURL: 'http://127.0.0.1:4000/v1',
  model: 'claude-haiku-4-5-20251001',
  knowledge,
  maskPii: true,
});

const sseStream = agent.chatSSE(
  { messages: [{ role: 'user', content: 'How do I create a virtual key?' }] },
  { audiences: ['public'] }
);
```

## Test Commands

Run from `agents/customer-support-agent/`:

```bash
pnpm test          # vitest run (24 test suites, 236 offline tests)
pnpm typecheck     # tsc --noEmit
pnpm build         # compiles to dist/
```

## Cross-Repo Wiring & Health Verification

- Host route: `nrouter-app` at `/api/public/ask`
- Frontend UI: `nrouter-frontend-ui` (`AskNRouterWidget`, `AskAiGuruFab`)
- Operational Skill: `nrouter-customer-support-widget` in `nrouter-app`
- Live E2E Health Check: `bash nrouter-app/skills/nrouter-customer-support-widget/scripts/verify-widget-e2e.sh`
