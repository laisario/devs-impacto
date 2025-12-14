/**
 * Page Object Model for Dashboard Page
 */

import { Page, Locator } from '@playwright/test';

export class DashboardPage {
  readonly checklistTab: Locator;
  readonly documentsTab: Locator;
  readonly taskItems: Locator;
  readonly documentItems: Locator;
  readonly logoutButton: Locator;

  constructor(private page: Page) {
    this.checklistTab = page.getByText('Checklist de Tarefas');
    this.documentsTab = page.getByText('Meus Documentos');
    this.taskItems = page.locator('[class*="bg-white"]').filter({ hasText: /tarefa|task/i });
    this.documentItems = page.locator('[class*="bg-white"]').filter({ hasText: /documento|document/i });
    this.logoutButton = page.getByText('Sair');
  }

  async goto() {
    await this.page.goto('/dashboard');
    await this.page.waitForLoadState('networkidle');
  }

  async clickChecklistTab() {
    await this.checklistTab.click();
  }

  async clickDocumentsTab() {
    await this.documentsTab.click();
  }

  async getTaskCount(): Promise<number> {
    return await this.taskItems.count();
  }

  async getDocumentCount(): Promise<number> {
    return await this.documentItems.count();
  }

  async clickTask(index: number) {
    await this.taskItems.nth(index).click();
  }

  async logout() {
    await this.logoutButton.click();
    await this.page.waitForURL('/', { timeout: 5000 });
  }
}
