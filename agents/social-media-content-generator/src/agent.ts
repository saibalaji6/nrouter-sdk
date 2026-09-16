import { nRouter } from '@nrouter_ai/sdk';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export interface SocialMediaOptions {
  apiKey?: string;
  topic: string;
  history: string[];
}

export async function generateSocialMediaContent(options: SocialMediaOptions): Promise<string> {
  const client = new nRouter({ apiKey: options.apiKey || process.env.NROUTER_API_KEY });
  const _dirname = path.dirname(fileURLToPath(import.meta.url));

  const instructions = fs.readFileSync(path.join(_dirname, '../skills/instructions.md'), 'utf-8');
  const brand = fs.readFileSync(path.join(_dirname, '../skills/brand.md'), 'utf-8');

  const response = await client.nr.messages({
    model: process.env.NROUTER_MODEL || 'claude-haiku-4-5-20251001',
    system: instructions + '\n\n' + brand + '\n\nHistory context: ' + options.history.join(', '),
    messages: [{ role: 'user', content: options.topic }],
    max_tokens: 1024,
  });

  const body = response.body as any;
  const textBlock = body.content?.find((c: any) => c.type === 'text');
  return textBlock ? textBlock.text : '';
}