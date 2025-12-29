import { ProtectedRoute } from '@/components/protected-route'
import { Sidebar } from '@/components/sidebar'
import { WebSocketProvider } from '@/contexts/websocket-context'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ProtectedRoute>
      <WebSocketProvider>
        <div className="flex h-screen bg-zinc-50">
          <Sidebar />
          <main className="flex-1 overflow-y-auto">
            <div className="p-8">{children}</div>
          </main>
        </div>
      </WebSocketProvider>
    </ProtectedRoute>
  )
}
