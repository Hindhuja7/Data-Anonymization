'use client';

import React, { useState } from 'react';
import { Database, Check, AlertCircle, Eye, EyeOff, Search, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { mockDatabaseConnection } from '@/lib/mock-data';
import { DatabaseType, DatabaseStatus } from '@/lib/types';

const databaseTypes = [
  {
    type: DatabaseType.POSTGRESQL,
    name: 'PostgreSQL',
    description: 'Open-source relational database',
    icon: '🐘',
    defaultPort: 5432,
  },
  {
    type: DatabaseType.MYSQL,
    name: 'MySQL',
    description: 'Popular open-source database',
    icon: '🐬',
    defaultPort: 3306,
  },
  {
    type: DatabaseType.SQL_SERVER,
    name: 'SQL Server',
    description: 'Microsoft SQL Server',
    icon: '🔷',
    defaultPort: 1433,
  },
];

export default function DataSourcesPage() {
  const [selectedType, setSelectedType] = useState<DatabaseType | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [isConnected, setIsConnected] = useState(true);
  const [isConnecting, setIsConnecting] = useState(false);

  const handleConnect = () => {
    setIsConnecting(true);
    setTimeout(() => {
      setIsConnecting(false);
      setIsConnected(true);
    }, 2000);
  };

  const handleTestConnection = () => {
    setIsConnecting(true);
    setTimeout(() => {
      setIsConnecting(false);
    }, 1500);
  };

  if (isConnected) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Data Sources</h1>
          <p className="text-gray-600 mt-1">Manage your database connections</p>
        </div>

        {/* Connected Database Card */}
        <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
          <div className="flex items-start justify-between mb-6">
            <div className="flex items-center space-x-4">
              <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center">
                <Database className="w-8 h-8 text-white" />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-900">Production Database</h3>
                <div className="flex items-center space-x-2 mt-1">
                  <Badge variant="success">Connected</Badge>
                  <span className="text-sm text-gray-500">PostgreSQL</span>
                </div>
              </div>
            </div>
            <Button variant="outline" size="sm">
              Disconnect
            </Button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-500 mb-1">Type</div>
              <div className="font-medium text-gray-900">PostgreSQL</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-500 mb-1">Status</div>
              <div className="font-medium text-green-600">Connected</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-500 mb-1">Access</div>
              <div className="font-medium text-gray-900">Read Only</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-500 mb-1">Tables</div>
              <div className="font-medium text-gray-900">4</div>
            </div>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
            <div className="flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
              <div>
                <div className="font-medium text-yellow-800">Security Notice</div>
                <div className="text-sm text-yellow-700 mt-1">
                  Your source database is accessed using a read-only connection. No data modifications will be made to the source.
                </div>
              </div>
            </div>
          </div>

          <div className="flex space-x-3">
            <Button className="flex-1">
              <Search className="w-4 h-4 mr-2" />
              View Schema
            </Button>
            <Button variant="outline" className="flex-1">
              <ArrowRight className="w-4 h-4 mr-2" />
              Start PII Discovery
            </Button>
          </div>
        </div>

        {/* Add New Database */}
        <div className="text-center py-12 border-2 border-dashed border-gray-200 rounded-xl">
          <Database className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Add Another Database</h3>
          <p className="text-gray-500 mb-4">Connect additional data sources for anonymization</p>
          <Button variant="outline" onClick={() => setIsConnected(false)}>
            Connect New Database
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Data Sources</h1>
        <p className="text-gray-600 mt-1">Connect your database to start the privacy pipeline</p>
      </div>

      {/* Database Type Selection */}
      {!selectedType ? (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Select Database Type</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {databaseTypes.map((db) => (
              <button
                key={db.type}
                onClick={() => setSelectedType(db.type)}
                className="bg-white rounded-xl p-6 border-2 border-gray-200 hover:border-primary-500 hover:shadow-md transition-all text-left group"
              >
                <div className="text-4xl mb-4">{db.icon}</div>
                <h3 className="text-lg font-semibold text-gray-900 mb-1">{db.name}</h3>
                <p className="text-sm text-gray-500">{db.description}</p>
                <div className="mt-4 flex items-center text-primary-600 opacity-0 group-hover:opacity-100 transition-opacity">
                  <span className="text-sm font-medium">Continue</span>
                  <ArrowRight className="w-4 h-4 ml-2" />
                </div>
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
          <button
            onClick={() => setSelectedType(null)}
            className="text-sm text-gray-500 hover:text-gray-700 mb-6 flex items-center"
          >
            ← Back to database selection
          </button>

          <h2 className="text-lg font-semibold text-gray-900 mb-6">
            Connect {databaseTypes.find((db) => db.type === selectedType)?.name}
          </h2>

          {/* Security Notice */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <div className="flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5" />
              <div>
                <div className="font-medium text-blue-800">Security Notice</div>
                <div className="text-sm text-blue-700 mt-1">
                  Your source database is accessed using a read-only connection. No data modifications will be made to the source.
                </div>
              </div>
            </div>
          </div>

          {/* Connection Form */}
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Host</label>
                <input
                  type="text"
                  defaultValue="localhost"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="localhost"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Port</label>
                <input
                  type="number"
                  defaultValue={databaseTypes.find((db) => db.type === selectedType)?.defaultPort}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="5432"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Database Name</label>
              <input
                type="text"
                defaultValue="production_db"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="production_db"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Username</label>
                <input
                  type="text"
                  defaultValue="admin"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="admin"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent pr-10"
                    placeholder="••••••••"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            </div>

            {/* Advanced Settings */}
            <details className="mt-4">
              <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900">
                Advanced Settings
              </summary>
              <div className="mt-4 space-y-4 pt-4 border-t border-gray-200">
                <div className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    id="ssl"
                    className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                  />
                  <label htmlFor="ssl" className="text-sm text-gray-700">Enable SSL</label>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Connection Timeout (seconds)</label>
                  <input
                    type="number"
                    defaultValue="30"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>
              </div>
            </details>
          </div>

          {/* Actions */}
          <div className="flex space-x-3 mt-6">
            <Button
              variant="outline"
              onClick={handleTestConnection}
              disabled={isConnecting}
              className="flex-1"
            >
              {isConnecting ? 'Testing...' : 'Test Connection'}
            </Button>
            <Button
              onClick={handleConnect}
              disabled={isConnecting}
              className="flex-1"
            >
              {isConnecting ? 'Connecting...' : 'Connect & Scan'}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
