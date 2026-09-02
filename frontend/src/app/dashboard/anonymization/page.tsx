'use client';

import React, { useState, useEffect } from 'react';
import { Database, Lock, CheckCircle, AlertCircle, Play, Square, Activity } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { mockAnonymizationRun } from '@/lib/mock-data';
import { AnonymizationStatus } from '@/lib/types';

export default function AnonymizationRunPage() {
  const [run, setRun] = useState(mockAnonymizationRun);
  const [isRunning, setIsRunning] = useState(true);

  // Simulate live updates
  useEffect(() => {
    if (!isRunning) return;

    const interval = setInterval(() => {
      setRun((prev) => {
        if (prev.rowsProcessed >= prev.totalRows) {
          setIsRunning(false);
          return { ...prev, status: AnonymizationStatus.COMPLETED };
        }

        const newRowsProcessed = Math.min(prev.rowsProcessed + 2450, prev.totalRows);
        const newProgress = (newRowsProcessed / prev.totalRows) * 100;
        const newChunk = Math.floor(newRowsProcessed / 1000);

        return {
          ...prev,
          rowsProcessed: newRowsProcessed,
          currentChunk: newChunk,
          tables: prev.tables.map((table) =>
            table.name === 'transactions'
              ? {
                  ...table,
                  progress: Math.min(newProgress, 100),
                  rowsProcessed: Math.min(newRowsProcessed, table.totalRows),
                }
              : table
          ),
          activityLog: [
            {
              timestamp: new Date().toISOString(),
              message: `Processing chunk ${newChunk}`,
              type: 'INFO',
            },
            ...prev.activityLog.slice(0, 4),
          ],
        };
      });
    }, 2000);

    return () => clearInterval(interval);
  }, [isRunning]);

  const handleStart = () => {
    setIsRunning(true);
    setRun({ ...run, status: AnonymizationStatus.RUNNING });
  };

  const handleStop = () => {
    setIsRunning(false);
    setRun({ ...run, status: AnonymizationStatus.STOPPED });
  };

  const getTableStatusColor = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return 'text-green-600';
      case 'IN_PROGRESS':
        return 'text-primary-600';
      case 'FAILED':
        return 'text-red-600';
      default:
        return 'text-gray-400';
    }
  };

  const getTableStatusIcon = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return <CheckCircle className="w-5 h-5" />;
      case 'IN_PROGRESS':
        return <Activity className="w-5 h-5 animate-pulse" />;
      case 'FAILED':
        return <AlertCircle className="w-5 h-5" />;
      default:
        return <div className="w-5 h-5 rounded-full border-2 border-gray-300" />;
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Protection Run</h1>
          <p className="text-gray-600 mt-1">Monitor anonymization pipeline execution</p>
        </div>
        <div className="flex items-center space-x-3">
          <Badge
            variant={run.status === AnonymizationStatus.RUNNING ? 'success' : run.status === AnonymizationStatus.COMPLETED ? 'success' : 'warning'}
          >
            {run.status}
          </Badge>
          {run.status === AnonymizationStatus.NOT_STARTED ? (
            <Button onClick={handleStart}>
              <Play className="w-4 h-4 mr-2" />
              Start Anonymization
            </Button>
          ) : run.status === AnonymizationStatus.RUNNING ? (
            <Button variant="outline" onClick={handleStop}>
              <Square className="w-4 h-4 mr-2" />
              Stop
            </Button>
          ) : null}
        </div>
      </div>

      {/* Database Connection Visualization */}
      <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
        <h2 className="text-lg font-semibold text-gray-900 mb-6">Data Flow</h2>
        <div className="flex items-center justify-between">
          {/* Source Database */}
          <div className="flex-1">
            <div className="bg-gray-50 rounded-xl p-6 border-2 border-gray-200">
              <div className="flex items-center space-x-3 mb-4">
                <Database className="w-8 h-8 text-primary-600" />
                <div>
                  <div className="font-semibold text-gray-900">Source Database</div>
                  <div className="text-sm text-gray-500">{run.sourceDatabase}</div>
                </div>
              </div>
              <Badge variant="info">READ ONLY</Badge>
            </div>
          </div>

          {/* Animated Pipeline */}
          <div className="flex-1 px-8">
            <div className="relative">
              <div className="h-1 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={`h-full bg-gradient-to-r from-primary-500 to-accent-500 transition-all duration-1000 ${
                    run.status === AnonymizationStatus.RUNNING ? 'animate-pulse' : ''
                  }`}
                  style={{ width: `${(run.rowsProcessed / run.totalRows) * 100}%` }}
                />
              </div>
              <div className="text-center mt-2">
                <span className="text-sm font-medium text-gray-900">
                  {Math.round((run.rowsProcessed / run.totalRows) * 100)}%
                </span>
              </div>
            </div>
          </div>

          {/* Destination Database */}
          <div className="flex-1">
            <div className="bg-gray-50 rounded-xl p-6 border-2 border-gray-200">
              <div className="flex items-center space-x-3 mb-4">
                <Database className="w-8 h-8 text-green-600" />
                <div>
                  <div className="font-semibold text-gray-900">Destination Database</div>
                  <div className="text-sm text-gray-500">{run.destinationDatabase}</div>
                </div>
              </div>
              <Badge variant="success">WRITABLE</Badge>
            </div>
          </div>
        </div>
      </div>

      {/* Progress Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
          <div className="text-sm text-gray-500 mb-2">Rows Processed</div>
          <div className="text-2xl font-bold text-gray-900">
            {run.rowsProcessed.toLocaleString()} / {run.totalRows.toLocaleString()}
          </div>
        </div>
        <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
          <div className="text-sm text-gray-500 mb-2">Current Table</div>
          <div className="text-2xl font-bold text-gray-900">{run.currentTable}</div>
        </div>
        <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
          <div className="text-sm text-gray-500 mb-2">Processing Rate</div>
          <div className="text-2xl font-bold text-gray-900">{run.processingRate.toLocaleString()} rows/sec</div>
        </div>
        <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
          <div className="text-sm text-gray-500 mb-2">Failed Chunks</div>
          <div className="text-2xl font-bold text-gray-900">{run.failedChunks}</div>
        </div>
      </div>

      {/* Table Progress */}
      <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Table Progress</h2>
        <div className="space-y-4">
          {run.tables.map((table) => (
            <div key={table.name}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-3">
                  <div className={getTableStatusColor(table.status)}>
                    {getTableStatusIcon(table.status)}
                  </div>
                  <span className="font-medium text-gray-900">{table.name}</span>
                </div>
                <div className="text-sm text-gray-600">
                  {table.rowsProcessed.toLocaleString()} / {table.totalRows.toLocaleString()}
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all ${
                    table.status === 'COMPLETED' ? 'bg-green-500' : table.status === 'IN_PROGRESS' ? 'bg-primary-500' : 'bg-gray-300'
                  }`}
                  style={{ width: `${table.progress}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* System Health */}
      <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">System Health</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <div>
              <div className="text-sm font-medium text-gray-900">Redis Mapping</div>
              <div className="text-xs text-gray-500">{run.systemHealth.redisMapping}</div>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <div>
              <div className="text-sm font-medium text-gray-900">Source Database</div>
              <div className="text-xs text-gray-500">{run.systemHealth.sourceDatabase} / Read Only</div>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <div>
              <div className="text-sm font-medium text-gray-900">Destination Database</div>
              <div className="text-xs text-gray-500">{run.systemHealth.destinationDatabase}</div>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <div>
              <div className="text-sm font-medium text-gray-900">Relationships</div>
              <div className="text-xs text-gray-500">{run.systemHealth.relationships}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Live Activity Timeline */}
      <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Live Activity</h2>
        <div className="space-y-3">
          {run.activityLog.map((log, index) => (
            <div key={index} className="flex items-start space-x-3">
              <div
                className={`w-2 h-2 rounded-full mt-2 ${
                  log.type === 'SUCCESS' ? 'bg-green-500' : log.type === 'ERROR' ? 'bg-red-500' : 'bg-primary-500'
                }`}
              />
              <div className="flex-1">
                <div className="text-sm text-gray-900">{log.message}</div>
                <div className="text-xs text-gray-500">
                  {new Date(log.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
