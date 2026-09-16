const fs = require('fs');
const path = require('path');

const agents = ['image-prompt-generator', 'video-prompt-generator', 'social-media-content-generator'];

// ==========================================
// ITERATION 10: ENTERPRISE-GRADE REFINEMENTS
// ==========================================

const imgBrand = `
# nRouter Enterprise Brand Identity (Iteration 10)

## 1. Enterprise Color Palette
- **Primary/Background:** Deep Navy (\`#0F172A\`) — conveys security, trust, and enterprise-grade infrastructure.
- **Accents:** Electric Blue (\`#3B82F6\`) and Neon Violet (\`#8B5CF6\`) — conveys modern speed, AI capabilities, and data flow.
- **Highlights:** Soft Cyan glow — used exclusively for active node connections and critical UI focal points.

## 2. Visual Aesthetic & Fidelity
- **Quality Specs:** 4K/8K resolution, ultra-crisp edges, high contrast, perfect geometric symmetry, 32k UHD rendering.
- **Style Constraints:** Premium Enterprise SaaS aesthetic. Flat vector art, isometric 3D topologies, or subtle glassmorphism (frosted glass overlays).
- **Core Motifs:** Interconnected network gateways, glowing fiber-optic data streams, minimalist circuit-board traces, abstract representations of Rust-lang gear logic.

## 3. Strict Negative Prompting
- **EXCLUDE:** Photorealism, human faces, generic corporate handshakes, messy chaotic data arrays, low-poly, text, watermarks, grainy artifacts, cluttered compositions.
`.trim();

const vidBrand = `
# nRouter Cinematic Enterprise Identity (Iteration 10)

## 1. Cinematic Environment & Lighting
- **Fidelity:** 8K resolution, hyper-realistic 3D rendering, Unreal Engine 5 level detail, path-traced global illumination.
- **Setting:** A premium, dimly lit, minimalist tech operations center or abstract void. 
- **Lighting Physics:** Volumetric light rays spilling from glowing monitors, soft cyan rim lighting separating subjects from deep matte-black backgrounds. 
- **Color Grade:** High-end cinematic LUT, cool teal-and-orange contrast, deep crushed blacks, perfectly balanced exposure.

## 2. Enterprise Interface Motion
- **Dashboard UI:** Sleek dark-mode analytics, microscopic pixel-perfect text, glowing real-time traffic graphs, pulsing global node maps.
- **Motion:** Smooth, weighted, heavy camera physics. No jitter.
`.trim();

const socBrand = `
# nRouter Enterprise Thought Leadership (Iteration 10)

## 1. Brand Voice & Tone
- **Persona:** A pragmatic, highly experienced VP of Engineering / CTO.
- **Tone:** Authoritative, insightful, data-driven, and slightly witty but deeply professional. 
- **Language:** Avoid fluffy marketing speak. Use precise engineering terminology (e.g., "p99 latency", "failover routing", "idempotent retry loops").

## 2. Core Pillars & Value Propositions
- **Zero-Latency Fallbacks:** "Enterprise reliability isn't a retry loop. It's instant, zero-latency provider rerouting."
- **Rust Gateway:** "Memory safety meets bare-metal speed. We process 10k RPM on a fraction of the compute."
- **FinOps & Observability:** "You can't manage what you don't measure. Granular LLM spend visibility."

## 3. Formatting
- Use structured line breaks. Bullet points for readability. 
- Professional hashtags: #EnterpriseArchitecture, #LLMOps, #RustLang, #nRouter
`.trim();

const videoModels = {
  'google-veo': `## Google Veo Prompt Architecture
1. **Subject Description:** Start with a macro description of the nRouter interface.
2. **Lighting:** Explicitly demand "motivated volumetric lighting" and "atmospheric dust particles" to leverage Veo's realistic physics engine.
3. **Camera Linguistics:** Use strict industry terms: "Slow dolly-in on a 50mm anamorphic lens," "rack focus from foreground nodes to background charts."`,
  
  'sora': `## OpenAI Sora Prompt Architecture
1. **Temporal Evolution:** Describe how the scene changes over a 10-second continuous take. Sora excels at maintaining state. 
2. **Fluid Dynamics:** "Data flows like glowing fluid through the network pipes."
3. **Complex Tracking:** "The camera executes an unbroken macroscopic tracking shot along a fiber-optic cable, emerging into a wide shot of the glowing nRouter dashboard."`,
  
  'runway-gen3': `## Runway Gen-3 Prompt Architecture
1. **Textural Fidelity:** Emphasize material properties. "Matte brushed aluminum bezels," "glossy glassmorphic UI cards," "subtle fingerprints on a glowing screen."
2. **Speed & Transitions:** "A sudden whip-pan that speed-ramps into a slow-motion push-in." Gen-3 excels at dynamic, commercial-style pacing.`,

  'luma-dream-machine': `## Luma Dream Machine Prompt Architecture
1. **Sprawling Environments:** "A sweeping drone-style orbital shot around a glowing 3D map of the globe, interconnected by laser-thin cyan data routes."
2. **Vibrant Contrast:** Emphasize extreme dynamic range and highly saturated neon accents against pitch black.`
};

// Update Image
const imgDir = path.join(__dirname, 'image-prompt-generator');
fs.writeFileSync(path.join(imgDir, 'skills', 'brand.md'), imgBrand);
fs.writeFileSync(path.join(imgDir, 'skills', 'instructions.md'), 'You are the elite nRouter Enterprise Image Prompt Generator.\nSynthesize the brand rules into a comma-separated prompt formatted for high-end diffusion models (Midjourney v6 style). Always append technical keywords like: 4K, 8K, highly detailed, Unreal Engine 5 render, cinematic lighting.');

// Update Video
const vidDir = path.join(__dirname, 'video-prompt-generator');
fs.writeFileSync(path.join(vidDir, 'skills', 'brand.md'), vidBrand);
fs.writeFileSync(path.join(vidDir, 'skills', 'instructions.md'), 'You are the elite nRouter Cinematic Video Prompt Generator.\nSynthesize the enterprise brand identity and the specific camera physics of the target video model into a highly professional, commercial-grade video prompt. Focus on ultra-high fidelity (8K, ARRI Alexa) and smooth professional cinematography.');
Object.keys(videoModels).forEach(model => {
  fs.writeFileSync(path.join(vidDir, 'skills', 'models', model + '.md'), videoModels[model]);
});

// Update Social
const socDir = path.join(__dirname, 'social-media-content-generator');
fs.writeFileSync(path.join(socDir, 'skills', 'brand.md'), socBrand);
fs.writeFileSync(path.join(socDir, 'skills', 'instructions.md'), 'You are the elite nRouter Enterprise Social Media Generator.\nDraft high-converting, thought-leadership posts aimed at CTOs and Lead Engineers. Ensure every post passes the "No Fluff" test—it must provide immediate architectural insight or quantifiable value.');

