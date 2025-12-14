/**
 * E2E test fixtures and helpers
 */

import type { Page } from '@playwright/test';

export class AuthHelper {
  constructor(private page: Page) {}

  async login(phone: string = '+5511999999999', otp: string = '123456') {
    // Navigate to login if not already there
    await this.page.goto('/');
    const loginButton = this.page.getByText('Entrar');
    if (await loginButton.isVisible()) {
      await loginButton.click();
    }

    // Wait for phone input
    await this.page.waitForSelector('input[type="tel"], input[placeholder*="telefone" i]', {
      timeout: 5000,
    });

    // Enter phone number
    const phoneInput = this.page.locator('input[type="tel"], input[placeholder*="telefone" i]').first();
    await phoneInput.fill(phone);
    await this.page.getByRole('button', { name: /continuar|enviar/i }).click();

    // Wait for OTP input
    await this.page.waitForSelector('input[placeholder*="código" i], input[maxlength="6"]', {
      timeout: 5000,
    });

    // Enter OTP
    const otpInput = this.page.locator('input[placeholder*="código" i], input[maxlength="6"]').first();
    await otpInput.fill(otp);
    await this.page.getByRole('button', { name: /verificar/i }).click();

    // Wait for redirect to dashboard
    await this.page.waitForURL(/dashboard|onboarding/, { timeout: 10000 });
  }

  async logout() {
    const logoutButton = this.page.getByText('Sair', { exact: false });
    if (await logoutButton.isVisible()) {
      await logoutButton.click();
    }
    await this.page.waitForURL('/', { timeout: 5000 });
  }
}

export class APIHelper {
  private baseURL = process.env.E2E_API_BASE_URL || 'http://localhost:8000';

  async createUser(phone: string = '+5511999999999'): Promise<string> {
    // Start auth
    await fetch(`${this.baseURL}/auth/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone_e164: phone }),
    });

    // Verify and get token
    const verifyResponse = await fetch(`${this.baseURL}/auth/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone_e164: phone, otp: '123456' }),
    });

    const data = await verifyResponse.json();
    return data.access_token;
  }

  async createProducerProfile(token: string) {
    const response = await fetch(`${this.baseURL}/producer-profile`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        producer_type: 'individual',
        name: 'Test Producer',
        address: 'Test Address',
        city: 'Test City',
        state: 'SP',
        dap_caf_number: 'DAP123456',
        cpf: '12345678901',
      }),
    });
    return response.json();
  }
}
