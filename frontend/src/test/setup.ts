import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';

// 清理 DOM
afterEach(() => {
  cleanup();
});

// 自定义断言扩展
expect.extend({
  toBeAccessible(received: Element | Document | null) {
    if (!received) {
      return { pass: false, message: () => 'Expected element to be accessible but received null' };
    }

    const issues: string[] = [];

    // 检查 alt 文本
    const images = received.querySelectorAll?.('img') || [];
    images.forEach((img, i) => {
      if (!img.getAttribute('alt')) {
        issues.push(`Image ${i + 1} is missing alt text`);
      }
    });

    // 检查按钮是否有 aria-label 或文本
    const buttons = received.querySelectorAll?.('button') || [];
    buttons.forEach((button, i) => {
      const text = button.textContent?.trim();
      const ariaLabel = button.getAttribute('aria-label');
      if (!text && !ariaLabel) {
        issues.push(`Button ${i + 1} is missing accessible text`);
      }
    });

    const pass = issues.length === 0;

    return {
      pass,
      message: () => `Expected element to be accessible${issues.length ? ': ' + issues.join(', ') : ''}`,
    };
  },
});
