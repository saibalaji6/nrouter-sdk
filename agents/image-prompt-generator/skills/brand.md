# nRouter Image Brand Specification (Authoritative Standard)
Source of Truth: nrouter-frontend-ui/image_prompt_final/STANDARD.md

## Surface Contract
- Master: 3840 × 2160 PNG (4K 16:9) or 3840 × 3840 PNG (1:1 Square)
- Delivery: 1600 × 900 JPEG under 500KB (Web/Blog) or 1200 × 630 PNG/JPEG (OG Card)

## Color Palette (Strict Rules)
- Obsidian: #0a0a0b (Matte black background for dark themes)
- Warm Ink: #211f1b
- Warm Paper: #fffefa (True/warm white for light themes)
- Mint: #90FCA6 (CRITICAL: Mint is an ACCENT ONLY, NEVER a flat background)
- Accents: Use ONE accent family per image. NEVER use generic purple AI gradients.

## Visual & Content Rules
- The generated foundation MUST be logo-free and text-free. Final typography and logos are composited deterministically.
- One focal visual, one clear reading direction, phone-readable hierarchy, generous negative space.
- Present nRouter STRICTLY as the secure LLM gateway/control layer, NEVER as an AI model.
- NEVER expose internal ports, credentials, database DSNs, or engine names.
- STRICT NEGATIVE PROMPTS: generic robot, brain graphic, glowing purple gradient, tangled connectors, random code snippets, fabricated UI charts, human stock photos, watermarks.