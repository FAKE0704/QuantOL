/**
 * Error Monitor Testing Utilities
 *
 * Helper functions to test the frontend error monitoring system.
 * These can be called from the browser console to verify error logging.
 */

import { logFrontendError, logFrontendWarning, logFrontendInfo } from './errorMonitor';

/**
 * Test logging an error manually
 */
export function testLogError() {
  logFrontendError('Test error message', new Error('Test error stack'), {
    userId: 'test-user-123',
    action: 'test-error-log',
  });
}

/**
 * Test logging a warning manually
 */
export function testLogWarning() {
  logFrontendWarning('Test warning message', {
    userId: 'test-user-123',
    action: 'test-warning-log',
  });
}

/**
 * Test logging info manually
 */
export function testLogInfo() {
  logFrontendInfo('Test info message', {
    userId: 'test-user-123',
    action: 'test-info-log',
  });
}

/**
 * Test synchronous error (throw in console)
 * Usage: In browser console, run: testSyncError()
 */
export function testSyncError() {
  // This will be caught by window.onerror
  const error = new Error('Test synchronous error');
  throw error;
}

/**
 * Test Promise rejection (run in console)
 * Usage: In browser console, run: testPromiseRejection()
 */
export function testPromiseRejection() {
  // This will be caught by unhandledrejection
  Promise.reject(new Error('Test Promise rejection'));
}

/**
 * Test high-frequency errors (to verify rate limiting)
 * Usage: In browser console, run: testHighFrequencyErrors()
 */
export function testHighFrequencyErrors() {
  for (let i = 0; i < 10; i++) {
    setTimeout(() => {
      logFrontendError(`High frequency error #${i + 1}`, undefined, {
        iteration: i + 1,
      });
    }, i * 100);
  }
}

/**
 * Expose test functions to window object for console testing
 * Call this once, then use window.testErrorMonitor to access tests
 */
export function exposeTestUtils() {
  if (typeof window !== 'undefined') {
    (window as any).testErrorMonitor = {
      logError: testLogError,
      logWarning: testLogWarning,
      logInfo: testLogInfo,
      syncError: testSyncError,
      promiseRejection: testPromiseRejection,
      highFrequency: testHighFrequencyErrors,
    };
    console.log('[ErrorMonitor] Test utilities exposed to window.testErrorMonitor');
    console.log('[ErrorMonitor] Available tests:');
    console.log('  - window.testErrorMonitor.logError()');
    console.log('  - window.testErrorMonitor.logWarning()');
    console.log('  - window.testErrorMonitor.logInfo()');
    console.log('  - window.testErrorMonitor.syncError()');
    console.log('  - window.testErrorMonitor.promiseRejection()');
    console.log('  - window.testErrorMonitor.highFrequency()');
  }
}
