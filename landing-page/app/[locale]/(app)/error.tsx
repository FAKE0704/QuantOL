'use client';

/**
 * Route-level Error Boundary
 *
 * Catches errors in React components within this route.
 * Displays a user-friendly error message.
 */

import { useEffect } from 'react';
import { logFrontendError } from '@/lib/errorMonitor';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to our monitoring system
    logFrontendError(
      `React Error Boundary caught: ${error.message}`,
      error,
      {
        digest: error.digest,
        componentStack: error.stack,
      }
    );
  }, [error]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-4">
      <div className="max-w-md rounded-lg border border-red-200 bg-red-50 p-6 text-center dark:border-red-800 dark:bg-red-950">
        <h2 className="mb-4 text-xl font-semibold text-red-800 dark:text-red-200">
          Something went wrong
        </h2>
        <p className="mb-6 text-red-600 dark:text-red-300">
          页面出错了，请刷新重试
        </p>
        <div className="flex flex-col gap-3 sm:flex-row">
          <button
            onClick={reset}
            className="rounded-lg bg-red-600 px-4 py-2 font-medium text-white transition-colors hover:bg-red-700 dark:bg-red-700 dark:hover:bg-red-600"
          >
            Try again
          </button>
          <button
            onClick={() => window.location.href = '/'}
            className="rounded-lg border border-red-600 px-4 py-2 font-medium text-red-600 transition-colors hover:bg-red-100 dark:border-red-400 dark:text-red-400 dark:hover:bg-red-900"
          >
            Go to homepage
          </button>
        </div>
        {process.env.NODE_ENV === 'development' && (
          <details className="mt-4 text-left">
            <summary className="cursor-pointer text-sm font-medium text-red-700 dark:text-red-300">
              Error details (dev only)
            </summary>
            <pre className="mt-2 overflow-auto rounded bg-red-100 p-2 text-xs text-red-800 dark:bg-red-900 dark:text-red-200">
              {error.message}
              {'\n'}
              {error.stack}
            </pre>
          </details>
        )}
      </div>
    </div>
  );
}
