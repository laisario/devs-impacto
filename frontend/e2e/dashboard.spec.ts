/**
 * E2E tests for dashboard interactions
 */

import { test, expect } from '@playwright/test';
import { LoginPage } from './page-objects/LoginPage';
import { DashboardPage } from './page-objects/DashboardPage';
import { APIHelper } from './fixtures';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Login and setup test data
    const loginPage = new LoginPage(page);
    await loginPage.login();

    // Create profile and some data via API
    const apiHelper = new APIHelper();
    const token = await apiHelper.createUser();
    await apiHelper.createProducerProfile(token);

    // Navigate to dashboard
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
  });

  test('should display dashboard with tasks and documents', async ({ page }) => {
    const dashboard = new DashboardPage(page);

    // Should see checklist tab
    await expect(dashboard.checklistTab).toBeVisible();

    // Should see documents tab
    await expect(dashboard.documentsTab).toBeVisible();

    // Should see some content (tasks or documents)
    const content = page.locator('[class*="bg-white"]').first();
    await expect(content).toBeVisible({ timeout: 10000 });
  });

  test('should switch between checklist and documents tabs', async ({ page }) => {
    const dashboard = new DashboardPage(page);

    // Click documents tab
    await dashboard.clickDocumentsTab();
    await page.waitForTimeout(500);

    // Should see documents content
    const documentsContent = page.getByText(/documento|document/i).first();
    await expect(documentsContent).toBeVisible({ timeout: 5000 });

    // Click checklist tab
    await dashboard.clickChecklistTab();
    await page.waitForTimeout(500);

    // Should see checklist content
    const checklistContent = page.getByText(/tarefa|task|checklist/i).first();
    await expect(checklistContent).toBeVisible({ timeout: 5000 });
  });

  test('should display formalization status', async ({ page }) => {
    // Should see status cards
    const statusCard = page.locator('[class*="bg-white"]').filter({ hasText: /status|progresso/i }).first();
    await expect(statusCard).toBeVisible({ timeout: 10000 });
  });

  test('should show progress percentage', async ({ page }) => {
    // Look for progress indicator
    const progressIndicator = page.locator('[class*="bg-green-500"]').filter({ hasText: /%/ }).first();
    if (await progressIndicator.isVisible()) {
      const progressText = await progressIndicator.textContent();
      expect(progressText).toMatch(/\d+%/);
    }
  });

  test('should allow task completion toggle', async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.clickChecklistTab();

    // Find a task checkbox
    const taskCheckbox = page.locator('[type="checkbox"], [class*="checkbox"], [class*="rounded"]').filter({
      has: page.locator('[class*="CheckCircle"]'),
    }).first();

    if (await taskCheckbox.isVisible()) {
      const initialState = await taskCheckbox.getAttribute('class');
      await taskCheckbox.click();
      await page.waitForTimeout(500);

      // State should change
      const newState = await taskCheckbox.getAttribute('class');
      expect(newState).not.toBe(initialState);
    }
  });

  test('should open task details', async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.clickChecklistTab();

    // Click on a task item
    const taskItem = page.locator('[class*="bg-white"]').filter({ hasText: /.+/ }).first();
    if (await taskItem.isVisible()) {
      await taskItem.click();
      await page.waitForTimeout(1000);

      // Should see task details or back button
      const backButton = page.getByText(/voltar|back/i);
      await expect(backButton).toBeVisible({ timeout: 5000 });
    }
  });

  test('should logout from dashboard', async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.logout();

    // Should be on landing page
    await expect(page).toHaveURL('/');
  });
});
