'use client'

import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'

export default function LogoutButton({ className = '' }: { className?: string }) {
  const router = useRouter()
  const supabase = createClient()

  async function handleLogout() {
    await supabase.auth.signOut()
    router.push('/login')
    router.refresh()
  }

  return (
    <button
      onClick={handleLogout}
      className={className || "bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-semibold transition"}
    >
      Cerrar Sesión
    </button>
  )
}
