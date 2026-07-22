'use client';

import React, { useState } from 'react';
import { Search, Filter, ArrowRight, Eye, EyeOff, X, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { mockDiscoveryResult, mockPIIColumns } from '@/lib/mock-data';
import { PIIType, DetectionMethod, AnonymizationTechnique } from '@/lib/types';

const getPIIBadgeColor = (piiType: PIIType) => {
  switch (piiType) {
    case PIIType.FULL_NAME:
      return 'bg-purple-100 text-purple-700';
    case PIIType.EMAIL:
      return 'bg-blue-100 text-blue-700';
    case PIIType.PHONE:
    case PIIType.INDIAN_PHONE:
      return 'bg-green-100 text-green-700';
    case PIIType.AADHAAR:
      return 'bg-red-100 text-red-700';
    case PIIType.PAN:
      return 'bg-orange-100 text-orange-700';
    case PIIType.LOCATION:
      return 'bg-yellow-100 text-yellow-700';
    case PIIType.FINANCIAL:
      return 'bg-pink-100 text-pink-700';
    default:
      return 'bg-gray-100 text-gray-700';
  }
};

const getDetectionMethodBadge = (method: DetectionMethod) => {
  switch (method) {
    case DetectionMethod.AI:
      return 'bg-purple-50 text-purple-600';
    case DetectionMethod.REGEX:
      return 'bg-blue-50 text-blue-600';
    case DetectionMethod.AI_REGEX:
      return 'bg-indigo-50 text-indigo-600';
    default:
      return 'bg-gray-50 text-gray-600';
  }
};

const maskValue = (value: string, piiType: PIIType) => {
  if (piiType === PIIType.EMAIL) {
    const [local, domain] = value.split('@');
    return `${local.substring(0, 2)}****@${domain}`;
  }
  if (piiType === PIIType.PHONE || piiType === PIIType.INDIAN_PHONE) {
    return value.replace(/\d(?=\d{4})/g, '*');
  }
  if (piiType === PIIType.AADHAAR) {
    return value.substring(0, 8) + 'XXXX';
  }
  if (piiType === PIIType.PAN) {
    return value.substring(0, 5) + 'XXXX';
  }
  if (piiType === PIIType.FULL_NAME) {
    return value.split(' ').map((n) => n.substring(0, 2) + '*****').join(' ');
  }
  return value.substring(0, 3) + '****';
};

export default function PIIDiscoveryPage() {
  const [selectedTable, setSelectedTable] = useState<string>('all');
  const [selectedColumn, setSelectedColumn] = useState<typeof mockPIIColumns[0] | null>(null);
  const [showOriginal, setShowOriginal] = useState(false);
  const [filterPIIOnly, setFilterPIIOnly] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  const filteredColumns = mockPIIColumns.filter((col) => {
    const matchesTable = selectedTable === 'all' || col.table === selectedTable;
    const matchesSearch = col.column.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesPII = !filterPIIOnly || col.piiType !== PIIType.NON_PII;
    return matchesTable && matchesSearch && matchesPII;
  });

  return (
    <div className="flex h-[calc(100vh-64px)]">
      {/* Left Panel - Tables */}
      <div className="w-64 bg-white border-r border-gray-200 p-4 overflow-y-auto">
        <h2 className="text-sm font-semibold text-gray-900 mb-4">Tables</h2>
        <div className="space-y-2">
          <button
            onClick={() => setSelectedTable('all')}
            className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
              selectedTable === 'all' ? 'bg-primary-50 text-primary-700' : 'hover:bg-gray-50'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="font-medium">All Tables</span>
              <Badge variant="default" className="text-xs">
                {mockDiscoveryResult.tables.reduce((acc, t) => acc + t.piiCount, 0)}
              </Badge>
            </div>
          </button>
          {mockDiscoveryResult.tables.map((table) => (
            <button
              key={table.name}
              onClick={() => setSelectedTable(table.name)}
              className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                selectedTable === table.name ? 'bg-primary-50 text-primary-700' : 'hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-medium">{table.name}</span>
                <Badge variant="default" className="text-xs">
                  {table.piiCount} PII
                </Badge>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Main Panel - Columns Table */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">PII Discovery</h1>
              <p className="text-gray-600 mt-1">
                {mockDiscoveryResult.piiColumns} Sensitive Fields Found Across {mockDiscoveryResult.tables.length} Tables
              </p>
            </div>
            <Button>
              Generate Protection Policy
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>

          {/* Filters */}
          <div className="flex items-center space-x-4 mb-6">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search columns..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-gray-400" />
              <label className="flex items-center space-x-2 text-sm">
                <input
                  type="checkbox"
                  checked={filterPIIOnly}
                  onChange={(e) => setFilterPIIOnly(e.target.checked)}
                  className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                />
                <span>PII Only</span>
              </label>
            </div>
          </div>

          {/* Columns Table */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Column Name</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Data Type</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">PII Classification</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Confidence</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Detected By</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Recommended Technique</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredColumns.map((col) => (
                  <tr
                    key={`${col.table}-${col.column}`}
                    onClick={() => setSelectedColumn(col)}
                    className="hover:bg-gray-50 cursor-pointer transition-colors"
                  >
                    <td className="px-4 py-3">
                      <div>
                        <div className="font-medium text-gray-900">{col.column}</div>
                        <div className="text-xs text-gray-500">{col.table}</div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">{col.dataType}</td>
                    <td className="px-4 py-3">
                      <Badge className={getPIIBadgeColor(col.piiType)}>{col.piiType}</Badge>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center space-x-2">
                        <div className="w-16 bg-gray-200 rounded-full h-1.5">
                          <div
                            className={`h-1.5 rounded-full ${col.confidence > 0.8 ? 'bg-green-500' : col.confidence > 0.6 ? 'bg-yellow-500' : 'bg-red-500'}`}
                            style={{ width: `${col.confidence * 100}%` }}
                          />
                        </div>
                        <span className="text-sm text-gray-600">{Math.round(col.confidence * 100)}%</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <Badge className={getDetectionMethodBadge(col.detectedBy)}>{col.detectedBy}</Badge>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">{col.recommendedTechnique}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Right Drawer - Column Details */}
      {selectedColumn && (
        <div className="w-96 bg-white border-l border-gray-200 p-6 overflow-y-auto">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-gray-900">Column Details</h2>
            <button
              onClick={() => setSelectedColumn(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Basic Info */}
          <div className="space-y-4 mb-6">
            <div>
              <div className="text-sm text-gray-500 mb-1">Column</div>
              <div className="font-medium text-gray-900">{selectedColumn.column}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500 mb-1">Table</div>
              <div className="font-medium text-gray-900">{selectedColumn.table}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500 mb-1">Data Type</div>
              <div className="font-medium text-gray-900">{selectedColumn.dataType}</div>
            </div>
          </div>

          {/* Classification */}
          <div className="border-t border-gray-200 pt-4 mb-6">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Classification</h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">PII Type</span>
                <Badge className={getPIIBadgeColor(selectedColumn.piiType)}>{selectedColumn.piiType}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Confidence</span>
                <span className="text-sm font-medium text-gray-900">{Math.round(selectedColumn.confidence * 100)}%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Detected By</span>
                <Badge className={getDetectionMethodBadge(selectedColumn.detectedBy)}>{selectedColumn.detectedBy}</Badge>
              </div>
            </div>
          </div>

          {/* Detection Evidence */}
          <div className="border-t border-gray-200 pt-4 mb-6">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Detection Evidence</h3>
            <div className="space-y-2 text-sm text-gray-600">
              <div>
                <span className="font-medium">LLM Result:</span> {selectedColumn.detectedBy === DetectionMethod.AI || selectedColumn.detectedBy === DetectionMethod.AI_REGEX ? 'Detected as PII' : 'N/A'}
              </div>
              <div>
                <span className="font-medium">Regex Result:</span> {selectedColumn.detectedBy === DetectionMethod.REGEX || selectedColumn.detectedBy === DetectionMethod.AI_REGEX ? 'Pattern matched' : 'N/A'}
              </div>
              <div>
                <span className="font-medium">Reason:</span> {selectedColumn.reason}
              </div>
            </div>
          </div>

          {/* Recommended Technique */}
          <div className="border-t border-gray-200 pt-4 mb-6">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Recommended Anonymization</h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Technique</span>
                <span className="text-sm font-medium text-gray-900">{selectedColumn.recommendedTechnique}</span>
              </div>
            </div>
          </div>

          {/* Example Transformation */}
          <div className="border-t border-gray-200 pt-4 mb-6">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Example Transformation</h3>
            {selectedColumn.sampleValues && selectedColumn.sampleValues.length > 0 && (
              <div className="space-y-3">
                {selectedColumn.sampleValues.slice(0, 2).map((value, index) => (
                  <div key={index} className="bg-gray-50 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-gray-500">Original</span>
                      <button
                        onClick={() => setShowOriginal(!showOriginal)}
                        className="text-xs text-primary-600 hover:text-primary-700"
                      >
                        {showOriginal ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                      </button>
                    </div>
                    <div className="text-sm font-mono text-gray-900">
                      {showOriginal ? value : maskValue(value, selectedColumn.piiType)}
                    </div>
                    <div className="mt-2">
                      <span className="text-xs text-gray-500">Protected</span>
                      <div className="text-sm font-mono text-green-700">
                        {maskValue(value, selectedColumn.piiType)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* PK/FK Info */}
          <div className="border-t border-gray-200 pt-4">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Key Information</h3>
            <div className="space-y-2">
              {selectedColumn.isPrimaryKey && (
                <div className="flex items-center space-x-2">
                  <Badge variant="info">Primary Key</Badge>
                </div>
              )}
              {selectedColumn.isForeignKey && (
                <div className="flex items-center space-x-2">
                  <Badge variant="info">Foreign Key</Badge>
                </div>
              )}
              {!selectedColumn.isPrimaryKey && !selectedColumn.isForeignKey && (
                <span className="text-sm text-gray-500">Not a key column</span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
