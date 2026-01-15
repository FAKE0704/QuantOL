"use client";

/**
 * Login Page
 *
 * User authentication page for QuantOL platform.
 */

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useAuth } from "@/lib/store";
import { useApi } from "@/lib/api";

const MAX_USERS = 100;

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, register, isLoading, error, clearError } = useAuth();
  const { getRegistrationStatus } = useApi();

  // UI state
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [remainingSlots, setRemainingSlots] = useState<number | null>(null);
  const [allowRegistration, setAllowRegistration] = useState(true);

  // Login form state
  const [loginUsername, setLoginUsername] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [isSubmittingLogin, setIsSubmittingLogin] = useState(false);

  // Register form state
  const [regUsername, setRegUsername] = useState("");
  const [regEmail, setRegEmail] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [isSubmittingRegister, setIsSubmittingRegister] = useState(false);

  // Get redirect URL from query params
  const redirectUrl = searchParams.get("redirect") || "/dashboard";

  // Load registration status on mount
  useEffect(() => {
    const loadRegistrationStatus = async () => {
      try {
        const response = await getRegistrationStatus();
        if (response.success && response.data) {
          setRemainingSlots(MAX_USERS - response.data.user_count);
          setAllowRegistration(response.data.allow_registration);
        }
      } catch (error) {
        console.error("Failed to load registration status:", error);
      }
    };
    loadRegistrationStatus();
  }, []);

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setIsSubmittingLogin(true);

    try {
      await login({ username_or_email: loginUsername, password: loginPassword });
      router.push(redirectUrl);
    } catch (err) {
      // Error is handled by the context
    } finally {
      setIsSubmittingLogin(false);
    }
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setIsSubmittingRegister(true);

    try {
      await register({
        username: regUsername,
        email: regEmail,
        password: regPassword,
      });
      router.push(redirectUrl);
    } catch (err) {
      // Error is handled by the context
    } finally {
      setIsSubmittingRegister(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-sky-950 via-slate-900 to-slate-950 px-4">
      <Card className="w-full max-w-md p-8 bg-slate-900/50 border-slate-800 backdrop-blur">
        {/* Logo/Header */}
        <div className="mb-6 text-center">
          <h1 className="text-3xl font-bold text-white mb-2">QuantOL</h1>
          <p className="text-slate-400">Quantitative Trading Platform</p>
        </div>

        {/* Mode Toggle */}
        <div className="mb-6 flex">
          <button
            type="button"
            onClick={() => setIsLoginMode(true)}
            className={`flex-1 py-2 text-sm font-medium transition-colors ${
              isLoginMode
                ? "text-sky-500 border-b-2 border-sky-500"
                : "text-slate-400 border-b-2 border-transparent hover:text-slate-300"
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => setIsLoginMode(false)}
            className={`flex-1 py-2 text-sm font-medium transition-colors ${
              !isLoginMode
                ? "text-sky-500 border-b-2 border-sky-500"
                : "text-slate-400 border-b-2 border-transparent hover:text-slate-300"
            }`}
            disabled={!allowRegistration}
          >
            Sign Up
            {remainingSlots !== null && (
              <span className="ml-1 text-xs opacity-75">
                ({remainingSlots} accounts left)
              </span>
            )}
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        {/* Login Form */}
        {isLoginMode ? (
          <form onSubmit={handleLoginSubmit} className="space-y-4">
            <div>
              <label htmlFor="login-username" className="block text-sm font-medium text-slate-300 mb-2">
                Username or Email
              </label>
              <input
                id="login-username"
                type="text"
                value={loginUsername}
                onChange={(e) => setLoginUsername(e.target.value)}
                className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent"
                placeholder="Enter your username or email"
                autoComplete="username"
                disabled={isLoading || isSubmittingLogin}
                required
              />
            </div>

            <div>
              <label htmlFor="login-password" className="block text-sm font-medium text-slate-300 mb-2">
                Password
              </label>
              <input
                id="login-password"
                type="password"
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
                className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent"
                placeholder="Enter your password"
                autoComplete="current-password"
                disabled={isLoading || isSubmittingLogin}
                required
              />
            </div>

            <Button
              type="submit"
              disabled={isLoading || isSubmittingLogin || !loginUsername || !loginPassword}
              className="w-full bg-sky-600 hover:bg-sky-700 text-white"
            >
              {isSubmittingLogin ? "Signing in..." : "Sign In"}
            </Button>
          </form>
        ) : (
          /* Register Form */
          <form onSubmit={handleRegisterSubmit} className="space-y-4">
            {!allowRegistration && (
              <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                <p className="text-sm text-amber-400">Registration is currently closed</p>
              </div>
            )}

            <div>
              <label htmlFor="reg-username" className="block text-sm font-medium text-slate-300 mb-2">
                Username
              </label>
              <input
                id="reg-username"
                type="text"
                value={regUsername}
                onChange={(e) => setRegUsername(e.target.value)}
                className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent"
                placeholder="Choose a username"
                autoComplete="username"
                disabled={isLoading || isSubmittingRegister || !allowRegistration}
                required
              />
            </div>

            <div>
              <label htmlFor="reg-email" className="block text-sm font-medium text-slate-300 mb-2">
                Email
              </label>
              <input
                id="reg-email"
                type="email"
                value={regEmail}
                onChange={(e) => setRegEmail(e.target.value)}
                className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent"
                placeholder="Enter your email"
                autoComplete="email"
                disabled={isLoading || isSubmittingRegister || !allowRegistration}
                required
              />
            </div>

            <div>
              <label htmlFor="reg-password" className="block text-sm font-medium text-slate-300 mb-2">
                Password
              </label>
              <input
                id="reg-password"
                type="password"
                value={regPassword}
                onChange={(e) => setRegPassword(e.target.value)}
                className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent"
                placeholder="Create a password"
                autoComplete="new-password"
                disabled={isLoading || isSubmittingRegister || !allowRegistration}
                required
              />
            </div>

            <Button
              type="submit"
              disabled={isLoading || isSubmittingRegister || !regUsername || !regEmail || !regPassword || !allowRegistration}
              className="w-full bg-sky-600 hover:bg-sky-700 text-white"
            >
              {isSubmittingRegister ? "Creating account..." : "Sign Up"}
            </Button>
          </form>
        )}

        {/* Back to Home */}
        <div className="mt-6 text-center">
          <Link href="/" className="text-sm text-slate-500 hover:text-slate-400">
            ← Back to home
          </Link>
        </div>
      </Card>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-sky-950 via-slate-900 to-slate-950 px-4">
        <Card className="w-full max-w-md p-8 bg-slate-900/50 border-slate-800 backdrop-blur">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sky-500 mx-auto mb-4" />
            <p className="text-slate-400">Loading...</p>
          </div>
        </Card>
      </div>
    }>
      <LoginForm />
    </Suspense>
  );
}
