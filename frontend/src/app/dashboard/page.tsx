'use client';

import React from 'react';
import { Database, Search, Shield, Lock, CheckCircle, ArrowRight, Play } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { mockRecentActivity, mockWorkflowPhases } from '@/lib/mock-data';
import { PhaseStatus } from '@/lib/types';

const getStatusColor = (status: PhaseStatus) => {
  switch (status) {
    case PhaseStatus.COMPLETED:
      return 'bg-green-500';
    case PhaseStatus.IN_PROGRESS:
      return 'bg-primary-500';
    case PhaseStatus.REQUIRES_REVIEW:
      return 'bg-yellow-500';
    default:
      return 'bg-gray-300';
  }
};

const getStatusText = (status: PhaseStatus) => {
  switch (status) {
    case PhaseStatus.COMPLETED:
      return 'Completed';
    case PhaseStatus.IN_PROGRESS:
      return 'In Progress';
    case PhaseStatus.REQUIRES_REVIEW:
      return 'Requires Review';
    default:
      return 'Not Started';
  }
};

export default function DashboardOverview() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard Overview</h1>
        <p className="text-gray-600 mt-1">Control center for your data privacy pipeline</p>
      </div>

      {/* Top Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <Database className="w-5 h-5 text-primary-600" />
            <span className="text-xs font-medium text-green-600 bg-green-50 px-2 py-1 rounded-full">Connected</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">1</div>
          <div className="text-sm text-gray-500 mt-1">Connected Data Sources</div>
        </div>
        <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <Search className="w-5 h-5 text-accent-600" />
            <span className="text-xs font-medium text-green-600 bg-green-50 px-2 py-1 rounded-full">Scanned</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">4</div>
          <div className="text-sm text-gray-500 mt-1">Tables Scanned</div>
        </div>
        <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <Shield className="w-5 h-5 text-cyan-600" />
            <span className="text-xs font-medium text-yellow-600 bg-yellow-50 px-2 py-1 rounded-full">Detected</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">14</div>
          <div className="text-sm text-gray-500 mt-1">PII Fields Detected</div>
        </div>
        <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <Lock className="w-5 h-5 text-green-600" />
            <span className="text-xs font-medium text-green-600 bg-green-50 px-2 py-1 rounded-full">Protected</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">1M</div>
          <div className="text-sm text-gray-500 mt-1">Records Protected</div>
        </div>
      </div>

      {/* Five-Phase Workflow */}
      <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
        <h2 className="text-lg font-semibold text-gray-900 mb-6">Privacy Pipeline Workflow</h2>
        <div className="flex items-center justify-between">
          {mockWorkflowPhases.map((phase, index) => (
            <React.Fragment key={phase.name}>
              <div className="flex flex-col items-center">
                <div className={`w-12 h-12 rounded-full ${getStatusColor(phase.status)} flex items-center justify-center mb-2`}>
                  {phase.status === PhaseStatus.COMPLETED ? (
                    <CheckCircle className="w-6 h-6 text-white" />
                  ) : phase.status === PhaseStatus.IN_PROGRESS ? (
                    <Play className="w-6 h-6 text-white fill-white" />
                  ) : (
                    <span className="text-white font-bold">{index + 1}</span>
                  )}
                </div>
                <div className="text-sm font-medium text-gray-900">{phase.name}</div>
                <div className="text-xs text-gray-500">{getStatusText(phase.status)}</div>
              </div>
              {index < mockWorkflowPhases.length - 1 && (
                <div className={`flex-1 h-0.5 mx-4 ${phase.status === PhaseStatus.COMPLETED ? 'bg-green-500' : 'bg-gray-200'}`} />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Button variant="outline" className="h-auto py-4 px-6 flex items-center justify-between group">
          <div className="flex items-center space-x-3">
            <Database className="w-5 h-5 text-primary-600" />
            <div className="text-left">
              <div className="font-medium">Connect Database</div>
              <div className="text-xs text-gray-500">Add a new data source</div>
            </div>
          </div>
          <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-gray-600 transition-colors" />
        </Button>
        <Button variant="outline" className="h-auto py-4 px-6 flex items-center justify-between group">
          <div className="flex items-center space-x-3">
            <Search className="w-5 h-5 text-accent-600" />
            <div className="text-left">
              <div className="font-medium">Start PII Scan</div>
              <div className="text-xs text-gray-500">Discover sensitive data</div>
            </div>
          </div>
          <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-gray-600 transition-colors" />
        </Button>
        <Button variant="outline" className="h-auto py-4 px-6 flex items-center justify-between group">
          <div className="flex items-center space-x-3">
            <Shield className="w-5 h-5 text-cyan-600" />
            <div className="text-left">
              <div className="font-medium">Review Policy</div>
              <div className="text-xs text-gray-500">Approve anonymization rules</div>
            </div>
          </div>
          <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-gray-600 transition-colors" />
        </Button>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
        <div className="space-y-4">
          {mockRecentActivity.map((activity, index) => (
            <div key={index} className="flex items-start space-x-3">
              <div className={`w-2 h-2 rounded-full mt-2 ${activity.type === 'success' ? 'bg-green-500' : 'bg-primary-500'}`} />
              <div className="flex-1">
                <div className="text-sm text-gray-900">{activity.message}</div>
                <div className="text-xs text-gray-500">{activity.timestamp}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
