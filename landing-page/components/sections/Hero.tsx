'use client'

import Link from 'next/link'
import { ArrowRight, Play, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { heroContent } from '@/lib/data'
import { motion } from 'framer-motion'
import { UserCount } from '@/components/UserCount'

export function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-primary/5" />

      {/* Animated grid background */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#262626_1px,transparent_1px),linear-gradient(to_bottom,#262626_1px,transparent_1px)] bg-[size:64px_64px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)] opacity-20" />

      {/* Animated gradient orbs */}
      <motion.div
        className="absolute top-1/4 -left-20 w-96 h-96 bg-primary/20 rounded-full blur-3xl"
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.3, 0.5, 0.3],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />
      <motion.div
        className="absolute bottom-1/4 -right-20 w-96 h-96 bg-accent/20 rounded-full blur-3xl"
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.3, 0.5, 0.3],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: "easeInOut",
          delay: 4
        }}
      />

      {/* Content */}
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left column - Text content */}
          <motion.div
            className="space-y-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            {/* Badge */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2, duration: 0.5 }}
            >
              <Badge className="bg-primary/10 text-primary border-primary/20 hover:bg-primary/20">
                <Sparkles className="w-3 h-3 mr-1" />
                专业级量化交易平台
              </Badge>
            </motion.div>

            {/* User Count */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3, duration: 0.6 }}
            >
              <UserCount />
            </motion.div>

            {/* Headline */}
            <motion.h1
              className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4, duration: 0.6 }}
            >
              <span className="bg-gradient-to-r from-foreground via-foreground to-muted-foreground bg-clip-text text-transparent">
                {heroContent.headline}
              </span>
            </motion.h1>

            {/* Subheadline */}
            <motion.p
              className="text-xl text-muted-foreground"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5, duration: 0.6 }}
            >
              {heroContent.subheadline}
            </motion.p>

            {/* Description */}
            <motion.p
              className="text-muted-foreground max-w-lg"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6, duration: 0.6 }}
            >
              {heroContent.description}
            </motion.p>

            {/* CTAs */}
            <motion.div
              className="flex flex-wrap gap-4"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7, duration: 0.6 }}
            >
              {heroContent.ctas.map((cta) =>
                cta.primary ? (
                  <Button
                    key={cta.label}
                    asChild
                    size="lg"
                    className="bg-gradient-to-r from-primary to-accent hover:from-primary/90 hover:to-accent/90 text-white"
                  >
                    <Link href={cta.href}>
                      {cta.label}
                      <ArrowRight className="ml-2 w-4 h-4" />
                    </Link>
                  </Button>
                ) : (
                  <Button
                    key={cta.label}
                    asChild
                    size="lg"
                    variant="outline"
                    className="border-border hover:bg-muted"
                  >
                    <Link href={cta.href}>
                      {cta.label}
                    </Link>
                  </Button>
                )
              )}
            </motion.div>

            {/* Stats */}
            <motion.div
              className="flex gap-8 pt-4"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8, duration: 0.6 }}
            >
              {heroContent.stats.map((stat, index) => (
                <div key={stat.label} className="space-y-1">
                  <div className="text-2xl font-bold text-primary">{stat.value}</div>
                  <div className="text-sm text-muted-foreground">{stat.label}</div>
                </div>
              ))}
            </motion.div>
          </motion.div>

          {/* Right column - Code preview */}
          <motion.div
            className="relative"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4, duration: 0.6 }}
          >
            <div className="relative bg-card border border-border rounded-lg p-6 shadow-2xl">
              {/* Window controls */}
              <div className="flex gap-2 mb-4">
                <div className="w-3 h-3 rounded-full bg-red-500/80" />
                <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
                <div className="w-3 h-3 rounded-full bg-green-500/80" />
              </div>

              {/* Code */}
              <pre className="font-mono text-sm text-muted-foreground overflow-x-auto">
                <code>{heroContent.codePreview}</code>
              </pre>

              {/* Glow effect */}
              <div className="absolute -inset-1 bg-gradient-to-r from-primary to-accent rounded-lg opacity-20 blur-xl -z-10" />
            </div>

            {/* Floating elements */}
            <motion.div
              className="absolute -top-4 -right-4 bg-gradient-to-br from-primary to-accent text-white p-3 rounded-lg shadow-lg"
              animate={{
                y: [0, -10, 0],
              }}
              transition={{
                duration: 3,
                repeat: Infinity,
                ease: "easeInOut"
              }}
            >
              <Play className="w-5 h-5" />
            </motion.div>
          </motion.div>
        </div>
      </div>

      {/* Scroll indicator */}
      <motion.div
        className="absolute bottom-8 left-1/2 -translate-x-1/2"
        animate={{
          y: [0, 10, 0],
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      >
        <div className="w-6 h-10 border-2 border-border rounded-full flex justify-center p-2">
          <div className="w-1 h-2 bg-muted-foreground rounded-full" />
        </div>
      </motion.div>
    </section>
  )
}
