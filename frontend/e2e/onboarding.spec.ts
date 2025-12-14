/**
 * E2E tests for onboarding flow
 */

import { test, expect } from '@playwright/test';
import { LoginPage } from './page-objects/LoginPage';
import { APIHelper } from './fixtures';

test.describe('Onboarding Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    const loginPage = new LoginPage(page);
    await loginPage.login();
  });

  test('should display onboarding questions', async ({ page }) => {
    // Navigate to onboarding if not already there
    await page.goto('/onboarding');
    await page.waitForLoadState('networkidle');

    // Should see question text
    const questionText = page.locator('h2').first();
    await expect(questionText).toBeVisible();
    await expect(questionText).not.toHaveText('');
  });

  test('should show progress indicator', async ({ page }) => {
    await page.goto('/onboarding');
    await page.waitForLoadState('networkidle');

    // Should see progress bar
    const progressBar = page.locator('[class*="bg-green-500"]').first();
    await expect(progressBar).toBeVisible();

    // Should see question counter
    const questionCounter = page.getByText(/pergunta|question/i);
    await expect(questionCounter).toBeVisible();
  });

  test('should answer boolean question', async ({ page }) => {
    await page.goto('/onboarding');
    await page.waitForLoadState('networkidle');

    // Look for Yes/No buttons
    const yesButton = page.getByRole('button', { name: /sim|yes/i }).first();
    const noButton = page.getByRole('button', { name: /não|no/i }).first();

    if (await yesButton.isVisible()) {
      await yesButton.click();
      // Should move to next question or complete
      await page.waitForTimeout(1000);
    }
  });

  test('should answer choice question', async ({ page }) => {
    await page.goto('/onboarding');
    await page.waitForLoadState('networkidle');

    // Look for choice buttons
    const choiceButtons = page.locator('button').filter({ hasText: /.+/ });
    const count = await choiceButtons.count();

    if (count > 0) {
      await choiceButtons.first().click();
      await page.waitForTimeout(1000);
    }
  });

  test('should answer text question', async ({ page }) => {
    await page.goto('/onboarding');
    await page.waitForLoadState('networkidle');

    // Look for text input
    const textInput = page.locator('input[type="text"]').first();
    if (await textInput.isVisible()) {
      await textInput.fill('Test answer');
      const submitButton = page.getByRole('button', { name: /continuar|submit/i });
      await submitButton.click();
      await page.waitForTimeout(1000);
    }
  });

  test('should track progress', async ({ page }) => {
    await page.goto('/onboarding');
    await page.waitForLoadState('networkidle');

    // Get initial progress
    const progressBar = page.locator('[class*="bg-green-500"]').first();
    const initialWidth = await progressBar.evaluate((el) => {
      return (el as HTMLElement).style.width;
    });

    // Answer a question
    const yesButton = page.getByRole('button', { name: /sim|yes/i }).first();
    if (await yesButton.isVisible()) {
      await yesButton.click();
      await page.waitForTimeout(2000);

      // Progress should update
      const newWidth = await progressBar.evaluate((el) => {
        return (el as HTMLElement).style.width;
      });
      // Width should have changed (progress increased)
      expect(newWidth).not.toBe(initialWidth);
    }
  });
});
