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
    { name: 'Overview', href: '/dashboard', icon: '📊' },
    { name: 'Brands', href: '/dashboard/brands', icon: '🏷️' },
  ]

  return (
    <div className="flex h-full w-64 flex-col border-r border-border bg-card">
      <div className="flex h-16 items-center border-b border-border px-6">
        <h1 className="text-xl font-bold gradient-text">BrandPulse AI</h1>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200',
                isActive
                  ? 'bg-primary/10 text-primary'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground'
              )}
            >
              <span className="text-lg">{item.icon}</span>
              {item.name}
            </Link>
          )
        })}
      </nav>

      <div className="border-t border-border p-4">
        <div className="mb-3">
          <ConnectionStatusIndicator status={status} />
        </div>
        <div className="flex items-center justify-between">
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground truncate">
              {user?.username}
            </p>
            <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
          </div>
        </div>
        <button
          onClick={logout}
          className="mt-3 w-full rounded-lg bg-muted px-3 py-2 text-sm font-medium text-foreground hover:bg-danger hover:text-white transition-all duration-200"
        >
          Sign out
        </button>
      </div>
    </div>
  )
}
