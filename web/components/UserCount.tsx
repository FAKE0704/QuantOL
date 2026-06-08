'use client'

import { useEffect, useState } from 'react'
import { Users } from 'lucide-react'

interface RegistrationStatus {
  allow_registration: boolean
  user_count: number
}

export function UserCount() {
  const [userCount, setUserCount] = useState<number>(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchUserCount = async () => {
      try {
        const response = await fetch(`${window.location.origin}/api/auth/registration-status`)
        if (response.ok) {
          const data: RegistrationStatus = await response.json()
          setUserCount(data.user_count)
        }
      } catch (error) {
        console.error('Failed to fetch user count:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchUserCount()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-muted-foreground">
        <Users className="w-5 h-5" />
        <span>加载中...</span>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2 text-muted-foreground">
      <Users className="w-5 h-5 text-primary" />
      <span>
        <span className="text-foreground font-semibold">{userCount}</span> 位用户注册
      </span>
    </div>
  )
}
