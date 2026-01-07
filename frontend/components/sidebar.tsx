'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuth } from '@/contexts/auth-context'
import { useWebSocketContext } from '@/contexts/websocket-context'
import { ConnectionStatusIndicator } from '@/components/connection-status'
import { cn } from '@/lib/utils'

export function Sidebar() {
  const pathname = usePathname()
  const { user, logout } = useAuth()
  const { status } = useWebSocketContext()

  const navigation = [
    {
      name: 'Overview',
      href: '/dashboard',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      )
    },
    {
      name: 'Brands',
      href: '/dashboard/brands',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
        </svg>
      )
    },
  ]

  // Generate user avatar color based on username
  const getUserColor = (name?: string) => {
    if (!name) return 'from-primary to-secondary'
    const colors = [
      'from-blue-500 to-blue-600',
      'from-purple-500 to-purple-600',
      'from-pink-500 to-pink-600',
      'from-teal-500 to-teal-600',
      'from-green-500 to-green-600',
      'from-orange-500 to-orange-600',
    ]
    const hash = name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
    return colors[hash % colors.length]
  }

  return (
    <div className="flex h-full w-64 flex-col border-r border-border bg-card relative overflow-hidden">
      {/* Decorative gradient background */}
      <div className="absolute top-0 right-0 w-64 h-64 gradient-primary opacity-5 rounded-full blur-3xl -translate-y-32 translate-x-32" />

      {/* Header */}
      <div className="relative flex h-16 items-center border-b border-border px-6">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg gradient-primary">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <h1 className="text-xl font-bold gradient-text">BrandPulse AI</h1>
        </div>
      </div>

      {/* Navigation */}
      <nav className="relative flex-1 space-y-2 px-3 py-6">
        {navigation.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'group flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-semibold transition-all duration-200 relative overflow-hidden',
                isActive
                  ? 'gradient-primary text-white shadow-lg'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground'
              )}
            >
              {isActive && (
                <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/10 to-white/0 shimmer" />
              )}
              <div className={cn(
                'flex h-9 w-9 items-center justify-center rounded-lg transition-all',
                isActive ? 'bg-white/20' : 'bg-muted/50 group-hover:bg-muted'
              )}>
                {item.icon}
              </div>
              <span className="relative">{item.name}</span>
            </Link>
          )
        })}
      </nav>

      {/* User Section */}
      <div className="relative border-t border-border p-4">
        <div className="mb-4">
          <ConnectionStatusIndicator status={status} />
        </div>

        {/* User Info Card */}
        <div className="mb-3 rounded-xl bg-muted/50 p-3">
          <div className="flex items-center gap-3">
            {/* User Avatar */}
            <div className={`flex-shrink-0 h-10 w-10 rounded-xl bg-gradient-to-br ${getUserColor(user?.username)} flex items-center justify-center shadow-lg`}>
              <span className="text-lg font-bold text-white">
                {user?.username?.charAt(0).toUpperCase() || 'U'}
              </span>
            </div>

            {/* User Details */}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-bold text-foreground truncate">
                {user?.username}
              </p>
              <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
            </div>
          </div>
        </div>

        {/* Sign Out Button */}
        <button
          onClick={logout}
          className="group w-full rounded-xl bg-muted px-4 py-3 text-sm font-semibold text-foreground hover:bg-danger hover:text-white transition-all duration-200 flex items-center justify-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          Sign out
        </button>
      </div>
    </div>
  )
}
