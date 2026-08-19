"use client";

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  Database, 
  Building2, 
  Workflow, 
  CheckSquare, 
  FileText, 
  ShieldCheck, 
  Settings,
  Activity,
  Server,
  HardDrive,
  Key,
  Users
} from 'lucide-react';

interface SidebarProps {
  pipelineProgress?: string;
}

interface MenuItem {
  id: string;
  label: string;
  icon: any;
  progress?: string;
}

interface MenuSection {
  section: string;
  items: MenuItem[];
}

export default function Sidebar({ pipelineProgress }: SidebarProps) {
  const pathname = usePathname();
  const activeTab = pathname.replace('/', '') || 'dashboard';

  const menuItems: MenuSection[] = [
    {
      section: 'OVERVIEW',
      items: [
        { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
      ]
    },
    {
      section: 'DATA',
      items: [
        { id: 'database', label: 'Database Connections', icon: Database },
        { id: 'sandbox', label: 'Sandbox Environment', icon: HardDrive },
      ]
    },
    {
      section: 'EXECUTION',
      items: [
        { id: 'pipeline', label: 'Pipeline', icon: Workflow, progress: pipelineProgress },
        { id: 'simulator', label: 'Live Traffic Simulator', icon: Activity },
        { id: 'approval', label: 'Approval Queue', icon: CheckSquare },
      ]
    },
    {
      section: 'COMPLIANCE',
      items: [
        { id: 'audit', label: 'Audit Logs', icon: ShieldCheck },
        { id: 'reports', label: 'Reports', icon: FileText },
      ]
    },
    {
      section: 'SYSTEM',
      items: [
        { id: 'settings', label: 'Settings', icon: Settings },
        { id: 'api-keys', label: 'API Keys', icon: Key },
        { id: 'users', label: 'Users', icon: Users },
      ]
    }
  ];

  return (
    <div className="w-64 bg-white border-r border-slate-200 flex flex-col h-screen">
      {/* Logo - Ocean Blue Branding Area */}
      <div className="p-4 border-b border-slate-200 bg-gradient-to-r from-sky-50 to-blue-50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-sky-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
            <ShieldCheck className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-slate-900">DataVault AI</h1>
            <p className="text-xs text-slate-500">Enterprise Data Protection</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex-1 overflow-y-auto py-4">
        {menuItems.map((section) => (
          <div key={section.section} className="mb-6">
            <p className="px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              {section.section}
            </p>
            <div className="space-y-1">
              {section.items.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <Link
                    key={item.id}
                    href={`/${item.id}`}
                    className={`w-full flex items-center gap-3 px-4 py-2 text-sm transition-colors ${
                      isActive 
                        ? 'bg-blue-50 text-blue-600 border-r-2 border-blue-600' 
                        : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                    }`}
                  >
                    <Icon className={`w-4 h-4 ${isActive ? 'text-blue-600' : 'text-slate-500'}`} />
                    <span className="flex-1 text-left">{item.label}</span>
                    {item.progress && (
                      <span className="text-xs text-slate-400">{item.progress}</span>
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* System Status */}
      <div className="p-4 border-t border-slate-200">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
          System Status
        </p>
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-xs">
            <div className="w-2 h-2 bg-emerald-500 rounded-full" />
            <span className="text-slate-600">Backend Connected</span>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <div className="w-2 h-2 bg-emerald-500 rounded-full" />
            <span className="text-slate-600">Redis Connected</span>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <div className="w-2 h-2 bg-emerald-500 rounded-full" />
            <span className="text-slate-600">Database Connected</span>
          </div>
        </div>
      </div>
    </div>
  );
}
