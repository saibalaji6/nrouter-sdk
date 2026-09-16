import { nRouter } from '@nrouter_ai/sdk';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export interface ImagePromptOptions {
  apiKey?: string;
  query: string;
}

export async function generateImagePrompt(options: ImagePromptOptions): Promise<string> {
  const client = new nRouter({ apiKey: options.apiKey || process.env.NROUTER_API_KEY });
  const _dirname = path.dirname(fileURLToPath(import.meta.url));

  const instructions = fs.readFileSync(path.join(_dirname, '../skills/instructions.md'), 'utf-8');
  const brand = fs.readFileSync(path.join(_dirname, '../skills/brand.md'), 'utf-8');

  const response = await client.nr.messages({
    model: process.env.NROUTER_MODEL || 'claude-haiku-4-5-20251001',
    system: instructions + '\n\n' + brand,
    messages: [{ role: 'user', content: options.query }],
    max_tokens: 1024,
  });

  const body = response.body as any;
  const textBlock = body.content?.find((c: any) => c.type === 'text');
  return textBlock ? textBlock.text : '';
}