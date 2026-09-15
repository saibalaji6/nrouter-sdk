import { nRouter } from '@nrouter_ai/sdk';

export interface SocialMediaOptions {
  apiKey?: string;
  topic: string;
  history?: string[];
}

export async function generateSocialMediaContent(options: SocialMediaOptions): Promise<string> {
  const client = new nRouter({
    apiKey: options.apiKey || process.env.NROUTER_API_KEY,
  });

  const historyContext = options.history && options.history.length > 0 
    ? `\n\nPreviously discussed topics (avoid repeating these exact angles):\n- ${options.history.join('\n- ')}` 
    : '';

  const response = await client.chat.completions.create({
    model: 'gemini-3.8-flash-high',
    messages: [
      {
        role: 'system',
        content: `You are the nRouter Social Media Content Generator.
Your goal is to draft viral social media posts (for X/Twitter, LinkedIn, etc.) about nRouter.
Keep the tone engaging, technical yet accessible. Use relevant hashtags like #AI #DevTools #nRouter.${historyContext}`
      },
      {
        role: 'user',
        content: options.topic
      }
    ],
  });

  return response.choices[0]?.message?.content || '';
}
