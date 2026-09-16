import { test, expect } from '@playwright/test';

test('generates Image Prompt', async ({ page }) => {
  await page.goto('/');
  await page.fill('#queryInput', 'A banner for Rust Gateway');
  await page.click('#genBtn');
  
  // Wait for the output to populate with something
  await expect(page.locator('#output')).not.toBeEmpty({ timeout: 60000 });
  
  const text = await page.locator('#output').textContent();
  expect(text).toContain('#0F172A');
});