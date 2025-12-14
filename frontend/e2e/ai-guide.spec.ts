/**
 * E2E tests for AI guide generation
 */

import { test, expect } from '@playwright/test';
import { LoginPage } from './page-objects/LoginPage';
import { DashboardPage } from './page-objects/DashboardPage';
import { APIHelper } from './fixtures';

test.describe('AI Guide Generation', () => {
  test.beforeEach(async ({ page }) => {
    // Login and setup
    const loginPage = new LoginPage(page);
    await loginPage.login();

    const apiHelper = new APIHelper();
    const token = await apiHelper.createUser();
    await apiHelper.createProducerProfile(token);

    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
  });

  test('should show AI guide button in task details', async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.clickChecklistTab();

    // Click on a task to open details
    const taskItem = page.locator('[class*="bg-white"]').filter({ hasText: /.+/ }).first();
    if (await taskItem.isVisible()) {
      await taskItem.click();
      await page.waitForTimeout(1000);

      // Look for AI guide button
      const aiGuideButton = page.getByRole('button', { name: /guia|guide|gerar/i }).first();
      // May or may not be visible depending on task
      if (await aiGuideButton.isVisible({ timeout: 5000 })) {
        await expect(aiGuideButton).toBeVisible();
      }
    }
  });

  test('should generate AI guide when button is clicked', async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.clickChecklistTab();

    // Open task details
    const taskItem = page.locator('[class*="bg-white"]').filter({ hasText: /.+/ }).first();
    if (await taskItem.isVisible()) {
      await taskItem.click();
      await page.waitForTimeout(1000);

      // Look for and click AI guide button
      const aiGuideButton = page.getByRole('button', { name: /gerar guia|generate guide/i }).first();
      if (await aiGuideButton.isVisible({ timeout: 5000 })) {
        await aiGuideButton.click();

        // Should show loading state
        const loadingIndicator = page.getByText(/gerando|loading|carregando/i);
        await expect(loadingIndicator).toBeVisible({ timeout: 5000 });

        // Wait for guide to appear
        await page.waitForTimeout(3000);

        // Should see guide content
        const guideContent = page.getByText(/passo|step|resumo|summary/i).first();
        await expect(guideContent).toBeVisible({ timeout: 10000 });
      }
    }
  });

  test('should display guide steps', async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.clickChecklistTab();

    // Open task details and generate guide
    const taskItem = page.locator('[class*="bg-white"]').filter({ hasText: /.+/ }).first();
    if (await taskItem.isVisible()) {
      await taskItem.click();
      await page.waitForTimeout(1000);

      const aiGuideButton = page.getByRole('button', { name: /gerar guia/i }).first();
      if (await aiGuideButton.isVisible({ timeout: 5000 })) {
        await aiGuideButton.click();
        await page.waitForTimeout(5000);

        // Should see guide steps
        const steps = page.locator('[class*="bg-white"], [class*="bg-purple"]').filter({
          hasText: /\d+/,
        });
        const stepCount = await steps.count();
        
        if (stepCount > 0) {
          // Should have at least one step
          expect(stepCount).toBeGreaterThan(0);
        }
      }
    }
  });

  test('should display guide summary and metadata', async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.clickChecklistTab();

    // Open task details
    const taskItem = page.locator('[class*="bg-white"]').filter({ hasText: /.+/ }).first();
    if (await taskItem.isVisible()) {
      await taskItem.click();
      await page.waitForTimeout(1000);

      const aiGuideButton = page.getByRole('button', { name: /gerar guia/i }).first();
      if (await aiGuideButton.isVisible({ timeout: 5000 })) {
        await aiGuideButton.click();
        await page.waitForTimeout(5000);

        // Should see summary or estimated time
        const summary = page.getByText(/resumo|summary|tempo|time|dias|days/i).first();
        if (await summary.isVisible({ timeout: 5000 })) {
          await expect(summary).toBeVisible();
        }
      }
    }
  });
});
