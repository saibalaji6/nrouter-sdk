# nRouter Social Media Content Generator SDK

This package exposes `generateSocialMediaContent(options)`, an SDK utility that drafts viral social media posts for nRouter.

## Brand & Skill Integration

**How Brand Tone is Incorporated:**
The nRouter social presence requires a specific tone: punchy, technical, yet accessible. The agent's system prompt ensures that the generated content avoids overly dense corporate jargon in favor of a "developer-friendly" voice. It dynamically adapts to previously discussed history so that angles aren't repeated.

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
