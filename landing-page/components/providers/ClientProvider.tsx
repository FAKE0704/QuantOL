"use client";

/**
 * Client-side Provider Wrapper
 *
 * Wraps the application with client-side providers like AuthProvider and ThemeProvider.
 */

import { ReactNode } from "react";
import { AuthProvider } from "@/lib/store";
import { ThemeProvider } from "@/components/providers/ThemeProvider";

export function ClientProvider({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider defaultTheme="light">
      <AuthProvider>{children}</AuthProvider>
    </ThemeProvider>
  );
}
