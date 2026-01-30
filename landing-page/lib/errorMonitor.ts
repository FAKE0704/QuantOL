/**
 * Frontend Error Monitor
 *
 * Captures unhandled errors and Promise rejections, outputs them to console
 * for PM2 log capture, and implements rate limiting to prevent log flooding.
 */

interface ErrorContext {
  userAgent: string;
  url: string;
  timestamp: string;
  userId?: string;
}

interface ErrorRecord {
  message: string;
  filename?: string;
  lineno?: number;
  colno?: number;
  lastLogged: number;
  count: number;
}

class ErrorMonitor {
  private errorCache = new Map<string, ErrorRecord>();
  private readonly RATE_LIMIT_MS = 30000; // 30 seconds
  private readonly MAX_ERRORS_PER_MINUTE = 3;
  private errorCounter: { [key: string]: number } = {};
  private lastResetTime = Date.now();

  constructor() {
    this.resetCounterIfNeeded();
  }

  /**
   * Initialize error monitoring
   */
  init(): void {
    // Catch synchronous errors
    window.onerror = (message, source, lineno, colno, error) => {
      this.handleError({
        message: String(message),
        filename: source,
        lineno,
        colno,
        error: error || undefined,
      });
      return false; // Let the error propagate to console
    };

    // Catch unhandled Promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.handleError({
        message: `Unhandled Promise Rejection: ${event.reason}`,
        error: event.reason,
      });
    });
  }

  /**
   * Handle an error with rate limiting and deduplication
   */
  private handleError(params: {
    message: string;
    filename?: string;
    lineno?: number;
    colno?: number;
    error?: unknown;
  }): void {
    const { message, filename, lineno, colno, error } = params;

    // Create unique key for deduplication
    const key = this.createErrorKey(message, filename);
    const now = Date.now();

    // Reset counter if needed
    this.resetCounterIfNeeded();

    // Check rate limiting
    const record = this.errorCache.get(key);
    if (record) {
      const timeSinceLastLog = now - record.lastLogged;

      // Same error within rate limit period
      if (timeSinceLastLog < this.RATE_LIMIT_MS) {
        record.count++;

        // Check if we've exceeded max errors per minute
        const errorCount = this.errorCounter[key] || 0;
        if (errorCount >= this.MAX_ERRORS_PER_MINUTE) {
          return; // Skip logging this error
        }

        this.errorCounter[key] = errorCount + 1;
        record.lastLogged = now;
      } else {
        // Rate limit period passed, reset
        record.lastLogged = now;
        record.count = 1;
        this.errorCounter[key] = 1;
      }
    } else {
      // New error
      this.errorCache.set(key, {
        message,
        filename,
        lineno,
        colno,
        lastLogged: now,
        count: 1,
      });
      this.errorCounter[key] = 1;
    }

    // Log the error
    this.logToConsole({
      message,
      filename,
      lineno,
      colno,
      error,
    });
  }

  /**
   * Create a unique key for error deduplication
   */
  private createErrorKey(message: string, filename?: string): string {
    const cleanMessage = message.split('\n')[0].trim().substring(0, 100);
    return filename ? `${cleanMessage}@${filename}` : cleanMessage;
  }

  /**
   * Reset error counter if a minute has passed
   */
  private resetCounterIfNeeded(): void {
    const now = Date.now();
    if (now - this.lastResetTime > 60000) {
      this.errorCounter = {};
      this.lastResetTime = now;
    }
  }

  /**
   * Log error to console for PM2 capture
   */
  private logToConsole(params: {
    message: string;
    filename?: string;
    lineno?: number;
    colno?: number;
    error?: unknown;
  }): void {
    const { message, filename, lineno, colno, error } = params;
    const context = this.getExecutionContext();

    let logMessage = `[Frontend Error] ${message}`;

    if (filename) {
      logMessage += `\n  at ${filename}`;
      if (lineno !== undefined) {
        logMessage += `:${lineno}`;
        if (colno !== undefined) {
          logMessage += `:${colno}`;
        }
      }
    }

    logMessage += `\n  Context: ${context.url}`;
    logMessage += `\n  UserAgent: ${context.userAgent}`;
    logMessage += `\n  Time: ${context.timestamp}`;

    if (context.userId) {
      logMessage += `\n  UserId: ${context.userId}`;
    }

    // Output to console error (captured by PM2)
    console.error(logMessage);

    // Also log the stack trace if available
    if (error instanceof Error && error.stack) {
      console.error('[Stack Trace]', error.stack);
    }
  }

  /**
   * Get current execution context
   */
  private getExecutionContext(): ErrorContext {
    return {
      userAgent: navigator.userAgent,
      url: window.location.href,
      timestamp: new Date().toISOString(),
    };
  }

  /**
   * Manually log an error
   */
  logError(message: string, error?: unknown, extra?: Record<string, unknown>): void {
    const context = this.getExecutionContext();

    let logMessage = `[Frontend Error] ${message}`;
    logMessage += `\n  Context: ${context.url}`;
    logMessage += `\n  Time: ${context.timestamp}`;

    if (extra) {
      try {
        logMessage += `\n  Extra: ${JSON.stringify(extra, null, 2)}`;
      } catch {
        logMessage += `\n  Extra: [Unable to stringify]`;
      }
    }

    console.error(logMessage);

    if (error instanceof Error && error.stack) {
      console.error('[Stack Trace]', error.stack);
    }
  }

  /**
   * Manually log a warning
   */
  logWarning(message: string, extra?: Record<string, unknown>): void {
    const context = this.getExecutionContext();

    let logMessage = `[Frontend Warning] ${message}`;
    logMessage += `\n  Context: ${context.url}`;
    logMessage += `\n  Time: ${context.timestamp}`;

    if (extra) {
      try {
        logMessage += `\n  Extra: ${JSON.stringify(extra, null, 2)}`;
      } catch {
        logMessage += `\n  Extra: [Unable to stringify]`;
      }
    }

    console.warn(logMessage);
  }

  /**
   * Manually log info
   */
  logInfo(message: string, extra?: Record<string, unknown>): void {
    const context = this.getExecutionContext();

    let logMessage = `[Frontend Info] ${message}`;
    logMessage += `\n  Context: ${context.url}`;
    logMessage += `\n  Time: ${context.timestamp}`;

    if (extra) {
      try {
        logMessage += `\n  Extra: ${JSON.stringify(extra, null, 2)}`;
      } catch {
        logMessage += `\n  Extra: [Unable to stringify]`;
      }
    }

    console.log(logMessage);
  }

  /**
   * Get error statistics
   */
  getStats(): { cachedErrors: number; errorCounts: Record<string, number> } {
    return {
      cachedErrors: this.errorCache.size,
      errorCounts: { ...this.errorCounter },
    };
  }

  /**
   * Clear error cache
   */
  clearCache(): void {
    this.errorCache.clear();
    this.errorCounter = {};
    this.lastResetTime = Date.now();
  }
}

// Singleton instance
let errorMonitorInstance: ErrorMonitor | null = null;

/**
 * Get or create the ErrorMonitor singleton
 */
export function getErrorMonitor(): ErrorMonitor {
  if (!errorMonitorInstance) {
    errorMonitorInstance = new ErrorMonitor();
  }
  return errorMonitorInstance;
}

/**
 * Initialize error monitoring (call this once at app startup)
 */
export function initErrorMonitoring(): void {
  const monitor = getErrorMonitor();
  monitor.init();

  // Log initialization
  console.log('[Frontend Error Monitor] Initialized');
}

/**
 * Log an error manually
 */
export function logFrontendError(
  message: string,
  error?: unknown,
  extra?: Record<string, unknown>
): void {
  getErrorMonitor().logError(message, error, extra);
}

/**
 * Log a warning manually
 */
export function logFrontendWarning(message: string, extra?: Record<string, unknown>): void {
  getErrorMonitor().logWarning(message, extra);
}

/**
 * Log info manually
 */
export function logFrontendInfo(message: string, extra?: Record<string, unknown>): void {
  getErrorMonitor().logInfo(message, extra);
}
