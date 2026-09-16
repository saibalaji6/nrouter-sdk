# nRouter Video Prompt Generator SDK

This package exposes `generateVideoPrompt(options)`, an SDK utility that generates highly optimized prompts for video generation models.

## Brand & Skill Integration

**How Video Skills are Incorporated:**
Video generation models (like Google Veo, Luma Dream Machine, Sora) require explicit camera linguistics and lighting physics to produce coherent generations. The agent is explicitly instructed to adapt the prompt to the selected `videoModel`'s strengths, automatically appending specific cinematic terms (e.g., "dolly-in", "volumetric light") to ensure the generated video aligns with high-end tech commercial standards.

## Local Playwright Testing

To run the Playwright end-to-end test suite:
```bash
NROUTER_API_KEY="sk-nrouter-..." npm run test:e2e
```


## 🛠️ How to Tweak Skills & Agent Memory

This agent is powered by a configurable "Skills & Memory" markdown file, rather than hardcoded logic. This allows design and content teams to update the agent's behavior without modifying the TypeScript codebase.

1. **Locate the Skills File**: Open `skills/instructions.md`.
2. **Tweak the Guidelines**: Modify the brand colors, tone of voice, visual aesthetics, or negative prompts directly in the markdown.
3. **Deploy as a Package**: Because the `skills/` directory is explicitly whitelisted in the `package.json` `"files"` array, any changes you make to `instructions.md` will be automatically bundled when you run `npm publish`.

When installed externally via NPM, the agent will dynamically read from its packaged `skills/instructions.md` file at runtime!
