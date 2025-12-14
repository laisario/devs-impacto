/**
 * Test setup file for Vitest
 */

// @ts-expect-error - vitest types may not be available in all environments
import { expect, afterEach, vi } from 'vitest';
// @ts-expect-error - testing-library types may not be available
import { cleanup } from '@testing-library/react';
// @ts-expect-error - jest-dom types may not be available
import * as matchers from '@testing-library/jest-dom/matchers';

// Declare global for Node.js environment
declare const global: typeof globalThis & {
  localStorage?: Storage;
};

// Extend Vitest's expect with jest-dom matchers
expect.extend(matchers);

// Cleanup after each test
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  // Clear localStorage between tests
  if (typeof window !== 'undefined' && window.localStorage) {
    window.localStorage.clear();
  }
  if (global.localStorage) {
    global.localStorage.clear();
  }
});

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock localStorage with actual storage
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => {
      return store[key] || null;
    },
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
    get length() {
      return Object.keys(store).length;
    },
    key: (index: number) => {
      const keys = Object.keys(store);
      return keys[index] || null;
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true,
});

// Also set on global for Node.js environment
(globalThis as any).localStorage = localStorageMock;
