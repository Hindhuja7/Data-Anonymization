"use client";

import React, { useState } from 'react';
import { Search, Filter, Download, CheckCircle, AlertCircle, XCircle, Info } from 'lucide-react';

interface AuditLog {
  id: number;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'success';
  category: 'admin' | 'pipeline' | 'database' | 'system' | 'security';
  user: string;
  action: string;
  details: string;
  ipAddress?: string;
  sessionId?: string;
}

export default function AuditLogs() {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedLevel, setSelectedLevel] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const [logs] = useState<AuditLog[]>([
    {
      id: 1,
      timestamp: "2024-01-15 14:30:45",
      level: "warning",
      category: "pipeline",
      user: "System",
      action: "Workflow paused",
      details: "Workflow paused at Step 7 awaiting admin approval",
      ipAddress: "127.0.0.1",
      sessionId: "sess_12345"
    },
    {
      id: 2,
      timestamp: "2024-01-15 14:30:12",
      level: "success",
      category: "pipeline",
      user: "System",
      action: "Policy generation completed",
      details: "47 anonymization rules generated successfully",
      ipAddress: "127.0.0.1",
      sessionId: "sess_12345"
    },
    {
      id: 3,
      timestamp: "2024-01-15 14:29:55",
      level: "info",
      category: "admin",
      user: "Admin User",
      action: "Pipeline started",
      details: "Initiated anonymization pipeline for production_db",
      ipAddress: "192.168.1.100",
      sessionId: "sess_12345"
    },
    {
      id: 4,
      timestamp: "2024-01-15 14:29:50",
      level: "info",
      category: "database",
      user: "Admin User",
      action: "Database connected",
      details: "Connected to PostgreSQL production_db",
      ipAddress: "192.168.1.100",
      sessionId: "sess_12345"
    },
    {
      id: 5,
      timestamp: "2024-01-15 14:28:30",
      level: "success",
      category: "admin",
      user: "Admin User",
      action: "Login successful",
      details: "User authenticated via JWT token",
      ipAddress: "192.168.1.100",
      sessionId: "sess_12345"
    },
    {
      id: 6,
      timestamp: "2024-01-15 14:25:15",
      level: "error",
      category: "database",
      user: "System",
      action: "Connection failed",
      details: "Failed to connect to staging_db: timeout",
      ipAddress: "127.0.0.1",
      sessionId: "sess_12344"
    },
    {
      id: 7,
      timestamp: "2024-01-15 14:20:00",
      level: "warning",
      category: "security",
      user: "System",
      action: "Rate limit exceeded",
      details: "API rate limit exceeded for user Admin User",
      ipAddress: "192.168.1.100",
      sessionId: "sess_12343"
    },
    {
      id: 8,
      timestamp: "2024-01-15 14:15:30",
      level: "info",
      category: "system",
      user: "System",
      action: "System startup",
      details: "DataVault AI system initialized",
      ipAddress: "127.0.0.1",
      sessionId: "system_init"
    },
  ]);

  const filteredLogs = logs.filter(log => {
    const matchesCategory = selectedCategory === 'all' || log.category === selectedCategory;
    const matchesLevel = selectedLevel === 'all' || log.level === selectedLevel;
    const matchesSearch = searchQuery === '' || 
      log.action.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.details.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.user.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesLevel && matchesSearch;
  });

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'success': return <CheckCircle className="w-4 h-4 text-emerald-400" />;
      case 'warning': return <AlertCircle className="w-4 h-4 text-amber-400" />;
      case 'error': return <XCircle className="w-4 h-4 text-red-400" />;
      default: return <Info className="w-4 h-4 text-blue-400" />;
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'success': return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'warning': return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'error': return 'bg-red-500/10 text-red-400 border-red-500/20';
      default: return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-white">Audit Logs</h1>
        <p className="text-sm text-slate-400">System and admin activity monitoring</p>
      </div>

      {/* Filters */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 mb-6">
        <div className="flex items-center gap-4">
          <div className="flex-1 max-w-md">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search logs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
            >
              <option value="all">All Categories</option>
              <option value="admin">Admin</option>
              <option value="pipeline">Pipeline</option>
              <option value="database">Database</option>
              <option value="system">System</option>
              <option value="security">Security</option>
            </select>
            <select
              value={selectedLevel}
              onChange={(e) => setSelectedLevel(e.target.value)}
              className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
            >
              <option value="all">All Levels</option>
              <option value="success">Success</option>
              <option value="warning">Warning</option>
              <option value="error">Error</option>
              <option value="info">Info</option>
            </select>
            <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors flex items-center gap-2">
              <Download className="w-4 h-4" />
              Export
            </button>
          </div>
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-800/50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Timestamp</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Level</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Category</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">User</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Action</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Details</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">IP Address</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {filteredLogs.map((log) => (
              <tr key={log.id} className="hover:bg-slate-800/30 transition-colors">
                <td className="px-4 py-3 text-xs text-white font-mono">{log.timestamp}</td>
                <td className="px-4 py-3">
                  <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs border ${getLevelColor(log.level)}`}>
                    {getLevelIcon(log.level)}
                    {log.level}
                  </span>
                </td>
                <td className="px-4 py-3 text-xs text-slate-300 uppercase">{log.category}</td>
                <td className="px-4 py-3 text-xs text-white">{log.user}</td>
                <td className="px-4 py-3 text-xs text-white">{log.action}</td>
                <td className="px-4 py-3 text-xs text-slate-400 max-w-xs truncate">{log.details}</td>
                <td className="px-4 py-3 text-xs text-slate-400 font-mono">{log.ipAddress}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-4 mt-6">
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
          <p className="text-xs text-slate-400 mb-1">Total Logs</p>
          <p className="text-2xl font-semibold text-white">{logs.length}</p>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
          <p className="text-xs text-slate-400 mb-1">Admin Actions</p>
          <p className="text-2xl font-semibold text-blue-400">{logs.filter(l => l.category === 'admin').length}</p>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
          <p className="text-xs text-slate-400 mb-1">Security Events</p>
          <p className="text-2xl font-semibold text-amber-400">{logs.filter(l => l.category === 'security').length}</p>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
          <p className="text-xs text-slate-400 mb-1">Errors</p>
          <p className="text-2xl font-semibold text-red-400">{logs.filter(l => l.level === 'error').length}</p>
        </div>
      </div>
    </div>
  );
}
