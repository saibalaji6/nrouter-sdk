import { generateImagePrompt } from './image-prompt-generator/dist/agent.js';
import { generateVideoPrompt } from './video-prompt-generator/dist/agent.js';
import { generateSocialMediaContent } from './social-media-content-generator/dist/agent.js';
import path from 'path';


async function runTests() {
  console.log("=== Testing Image Prompt Generator ===");
  try {
    const imagePrompt = await generateImagePrompt({
      query: "A banner for our new Rust Gateway release"
    });
    console.log("Result:\n", imagePrompt, "\n");
  } catch (e) {
    console.error("Failed:", e);
  }

  console.log("=== Testing Video Prompt Generator ===");
  try {
    const videoPrompt = await generateVideoPrompt({
      query: "A cinematic introduction of the nRouter dashboard",
      videoModel: "Google Veo"
    });
    console.log("Result:\n", videoPrompt, "\n");
  } catch (e) {
    console.error("Failed:", e);
  }

  console.log("=== Testing Social Media Content Generator ===");
  try {
    const socialPost = await generateSocialMediaContent({
      topic: "Announcing zero-latency model fallbacks",
      history: ["Gateway 3.1 Launch"]
    });
    console.log("Result:\n", socialPost, "\n");
  } catch (e) {
    console.error("Failed:", e);
  }
}

runTests();
