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
import { useTranslations } from "next-intl";

const MAX_USERS = 200;

function LoginForm() {
  const t = useTranslations('login');
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
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <Card className="w-full max-w-md p-8 bg-[#FFEFD5] dark:bg-card border-border backdrop-blur">
        {/* Logo/Header */}
        <div className="mb-6 text-center">
          <h1 className="text-3xl font-bold text-foreground mb-2">{t('title')}</h1>
          <p className="text-muted-foreground">{t('subtitle')}</p>
        </div>

        {/* Mode Toggle */}
        <div className="mb-6 flex">
          <button
            type="button"
            onClick={() => setIsLoginMode(true)}
            className={`flex-1 py-2 text-sm font-medium transition-colors ${
              isLoginMode
                ? "text-primary border-b-2 border-primary"
                : "text-muted-foreground border-b-2 border-transparent hover:text-foreground"
            }`}
          >
            {t('signIn')}
          </button>
          <button
            type="button"
            onClick={() => setIsLoginMode(false)}
            className={`flex-1 py-2 text-sm font-medium transition-colors ${
              !isLoginMode
                ? "text-primary border-b-2 border-primary"
                : "text-muted-foreground border-b-2 border-transparent hover:text-foreground"
            }`}
            disabled={!allowRegistration}
          >
            {t('signUp')}
            {remainingSlots !== null && (
              <span className="ml-1 text-xs opacity-75">
                {t('accountsLeft', { count: remainingSlots })}
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
              <label htmlFor="login-username" className="block text-sm font-medium text-muted-foreground mb-2">
                {t('usernameOrEmail')}
              </label>
              <input
                id="login-username"
                type="text"
                value={loginUsername}
                onChange={(e) => setLoginUsername(e.target.value)}
                className="w-full px-4 py-2 bg-input border border-border rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                placeholder={t('enterUsernameOrEmail')}
                autoComplete="username"
                disabled={isLoading || isSubmittingLogin}
                required
              />
            </div>

            <div>
              <label htmlFor="login-password" className="block text-sm font-medium text-muted-foreground mb-2">
                {t('password')}
              </label>
              <input
                id="login-password"
                type="password"
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
                className="w-full px-4 py-2 bg-input border border-border rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                placeholder={t('enterPassword')}
                autoComplete="current-password"
                disabled={isLoading || isSubmittingLogin}
                required
              />
            </div>

            <Button
              type="submit"
              disabled={isLoading || isSubmittingLogin || !loginUsername || !loginPassword}
              className="w-full bg-[#FFEFD5] dark:bg-gradient-to-r dark:from-amber-500 dark:to-orange-500 hover:bg-[#FFE0C0] dark:hover:from-amber-600 dark:hover:to-orange-600 text-foreground dark:text-white rounded-full font-medium transition-all shadow-md hover:shadow-lg"
            >
              {isSubmittingLogin ? t('signingIn') : t('signIn')}
            </Button>
          </form>
        ) : (
          /* Register Form */
          <form onSubmit={handleRegisterSubmit} className="space-y-4">
            {!allowRegistration && (
              <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                <p className="text-sm text-amber-400">{t('registrationClosed')}</p>
              </div>
            )}

            <div>
              <label htmlFor="reg-username" className="block text-sm font-medium text-muted-foreground mb-2">
                {t('username')}
              </label>
              <input
                id="reg-username"
                type="text"
                value={regUsername}
                onChange={(e) => setRegUsername(e.target.value)}
                className="w-full px-4 py-2 bg-input border border-border rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                placeholder={t('chooseUsername')}
                autoComplete="username"
                disabled={isLoading || isSubmittingRegister || !allowRegistration}
                required
              />
            </div>

            <div>
              <label htmlFor="reg-email" className="block text-sm font-medium text-muted-foreground mb-2">
                {t('email')}
              </label>
              <input
                id="reg-email"
                type="email"
                value={regEmail}
                onChange={(e) => setRegEmail(e.target.value)}
                className="w-full px-4 py-2 bg-input border border-border rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                placeholder={t('enterEmail')}
                autoComplete="email"
                disabled={isLoading || isSubmittingRegister || !allowRegistration}
                required
              />
            </div>

            <div>
              <label htmlFor="reg-password" className="block text-sm font-medium text-muted-foreground mb-2">
                {t('password')}
              </label>
              <input
                id="reg-password"
                type="password"
                value={regPassword}
                onChange={(e) => setRegPassword(e.target.value)}
                className="w-full px-4 py-2 bg-input border border-border rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                placeholder={t('createPassword')}
                autoComplete="new-password"
                disabled={isLoading || isSubmittingRegister || !allowRegistration}
                required
              />
            </div>

            <Button
              type="submit"
              disabled={isLoading || isSubmittingRegister || !regUsername || !regEmail || !regPassword || !allowRegistration}
              className="w-full bg-[#FFEFD5] dark:bg-gradient-to-r dark:from-amber-500 dark:to-orange-500 hover:bg-[#FFE0C0] dark:hover:from-amber-600 dark:hover:to-orange-600 text-foreground dark:text-white rounded-full font-medium transition-all shadow-md hover:shadow-lg"
            >
              {isSubmittingRegister ? t('signingUp') : t('signUp')}
            </Button>
          </form>
        )}

        {/* Back to Home */}
        <div className="mt-6 text-center">
          <Link href="/" className="text-sm text-muted-foreground hover:text-muted-foreground">
            {t('backToHome')}
          </Link>
        </div>
      </Card>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center bg-background px-4">
        <Card className="w-full max-w-md p-8 bg-[#FFEFD5] dark:bg-card border-border backdrop-blur">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4" />
            <p className="text-muted-foreground">Loading...</p>
          </div>
        </Card>
      </div>
    }>
      <LoginForm />
    </Suspense>
  );
}
