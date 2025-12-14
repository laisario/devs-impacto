/**
 * E2E tests for authentication flow
 */

import { test, expect } from '@playwright/test';
import { LoginPage } from './page-objects/LoginPage';

test.describe('Authentication Flow', () => {
  test('should complete phone OTP login', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();

    // Enter phone number
    await loginPage.enterPhone('+5511999999999');
    await loginPage.clickContinue();

    // Wait for OTP step
    await expect(page.getByText(/código|verificação/i)).toBeVisible();

    // Enter OTP
    await loginPage.enterOTP('123456');
    await loginPage.clickVerify();

    // Should redirect to dashboard or onboarding
    await expect(page).toHaveURL(/dashboard|onboarding/, { timeout: 10000 });
  });

  test('should show error for invalid phone format', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();

    // Try invalid phone
    await loginPage.enterPhone('123');
    await loginPage.clickContinue();

    // Should show error
    await expect(page.getByText(/erro|inválido|válido/i)).toBeVisible({ timeout: 5000 });
  });

  test('should show error for wrong OTP', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();

    // Enter phone and continue
    await loginPage.enterPhone('+5511999999999');
    await loginPage.clickContinue();

    // Enter wrong OTP
    await loginPage.enterOTP('000000');
    await loginPage.clickVerify();

    // Should show error
    await expect(page.getByText(/erro|código inválido|inválido/i)).toBeVisible({ timeout: 5000 });
  });

  test('should persist token after login', async ({ page, context }) => {
    const loginPage = new LoginPage(page);
    await loginPage.login();

    // Check that token is stored
    const cookies = await context.cookies();
    const localStorage = await page.evaluate(() => {
      return {
        auth_token: localStorage.getItem('auth_token'),
      };
    });

    // Token should be in localStorage
    expect(localStorage.auth_token).toBeTruthy();
  });

  test('should logout and clear session', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.login();

    // Wait for dashboard
    await page.waitForURL(/dashboard/, { timeout: 10000 });

    // Logout
    const logoutButton = page.getByText('Sair');
    await logoutButton.click();

    // Should redirect to landing
    await expect(page).toHaveURL('/');

    // Token should be cleared
    const localStorage = await page.evaluate(() => {
      return localStorage.getItem('auth_token');
    });
    expect(localStorage).toBeNull();
  });
});
