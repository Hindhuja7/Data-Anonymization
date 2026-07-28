"use client";

import React, { useState } from 'react';
import { 
  Settings as SettingsIcon, 
  Bell, 
  Shield, 
  Key, 
  Users, 
  Moon, 
  Sun,
  ToggleLeft,
  ToggleRight
} from 'lucide-react';

export default function Settings() {
  const [darkMode, setDarkMode] = useState(true);
  const [notifications, setNotifications] = useState(true);
  const [emailAlerts, setEmailAlerts] = useState(false);
  const [twoFactor, setTwoFactor] = useState(false);

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-white">Settings</h1>
        <p className="text-sm text-slate-400">Configure your DataVault AI preferences</p>
      </div>

      <div className="max-w-3xl space-y-6">
        {/* Theme */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <SettingsIcon className="w-5 h-5" />
            Appearance
          </h2>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-white font-medium">Dark Mode</p>
              <p className="text-xs text-slate-400">Use dark theme across the application</p>
            </div>
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="p-2 rounded-lg hover:bg-slate-800 transition-colors"
            >
              {darkMode ? (
                <Moon className="w-6 h-6 text-blue-400" />
              ) : (
                <Sun className="w-6 h-6 text-amber-400" />
              )}
            </button>
          </div>
        </div>

        {/* Notifications */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Bell className="w-5 h-5" />
            Notifications
          </h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-white font-medium">Push Notifications</p>
                <p className="text-xs text-slate-400">Receive real-time alerts for pipeline events</p>
              </div>
              <button
                onClick={() => setNotifications(!notifications)}
                className="p-2 rounded-lg hover:bg-slate-800 transition-colors"
              >
                {notifications ? (
                  <ToggleRight className="w-6 h-6 text-emerald-400" />
                ) : (
                  <ToggleLeft className="w-6 h-6 text-slate-400" />
                )}
              </button>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-white font-medium">Email Alerts</p>
                <p className="text-xs text-slate-400">Receive email notifications for critical events</p>
              </div>
              <button
                onClick={() => setEmailAlerts(!emailAlerts)}
                className="p-2 rounded-lg hover:bg-slate-800 transition-colors"
              >
                {emailAlerts ? (
                  <ToggleRight className="w-6 h-6 text-emerald-400" />
                ) : (
                  <ToggleLeft className="w-6 h-6 text-slate-400" />
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Security */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Shield className="w-5 h-5" />
            Security
          </h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-white font-medium">Two-Factor Authentication</p>
                <p className="text-xs text-slate-400">Add an extra layer of security to your account</p>
              </div>
              <button
                onClick={() => setTwoFactor(!twoFactor)}
                className="p-2 rounded-lg hover:bg-slate-800 transition-colors"
              >
                {twoFactor ? (
                  <ToggleRight className="w-6 h-6 text-emerald-400" />
                ) : (
                  <ToggleLeft className="w-6 h-6 text-slate-400" />
                )}
              </button>
            </div>
            <button className="text-sm text-blue-400 hover:text-blue-300 transition-colors">
              Change Password
            </button>
          </div>
        </div>

        {/* API Keys */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Key className="w-5 h-5" />
            API Keys
          </h2>
          <div className="space-y-3">
            <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-700">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-white font-medium">Production Key</p>
                <span className="text-xs text-emerald-400">Active</span>
              </div>
              <p className="text-xs text-slate-400 font-mono">sk_live_51M...xY9Z</p>
            </div>
            <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-700">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-white font-medium">Test Key</p>
                <span className="text-xs text-emerald-400">Active</span>
              </div>
              <p className="text-xs text-slate-400 font-mono">sk_test_51N...aB3C</p>
            </div>
            <button className="text-sm text-blue-400 hover:text-blue-300 transition-colors">
              + Generate New API Key
            </button>
          </div>
        </div>

        {/* Users */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Users className="w-5 h-5" />
            Team Members
          </h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-medium">
                  A
                </div>
                <div>
                  <p className="text-sm text-white font-medium">Admin User</p>
                  <p className="text-xs text-slate-400">admin@datavault.ai</p>
                </div>
              </div>
              <span className="text-xs text-emerald-400">Admin</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-slate-600 rounded-full flex items-center justify-center text-white text-sm font-medium">
                  J
                </div>
                <div>
                  <p className="text-sm text-white font-medium">John Smith</p>
                  <p className="text-xs text-slate-400">john@datavault.ai</p>
                </div>
              </div>
              <span className="text-xs text-blue-400">Editor</span>
            </div>
            <button className="text-sm text-blue-400 hover:text-blue-300 transition-colors">
              + Invite Team Member
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
