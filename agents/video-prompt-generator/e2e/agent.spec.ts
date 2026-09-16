import { test, expect } from '@playwright/test';

test('generates Video Prompt', async ({ page }) => {
  await page.goto('/');
  await page.fill('#queryInput', 'Cinematic dashboard intro');
  await page.click('#genBtn');
  
  // Wait for the output to populate with something
  await expect(page.locator('#output')).not.toBeEmpty({ timeout: 60000 });
  
  const text = await page.locator('#output').textContent();
  expect(text).toContain('camera');
});