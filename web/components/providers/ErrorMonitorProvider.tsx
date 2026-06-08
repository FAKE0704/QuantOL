'use client';

/**
 * Error Monitor Provider
 *
 * Initializes the frontend error monitoring system when the app starts.
 * Should be placed near the root of the component tree.
 */

import { useEffect } from 'react';
import { initErrorMonitoring } from '@/lib/errorMonitor';

export function ErrorMonitorProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Initialize error monitoring on mount
    initErrorMonitoring();

    // Log that monitoring is active (in dev mode only)
    if (process.env.NODE_ENV === 'development') {
      console.log('[ErrorMonitor] Frontend error monitoring is active');

      // Expose test utilities in development
      import('@/lib/errorMonitor.test').then(({ exposeTestUtils }) => {
        exposeTestUtils();
      });
    }
  }, []);

  return <>{children}</>;
}
