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
    { name: 'Search', href: '/dashboard/search', icon: '🔍' },
  ]

  return (
    <div className="flex h-full w-64 flex-col border-r border-zinc-200 bg-white">
      <div className="flex h-16 items-center border-b border-zinc-200 px-6">
        <h1 className="text-xl font-bold text-zinc-900">BrandPulse AI</h1>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-zinc-100 text-zinc-900'
                  : 'text-zinc-600 hover:bg-zinc-50 hover:text-zinc-900'
              )}
            >
              <span className="text-lg">{item.icon}</span>
              {item.name}
            </Link>
          )
        })}
      </nav>

      <div className="border-t border-zinc-200 p-4">
        <div className="mb-3">
          <ConnectionStatusIndicator status={status} />
        </div>
        <div className="flex items-center justify-between">
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-zinc-900 truncate">
              {user?.username}
            </p>
            <p className="text-xs text-zinc-500 truncate">{user?.email}</p>
          </div>
        </div>
        <button
          onClick={logout}
          className="mt-3 w-full rounded-md bg-zinc-100 px-3 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-200 transition-colors"
        >
          Sign out
        </button>
      </div>
    </div>
  )
}
