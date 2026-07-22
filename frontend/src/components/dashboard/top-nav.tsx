'use client';

import React from 'react';
import { Bell, User, LogOut } from 'lucide-react';

export const TopNav = () => {
  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 ml-64">
      <div className="flex-1">
        <h1 className="text-xl font-semibold text-gray-900">Dashboard</h1>
      </div>
      
      <div className="flex items-center space-x-4">
        <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
          <Bell className="w-5 h-5" />
        </button>
        
        <div className="h-6 w-px bg-gray-200" />
        
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
            <User className="w-4 h-4 text-white" />
          </div>
          <div className="text-sm">
            <div className="font-medium text-gray-900">Admin User</div>
            <div className="text-gray-500">admin@dataguard.com</div>
          </div>
        </div>
        
        <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
          <LogOut className="w-5 h-5" />
        </button>
      </div>
    </header>
  );
};
