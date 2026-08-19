"use client";

import React, { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth';
import Sidebar from '@/components/layout/Sidebar';
import TopNav from '@/components/layout/TopNav';
import { Loader2 } from 'lucide-react';

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const token = useAuthStore((state) => state.token);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;

    if (!token && pathname !== '/login') {
      router.replace('/login');
    } else if (token && (pathname === '/login' || pathname === '/')) {
      router.replace('/dashboard');
    }
  }, [mounted, token, pathname, router]);

  // Prevent flash of protected content before hydration/auth check
  if (!mounted) {
    return (
      <div className="h-screen w-screen bg-slate-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  // Login page layout (no sidebar or topnav)
  if (pathname === '/login') {
    if (token) return null; // Redirecting to dashboard
    return <div className="min-h-screen bg-slate-50">{children}</div>;
  }

  // Redirecting unauthenticated user
  if (!token) {
    return (
      <div className="h-screen w-screen bg-slate-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  // Authenticated protected page layout
  return (
    <div className="flex h-screen bg-slate-50">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <TopNav />
        <main className="flex-1 overflow-auto bg-slate-50 text-slate-900">
          {children}
        </main>
      </div>
    </div>
  );
}
