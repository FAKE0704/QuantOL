"use client";

/**
 * Client-side Provider Wrapper
 *
 * Wraps the application with client-side providers like AuthProvider and ThemeProvider.
 */

import { ReactNode } from "react";
import { AuthProvider } from "@/lib/store";
import { ThemeProvider } from "@/components/providers/ThemeProvider";
import { ErrorMonitorProvider } from "@/components/providers/ErrorMonitorProvider";

export function ClientProvider({ children }: { children: ReactNode }) {
  return (
    <ErrorMonitorProvider>
      <ThemeProvider defaultTheme="light">
        <AuthProvider>{children}</AuthProvider>
      </ThemeProvider>
    </ErrorMonitorProvider>
  );
}
