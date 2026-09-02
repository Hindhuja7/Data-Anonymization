'use client';

import React from 'react';
import { 
  LayoutDashboard, 
  Database, 
  Search, 
  Shield as ShieldIcon,
  Zap,
  CheckCircle,
  Activity,
  Settings,
  ChevronRight
} from 'lucide-react';

const navItems = [
  {
    section: 'Overview',
    items: [
      { name: 'Overview', icon: LayoutDashboard, href: '/dashboard' },
    ],
  },
  {
    section: 'WORKSPACE',
    items: [
      { name: 'Data Sources', icon: Database, href: '/dashboard/data-sources' },
      { name: 'PII Discovery', icon: Search, href: '/dashboard/pii-discovery' },
      { name: 'Policy Studio', icon: ShieldIcon, href: '/dashboard/policy-studio' },
    ],
  },
  {
    section: 'PROTECTION',
    items: [
      { name: 'Anonymization Run', icon: Zap, href: '/dashboard/anonymization' },
      { name: 'Transformation Explorer', icon: Activity, href: '/dashboard/transformations' },
      { name: 'Change Monitoring', icon: Activity, href: '/dashboard/change-monitoring' },
    ],
  },
  {
    section: 'ASSURANCE',
    items: [
      { name: 'Validation', icon: CheckCircle, href: '/dashboard/validation' },
      { name: 'Privacy Risk', icon: ShieldIcon, href: '/dashboard/privacy-risk' },
      { name: 'Audit Reports', icon: Activity, href: '/dashboard/audit-reports' },
    ],
  },
  {
    section: 'SYSTEM',
    items: [
      { name: 'Activity', icon: Activity, href: '/dashboard/activity' },
      { name: 'Settings', icon: Settings, href: '/dashboard/settings' },
    ],
  },
];

export const Sidebar = () => {
  return (
    <aside className="w-64 bg-white border-r border-gray-200 h-screen fixed left-0 top-0 overflow-y-auto">
      <div className="p-6">
        <div className="flex items-center space-x-2 mb-8">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-600 to-accent-600 flex items-center justify-center">
            <ShieldIcon className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-bold gradient-text">DataGuard</span>
        </div>

        <nav className="space-y-6">
          {navItems.map((section) => (
            <div key={section.section}>
              <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
                {section.section}
              </div>
              <ul className="space-y-1">
                {section.items.map((item) => (
                  <li key={item.name}>
                    <a
                      href={item.href}
                      className="flex items-center space-x-3 px-3 py-2 rounded-lg text-sm text-gray-700 hover:bg-gray-50 hover:text-gray-900 transition-colors group"
                    >
                      <item.icon className="w-4 h-4 text-gray-400 group-hover:text-gray-600" />
                      <span>{item.name}</span>
                      <ChevronRight className="w-4 h-4 text-gray-400 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>
      </div>
    </aside>
  );
};
