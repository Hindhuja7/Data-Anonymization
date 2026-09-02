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
        <h1 className="text-2xl font-semibold text-slate-900">Settings</h1>
        <p className="text-sm text-slate-500">Configure your DataVault AI preferences</p>
      </div>

      <div className="max-w-3xl space-y-6">
        {/* Theme */}
        <div className="bg-white border border-slate-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <SettingsIcon className="w-5 h-5" />
            Appearance
          </h2>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-900 font-medium">Light Mode</p>
              <p className="text-xs text-slate-500">Use light theme across the application</p>
            </div>
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="p-2 rounded-lg hover:bg-slate-100 transition-colors"
            >
              {darkMode ? (
                <Moon className="w-6 h-6 text-blue-600" />
              ) : (
                <Sun className="w-6 h-6 text-amber-600" />
              )}
            </button>
          </div>
        </div>

        {/* Notifications */}
        <div className="bg-white border border-slate-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <Bell className="w-5 h-5" />
            Notifications
          </h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-900 font-medium">Push Notifications</p>
                <p className="text-xs text-slate-500">Receive real-time alerts for pipeline events</p>
              </div>
              <button
                onClick={() => setNotifications(!notifications)}
                className="p-2 rounded-lg hover:bg-slate-100 transition-colors"
              >
                {notifications ? (
                  <ToggleRight className="w-6 h-6 text-emerald-600" />
                ) : (
                  <ToggleLeft className="w-6 h-6 text-slate-400" />
                )}
              </button>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-900 font-medium">Email Alerts</p>
                <p className="text-xs text-slate-500">Receive email notifications for critical events</p>
              </div>
              <button
                onClick={() => setEmailAlerts(!emailAlerts)}
                className="p-2 rounded-lg hover:bg-slate-100 transition-colors"
              >
                {emailAlerts ? (
                  <ToggleRight className="w-6 h-6 text-emerald-600" />
                ) : (
                  <ToggleLeft className="w-6 h-6 text-slate-400" />
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Security */}
        <div className="bg-white border border-slate-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <Shield className="w-5 h-5" />
            Security
          </h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-900 font-medium">Two-Factor Authentication</p>
                <p className="text-xs text-slate-500">Add an extra layer of security to your account</p>
              </div>
              <button
                onClick={() => setTwoFactor(!twoFactor)}
                className="p-2 rounded-lg hover:bg-slate-100 transition-colors"
              >
                {twoFactor ? (
                  <ToggleRight className="w-6 h-6 text-emerald-600" />
                ) : (
                  <ToggleLeft className="w-6 h-6 text-slate-400" />
                )}
              </button>
            </div>
            <button className="text-sm text-blue-600 hover:text-blue-700 transition-colors">
              Change Password
            </button>
          </div>
        </div>

        {/* API Keys */}
        <div className="bg-white border border-slate-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <Key className="w-5 h-5" />
            API Keys
          </h2>
          <div className="space-y-3">
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-slate-900 font-medium">Production Key</p>
                <span className="text-xs text-emerald-600">Active</span>
              </div>
              <p className="text-xs text-slate-500 font-mono">sk_live_51M...xY9Z</p>
            </div>
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-slate-900 font-medium">Test Key</p>
                <span className="text-xs text-emerald-600">Active</span>
              </div>
              <p className="text-xs text-slate-500 font-mono">sk_test_51N...aB3C</p>
            </div>
            <button className="text-sm text-blue-600 hover:text-blue-700 transition-colors">
              + Generate New API Key
            </button>
          </div>
        </div>

        {/* Users */}
        <div className="bg-white border border-slate-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <Users className="w-5 h-5" />
            Team Members
          </h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-medium">
                  A
                </div>
                <div>
                  <p className="text-sm text-slate-900 font-medium">Admin User</p>
                  <p className="text-xs text-slate-500">admin@datavault.ai</p>
                </div>
              </div>
              <span className="text-xs text-emerald-600">Admin</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-slate-400 rounded-full flex items-center justify-center text-white text-sm font-medium">
                  J
                </div>
                <div>
                  <p className="text-sm text-slate-900 font-medium">John Smith</p>
                  <p className="text-xs text-slate-500">john@datavault.ai</p>
                </div>
              </div>
              <span className="text-xs text-blue-600">Editor</span>
            </div>
            <button className="text-sm text-blue-600 hover:text-blue-700 transition-colors">
              + Invite Team Member
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
