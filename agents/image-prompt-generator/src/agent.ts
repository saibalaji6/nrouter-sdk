import { nRouter } from '@nrouter_ai/sdk';

export interface ImagePromptOptions {
  apiKey?: string;
  query: string;
}

export async function generateImagePrompt(options: ImagePromptOptions): Promise<string> {
  const client = new nRouter({
    apiKey: options.apiKey || process.env.NROUTER_API_KEY,
  });

  const response = await client.chat.completions.create({
    model: 'gemini-3.8-flash-high',
    messages: [
      {
        role: 'system',
        content: `You are the nRouter Image Prompt Generator.
Your goal is to generate highly optimized prompts for image models based on user requests.
You MUST adhere to the nRouter image branding standard:
1. All images must align with the nRouter brand (clean, modern, technical).
2. Avoid generic corporate stock photos; prefer vector-style or abstract tech visualizations.
3. Use the nRouter color palette: primary #0F172A (navy), accents in vibrant blue and purple.
Output only the final prompt.`
      },
      {
        role: 'user',
        content: options.query
      }
    ],
  });

  return response.choices[0]?.message?.content || '';
}
