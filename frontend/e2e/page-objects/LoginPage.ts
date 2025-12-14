/**
 * Page Object Model for Login Page
 */

import { Page, Locator } from '@playwright/test';

export class LoginPage {
  readonly phoneInput: Locator;
  readonly otpInput: Locator;
  readonly continueButton: Locator;
  readonly verifyButton: Locator;
  readonly backButton: Locator;

  constructor(private page: Page) {
    this.phoneInput = page.locator('input[type="tel"]').first();
    this.otpInput = page.locator('input[maxlength="6"]').first();
    this.continueButton = page.getByRole('button', { name: /continuar/i });
    this.verifyButton = page.getByRole('button', { name: /verificar/i });
    this.backButton = page.getByText('Voltar').first();
  }

  async goto() {
    await this.page.goto('/');
    const loginButton = this.page.getByText('Entrar');
    if (await loginButton.isVisible()) {
      await loginButton.click();
    }
    await this.page.waitForURL(/login/, { timeout: 5000 });
  }

  async enterPhone(phone: string) {
    await this.phoneInput.fill(phone);
  }

  async clickContinue() {
    await this.continueButton.click();
  }

  async enterOTP(otp: string) {
    await this.otpInput.fill(otp);
  }

  async clickVerify() {
    await this.verifyButton.click();
  }

  async login(phone: string = '+5511999999999', otp: string = '123456') {
    await this.enterPhone(phone);
    await this.clickContinue();
    await this.enterOTP(otp);
    await this.clickVerify();
    await this.page.waitForURL(/dashboard|onboarding/, { timeout: 10000 });
  }
}
