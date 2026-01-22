'use client'

import { Hero } from '@/components/sections/Hero'
import { Features } from '@/components/sections/Features'
import { Performance } from '@/components/sections/Performance'
import { CTA } from '@/components/sections/CTA'
import { ShaderGradientCanvas, ShaderGradient } from '@shadergradient/react'
import { useTheme } from '@/components/providers/ThemeProvider'

export default function Home() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <>
      {/* Global ShaderGradient Background */}
      <div className="fixed inset-0 -z-10">
        <ShaderGradientCanvas
          style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }}
          pixelDensity={isDark ? 1.3 : 1.2}
          fov={isDark ? 45 : 40}
        >
          <ShaderGradient
            animate="on"
            axesHelper="off"
            brightness={isDark ? 0.3 : 0.8}
            cAzimuthAngle={isDark ? 180 : 250}
            cDistance={isDark ? 3.6 : 14}
            cPolarAngle={isDark ? 90 : 60}
            cameraZoom={isDark ? 1 : 5}
            color1={isDark ? "#ff5005" : "#57ffca"}
            color2={isDark ? "#7d8bdb" : "#30dba2"}
            color3={isDark ? "#e1565c" : "#48e1ab"}
            destination="onCanvas"
            embedMode="off"
            envPreset="dawn"
            format="gif"
            frameRate={10}
            gizmoHelper="hide"
            grain="on"
            lightType="env"
            positionX={isDark ? -1.4 : 0}
            positionY={0}
            positionZ={0}
            range="enabled"
            rangeEnd={isDark ? 40 : 38}
            rangeStart={0}
            reflection={isDark ? 0.2 : 0.4}
            rotationX={0}
            rotationY={10}
            rotationZ={50}
            shader="defaults"
            type="sphere"
            uAmplitude={isDark ? 1 : 2.4}
            uDensity={isDark ? 3.3 : 2.2}
            uFrequency={5.5}
            uSpeed={0.1}
            uStrength={isDark ? 3.1 : 5.3}
            uTime={0}
            wireframe={false}
            zoomOut={true}
          />
        </ShaderGradientCanvas>
      </div>

      <Hero />
      <Features />
      <Performance />
      <CTA />
    </>
  )
}
