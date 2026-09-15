import { nRouter } from '@nrouter_ai/sdk';

export interface VideoPromptOptions {
  apiKey?: string;
  query: string;
  videoModel: string;
}

export async function generateVideoPrompt(options: VideoPromptOptions): Promise<string> {
  const client = new nRouter({
    apiKey: options.apiKey || process.env.NROUTER_API_KEY,
  });

  const response = await client.chat.completions.create({
    model: 'gemini-3.8-flash-high',
    messages: [
      {
        role: 'system',
        content: `You are the Video Prompt Generator.
Generate a highly optimized prompt tailored to the specified video model's strengths (${options.videoModel}). 
Include camera motion terms and lighting details suitable for this specific architecture.`
      },
      {
        role: 'user',
        content: options.query
      }
    ],
  });

  return response.choices[0]?.message?.content || '';
}
