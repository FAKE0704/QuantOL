"use client";

/**
 * Client-side Provider Wrapper
 *
 * Wraps the application with client-side providers like AuthProvider.
 */

import { ReactNode } from "react";
import { AuthProvider } from "@/lib/store";

export function ClientProvider({ children }: { children: ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}
