"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Database, CheckCircle, AlertCircle, Loader2, Table, Server, RefreshCw, ShieldCheck, AlertTriangle, ArrowRight } from 'lucide-react';
import { useDatabase } from '@/context/DatabaseContext';

export default function DatabaseConnection() {
  const router = useRouter();
  const {
    formData,
    setFormData,
    selectedTable,
    setSelectedTable,
    isTesting,
    setIsTesting,
    isInspecting,
    setIsInspecting,
    isConnected,
    setIsConnected,
    connectedTable,
    setConnectedTable,
    testResult,
    setTestResult,
    inspectionData,
    setInspectionData,
    inspectionError,
    setInspectionError,
    handleInputChange,
  } = useDatabase();

  const [isConnecting, setIsConnecting] = useState(false);
  const [configuredRunId, setConfiguredRunId] = useState<string | null>(null);

  const runInspection = async (testPayload: any) => {
    setIsInspecting(true);
    setInspectionError(null);
    setInspectionData(null);
    setSelectedTable('');

    try {
      const inspectRes = await fetch('http://localhost:8000/api/database/inspect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(testPayload),
      });

      const inspectData = await inspectRes.json();

      if (inspectRes.ok && inspectData.status === 'success') {
        setInspectionData(inspectData);
      } else {
        setInspectionError(inspectData.message || 'Failed to inspect database schema.');
      }
    } catch (err) {
      setInspectionError('Network error while inspecting database.');
    } finally {
      setIsInspecting(false);
    }
  };

  const handleTestConnection = async () => {
    // 1. Basic Required Field Validation
    if (!formData.host.trim() || !formData.database.trim() || !formData.username.trim() || !formData.password) {
      setTestResult({
        success: false,
        message: 'Host, Username, Password, and Database Name are required.',
      });
      return;
    }

    // 2. Port Syntax Validation
    const portStr = formData.port.trim();
    if (!portStr) {
      setTestResult({
        success: false,
        message: 'Port number is required (e.g. 5432).',
      });
      return;
    }

    const portNum = Number(portStr);
    if (isNaN(portNum) || !Number.isInteger(portNum) || portNum <= 0 || portNum > 65535) {
      setTestResult({
        success: false,
        message: 'Port must be a valid integer between 1 and 65535.',
      });
      return;
    }

    setIsTesting(true);
    setTestResult(null);
    setInspectionData(null);
    setInspectionError(null);
    setSelectedTable('');
    setIsConnected(false);

    const testPayload = {
      type: formData.type,
      host: formData.host.trim(),
      port: portNum,
      username: formData.username.trim(),
      password: formData.password,
      database: formData.database.trim(),
      use_saved_credentials: false,
    };

    try {
      const testRes = await fetch('http://localhost:8000/api/database/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(testPayload),
      });

      const testData = await testRes.json();

      if (testRes.ok && testData.status === 'success') {
        setTestResult({
          success: true,
          message: 'Connection Test Successful!',
        });

        // Trigger dynamic inspection immediately after successful test
        await runInspection(testPayload);
      } else {
        setTestResult({
          success: false,
          message: testData.message || 'Connection test failed. Please verify credentials.',
        });
      }
    } catch (error) {
      setTestResult({
        success: false,
        message: 'Network error occurred while testing connection.',
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleConnectAndUse = async () => {
    if (!testResult?.success || !selectedTable || !inspectionData) {
      return;
    }

    setIsConnecting(true);

    try {
      const activeUserId = typeof window !== 'undefined'
        ? localStorage.getItem('datavault_user_email') || localStorage.getItem('datavault_user_id') || localStorage.getItem('datavault_active_user') || 'a@gmail.com'
        : 'a@gmail.com';

      const savePayload = {
        type: formData.type,
        host: formData.host.trim(),
        port: parseInt(formData.port, 10) || 5432,
        username: formData.username.trim(),
        password: formData.password,
        database: formData.database.trim(),
        target_table: selectedTable,
        user_id: activeUserId
      };

      const response = await fetch('/api/database/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(savePayload),
      });

      if (response.ok) {
        const resData = await response.json();
        setIsConnected(true);
        setConnectedTable(selectedTable);
        setConfiguredRunId(resData.run_id || null);
      } else {
        setTestResult({
          success: false,
          message: 'Failed to save database configuration.',
        });
      }
    } catch (error) {
      setTestResult({
        success: false,
        message: 'Error saving database configuration.',
      });
    } finally {
      setIsConnecting(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Database Connections</h1>
        <p className="text-sm text-slate-500 mt-1">
          Manually enter credentials, test connection, inspect discovered tables, and select target table for pipeline processing.
        </p>
      </div>

      {/* Main Grid: Form on Left (55%), Live DB Explorer on Right (45%) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* LEFT PANEL: Clean Manual Credential Entry */}
        <div className="lg:col-span-7 space-y-6">
          <div className="bg-white border border-slate-200 rounded-xl p-6">
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-200">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-sky-100 text-sky-600 rounded-lg">
                  <Database className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-base font-semibold text-slate-900">Manual Database Connection</h2>
                  <p className="text-xs text-slate-500">PostgreSQL / Cloud Connection</p>
                </div>
              </div>
              <span className={`text-xs font-mono px-2.5 py-1 rounded border ${
                isConnected 
                  ? 'bg-emerald-50 text-emerald-600 border-emerald-200' 
                  : 'bg-slate-100 text-slate-500 border-slate-200'
              }`}>
                {isConnected ? '✓ CONNECTED' : 'NOT CONNECTED'}
              </span>
            </div>

            <div className="space-y-4">
              {/* Database Engine */}
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wider">
                  Database Type
                </label>
                <select
                  value={formData.type}
                  onChange={(e) => handleInputChange('type', e.target.value)}
                  className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-slate-900 text-sm focus:outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20"
                >
                  <option value="postgresql">PostgreSQL (Neon DB / Cloud / On-Prem)</option>
                  <option value="mysql">MySQL / MariaDB (Aiven / AWS RDS / Cloud / On-Prem)</option>
                  <option value="sqlite">SQLite</option>
                </select>
              </div>

              {/* Host & Port */}
              <div className="grid grid-cols-3 gap-3">
                <div className="col-span-2">
                  <label className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wider">
                    Host / Endpoint
                  </label>
                  <input
                    type="text"
                    placeholder="Enter database host (e.g. ep-gentle-wave...)"
                    value={formData.host}
                    onChange={(e) => handleInputChange('host', e.target.value)}
                    className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-slate-900 text-sm focus:outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wider">
                    Port
                  </label>
                  <input
                    type="text"
                    placeholder="PostgreSQL default: 5432"
                    value={formData.port}
                    onChange={(e) => handleInputChange('port', e.target.value)}
                    className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-slate-900 text-sm focus:outline-none focus:border-sky-500 font-mono"
                  />
                </div>
              </div>

              {/* Username & Password */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wider">
                    Username
                  </label>
                  <input
                    type="text"
                    placeholder="Enter username"
                    value={formData.username}
                    onChange={(e) => handleInputChange('username', e.target.value)}
                    className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-slate-900 text-sm focus:outline-none focus:border-sky-500 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wider">
                    Password
                  </label>
                  <input
                    type="password"
                    autoComplete="new-password"
                    placeholder="Enter database password"
                    value={formData.password}
                    onChange={(e) => handleInputChange('password', e.target.value)}
                    className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-slate-900 text-sm focus:outline-none focus:border-sky-500 font-mono"
                  />
                </div>
              </div>

              {/* Database Name */}
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wider">
                  Database Name
                </label>
                <input
                  type="text"
                  placeholder="Enter database name (e.g. neondb)"
                  value={formData.database}
                  onChange={(e) => handleInputChange('database', e.target.value)}
                  className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-slate-900 text-sm focus:outline-none focus:border-sky-500 font-mono"
                />
              </div>

              {/* Test Status Banner */}
              {testResult && (
                <div className={`p-3 rounded-lg border text-xs flex items-center gap-2 ${
                  testResult.success 
                    ? 'bg-emerald-50 border-emerald-200 text-emerald-600' 
                    : 'bg-red-50 border-red-200 text-red-600'
                }`}>
                  {testResult.success ? <CheckCircle className="w-4 h-4 flex-shrink-0" /> : <AlertCircle className="w-4 h-4 flex-shrink-0" />}
                  <p>{testResult.message}</p>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex items-center justify-between pt-4 border-t border-slate-200">
                <button
                  type="button"
                  onClick={handleTestConnection}
                  disabled={isTesting || isInspecting || !formData.host || !formData.port || !formData.username || !formData.password || !formData.database}
                  className="px-5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-900 text-xs font-semibold rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50"
                >
                  {isTesting ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                  Test Connection
                </button>

                <button
                  type="button"
                  onClick={handleConnectAndUse}
                  disabled={isConnecting || isInspecting || !testResult?.success || !selectedTable || !inspectionData}
                  className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg transition-colors flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed shadow-md"
                >
                  {isConnecting ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />}
                  Connect & Use Database
                </button>
              </div>
            </div>
          </div>

          {/* Connection Summary Card */}
          {isConnected && (
            <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 space-y-3">
              <div className="flex items-center gap-2 font-bold text-sm">
                <CheckCircle className="w-4 h-4 text-emerald-600" />
                <span>Database Configured Successfully</span>
              </div>
              <p className="text-xs text-emerald-700 font-mono">
                Pipeline execution started automatically.
              </p>
              <div className="flex flex-wrap items-center gap-4 text-xs font-mono">
                {configuredRunId && (
                  <div>
                    <span className="text-slate-500 block text-[10px]">Run ID</span>
                    <strong className="text-slate-900 font-bold">{configuredRunId}</strong>
                  </div>
                )}
                <div>
                  <span className="text-slate-500 block text-[10px]">Target Table</span>
                  <strong className="text-slate-900 font-bold">{connectedTable}</strong>
                </div>
              </div>
              <div className="pt-2">
                <button
                  type="button"
                  onClick={() => router.push('/pipeline')}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg flex items-center gap-2 transition-colors shadow-md"
                >
                  <ArrowRight className="w-4 h-4" />
                  View Pipeline Status
                </button>
              </div>
            </div>
          )}
        </div>

        {/* RIGHT PANEL: Dynamic Database Discovery Overview */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-white border border-slate-200 rounded-xl p-6 h-full flex flex-col justify-between min-h-[480px]">
            <div>
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-200">
                <div className="flex items-center gap-2">
                  <Server className="w-4 h-4 text-blue-600" />
                  <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider">Database Overview</h3>
                </div>
                {inspectionData && (
                  <span className="text-[10px] font-mono bg-blue-50 text-blue-600 px-2 py-0.5 rounded border border-blue-200">
                    {inspectionData.total_tables} TABLES DISCOVERED
                  </span>
                )}
              </div>

              {/* 1. Empty Initial State */}
              {!isInspecting && !inspectionData && !inspectionError && (
                <div className="py-16 text-center space-y-3">
                  <div className="p-3 bg-slate-100 rounded-full w-fit mx-auto border border-slate-200">
                    <Database className="w-8 h-8 text-slate-500" />
                  </div>
                  <p className="text-xs text-slate-500 max-w-xs mx-auto leading-relaxed">
                    Enter database credentials and test the connection to inspect the database schema and discover tables.
                  </p>
                </div>
              )}

              {/* 2. Inspection Loading State */}
              {isInspecting && (
                <div className="py-16 text-center space-y-4">
                  <Loader2 className="w-8 h-8 text-blue-600 animate-spin mx-auto" />
                  <div>
                    <h4 className="text-sm font-semibold text-slate-900">Inspecting Database Schema...</h4>
                    <p className="text-xs text-slate-500 mt-1">
                      Discovering tables, columns, and calculating record statistics.
                    </p>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 max-w-xs mx-auto text-left text-[11px] text-slate-600 space-y-1">
                    <p className="flex items-center gap-1.5"><CheckCircle className="w-3 h-3 text-emerald-600" /> Connection Established</p>
                    <p className="flex items-center gap-1.5 text-blue-600 animate-pulse">• Inspecting table schemas & record counts...</p>
                  </div>
                </div>
              )}

              {/* 3. Inspection Error State */}
              {!isInspecting && inspectionError && (
                <div className="py-12 text-center space-y-4">
                  <div className="p-3 bg-red-50 rounded-full w-fit mx-auto border border-red-200 text-red-600">
                    <AlertTriangle className="w-8 h-8" />
                  </div>
                  <div className="space-y-1">
                    <h4 className="text-sm font-semibold text-red-600">Unable to Inspect Database</h4>
                    <p className="text-xs text-slate-500 max-w-xs mx-auto">{inspectionError}</p>
                  </div>
                  <button
                    type="button"
                    onClick={handleTestConnection}
                    className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-900 text-xs font-semibold rounded-lg transition-colors inline-flex items-center gap-2"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    Retry Inspection
                  </button>
                </div>
              )}

              {/* 4. Dynamic Inspection Metadata Panel */}
              {!isInspecting && inspectionData && (
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-3 p-3 bg-slate-50 rounded-lg border border-slate-200 text-center">
                    <div>
                      <span className="text-[10px] text-slate-500 block uppercase">Database</span>
                      <span className="text-xs font-mono font-bold text-emerald-600 truncate block">{inspectionData.database}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 block uppercase">Total Records</span>
                      <span className="text-xs font-mono font-bold text-slate-900">{inspectionData.total_records.toLocaleString()}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 block uppercase">Total Columns</span>
                      <span className="text-xs font-mono font-bold text-slate-900">{inspectionData.total_columns}</span>
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-xs font-semibold text-slate-600 uppercase tracking-wider">Select Target Table for Processing</p>
                      <span className="text-[10px] text-amber-600">Explicit Selection Required</span>
                    </div>

                    <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                      {inspectionData.tables.map((tbl: any) => {
                        const isSelected = selectedTable === tbl.name;
                        return (
                          <div
                            key={tbl.name}
                            onClick={() => setSelectedTable(tbl.name)}
                            className={`p-3 rounded-lg cursor-pointer transition-all border ${
                              isSelected
                                ? 'bg-blue-50 border-blue-500 text-slate-900 shadow-md'
                                : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-2.5">
                                <input
                                  type="radio"
                                  name="targetTableSelect"
                                  checked={isSelected}
                                  onChange={() => setSelectedTable(tbl.name)}
                                  className="text-blue-500 focus:ring-0 focus:ring-offset-0"
                                />
                                <Table className={`w-4 h-4 ${isSelected ? 'text-blue-600' : 'text-slate-400'}`} />
                                <span className={`text-xs font-mono font-bold ${isSelected ? 'text-blue-600' : 'text-slate-900'}`}>
                                  {tbl.name}
                                </span>
                              </div>
                              <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                                isSelected ? 'bg-blue-100 text-blue-700 border border-blue-200' : 'bg-slate-100 text-slate-500'
                              }`}>
                                {isSelected ? 'SELECTED TARGET' : 'SELECT'}
                              </span>
                            </div>

                            <div className="grid grid-cols-2 gap-2 text-[11px] mt-2 pt-2 border-t border-slate-200">
                              <div>
                                <span className="text-slate-500">Columns: </span>
                                <span className="text-slate-900 font-mono font-semibold">{tbl.columns}</span>
                              </div>
                              <div>
                                <span className="text-slate-500">Records: </span>
                                <span className="text-slate-900 font-mono font-semibold">{tbl.records.toLocaleString()}</span>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="pt-4 border-t border-slate-800 text-[11px] text-slate-500 flex items-center justify-between">
              <span>Dynamic PostgreSQL Metadata Query</span>
              <RefreshCw className="w-3.5 h-3.5 text-slate-500" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
