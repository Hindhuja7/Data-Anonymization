"use client";

import React from 'react';
import { Bell, Search, User, LogOut } from 'lucide-react';
import { useAuthStore } from '@/store/auth';
import { useRouter } from 'next/navigation';

import { useDatabase } from '@/context/DatabaseContext';

export default function TopNav() {
  const { logout, user } = useAuthStore();
  const { resetWorkflow } = useDatabase();
  const router = useRouter();
  const [isLoggingOut, setIsLoggingOut] = React.useState(false);

  const handleLogout = async () => {
    if (isLoggingOut) return;
    setIsLoggingOut(true);
    try {
      await fetch('http://localhost:8000/api/pipeline/logout', { method: 'POST' });
    } catch (err) {
      console.error('Logout cleanup error:', err);
    } finally {
      try {
        resetWorkflow();
      } catch (e) {}
      if (typeof window !== 'undefined') {
        sessionStorage.removeItem('database_config');
        sessionStorage.removeItem('database_inspection');
        sessionStorage.removeItem('selected_table');
        sessionStorage.removeItem('token');
        sessionStorage.removeItem('user');
      }
      logout();
      setIsLoggingOut(false);
      router.replace('/login');
    }
  };

  return (
    <div className="h-14 bg-slate-900 border-b border-slate-800 flex items-center justify-between px-6">
      {/* Search */}
      <div className="flex-1 max-w-xl">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search pipelines, databases, reports..."
            className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500/50 focus:bg-slate-800 transition-all"
          />
        </div>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-4">
        {/* User */}
        <div className="flex items-center gap-3 pl-4 border-l border-slate-800">
          <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
            <User className="w-4 h-4 text-white" />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-white">{user?.email || 'Admin User'}</span>
          </div>
        </div>

        {/* Logout Button */}
        <button
          onClick={handleLogout}
          disabled={isLoggingOut}
          title="Sign Out"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-red-500/20 bg-red-500/10 hover:bg-red-500/20 text-red-400 text-xs font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <LogOut className={`w-3.5 h-3.5 ${isLoggingOut ? 'animate-spin' : ''}`} />
          <span>{isLoggingOut ? 'Ending pipeline & logging out...' : 'Logout'}</span>
        </button>
      </div>
    </div>
  );
}
