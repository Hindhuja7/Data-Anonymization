'use client';

import React, { useState } from 'react';
import { Search, Filter, Eye, EyeOff, Info } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { mockTransformations } from '@/lib/mock-data';
import { AnonymizationTechnique, PIIType } from '@/lib/types';

const getTechniqueBadgeColor = (technique: AnonymizationTechnique) => {
  switch (technique) {
    case AnonymizationTechnique.TOKENIZATION:
      return 'bg-purple-100 text-purple-700';
    case AnonymizationTechnique.MASKING:
      return 'bg-blue-100 text-blue-700';
    case AnonymizationTechnique.HASHING:
      return 'bg-green-100 text-green-700';
    case AnonymizationTechnique.DIFFERENTIAL_PRIVACY:
      return 'bg-orange-100 text-orange-700';
    case AnonymizationTechnique.REDACTION:
      return 'bg-red-100 text-red-700';
    case AnonymizationTechnique.NO_CHANGE:
      return 'bg-gray-100 text-gray-700';
    default:
      return 'bg-gray-100 text-gray-700';
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
  if (piiType === PIIType.FINANCIAL) {
    return value.substring(0, 4) + '****' + value.substring(value.length - 4);
  }
  return value.substring(0, 3) + '****';
};

const getTransformationExplanation = (technique: AnonymizationTechnique, piiType: PIIType) => {
  switch (technique) {
    case AnonymizationTechnique.TOKENIZATION:
      return 'Replaces original values with realistic fake data while preserving format and referential integrity across tables.';
    case AnonymizationTechnique.MASKING:
      return 'Preserves partial recognizability by masking sensitive characters while keeping the data structure intact.';
    case AnonymizationTechnique.HASHING:
      return 'One-way cryptographic transformation ideal for identifiers where the original value is never needed again.';
    case AnonymizationTechnique.DIFFERENTIAL_PRIVACY:
      return 'Adds statistical noise to numerical values to prevent re-identification while maintaining aggregate accuracy.';
    case AnonymizationTechnique.REDACTION:
      return 'Completely removes sensitive values where the data is not needed for analysis.';
    case AnonymizationTechnique.NO_CHANGE:
      return 'Data is left unchanged as it was determined to be non-sensitive.';
    default:
      return 'Standard anonymization technique applied.';
  }
};

export default function TransformationExplorerPage() {
  const [selectedTable, setSelectedTable] = useState<string>('all');
  const [selectedTechnique, setSelectedTechnique] = useState<string>('all');
  const [selectedPIIType, setSelectedPIIType] = useState<string>('all');
  const [showOriginal, setShowOriginal] = useState(false);
  const [selectedRow, setSelectedRow] = useState<typeof mockTransformations[0] | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const tables = Array.from(new Set(mockTransformations.map((t) => t.table)));
  const techniques = Array.from(new Set(mockTransformations.map((t) => t.technique)));
  const piiTypes = Array.from(new Set(mockTransformations.map((t) => t.piiType)));

  const filteredTransformations = mockTransformations.filter((t) => {
    const matchesTable = selectedTable === 'all' || t.table === selectedTable;
    const matchesTechnique = selectedTechnique === 'all' || t.technique === selectedTechnique;
    const matchesPIIType = selectedPIIType === 'all' || t.piiType === selectedPIIType;
    const matchesSearch = t.column.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesTable && matchesTechnique && matchesPIIType && matchesSearch;
  });

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Transformation Explorer</h1>
        <p className="text-gray-600 mt-1">View how your data was protected</p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
        <div className="flex flex-wrap items-center gap-4">
          <div className="relative flex-1 min-w-[200px]">
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
            <select
              value={selectedTable}
              onChange={(e) => setSelectedTable(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="all">All Tables</option>
              {tables.map((table) => (
                <option key={table} value={table}>
                  {table}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <select
              value={selectedTechnique}
              onChange={(e) => setSelectedTechnique(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="all">All Techniques</option>
              {techniques.map((technique) => (
                <option key={technique} value={technique}>
                  {technique}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <select
              value={selectedPIIType}
              onChange={(e) => setSelectedPIIType(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="all">All PII Types</option>
              {piiTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>

          <label className="flex items-center space-x-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={showOriginal}
              onChange={(e) => setShowOriginal(e.target.checked)}
              className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
            />
            <span>Show Original Values</span>
            <Eye className="w-4 h-4 text-gray-400" />
          </label>
        </div>
      </div>

      {/* Security Notice */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <Info className="w-5 h-5 text-yellow-600 mt-0.5" />
          <div>
            <div className="font-medium text-yellow-800">Security Notice</div>
            <div className="text-sm text-yellow-700 mt-1">
              Original PII values are masked by default. Enable "Show Original Values" only when authorized to view sensitive data.
            </div>
          </div>
        </div>
      </div>

      {/* Transformation Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Field</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Original</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Protected</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Technique</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">PII Type</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {filteredTransformations.map((transformation, index) => (
              <tr
                key={index}
                onClick={() => setSelectedRow(transformation)}
                className="hover:bg-gray-50 cursor-pointer transition-colors"
              >
                <td className="px-4 py-3">
                  <div>
                    <div className="font-medium text-gray-900">{transformation.column}</div>
                    <div className="text-xs text-gray-500">{transformation.table}</div>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="font-mono text-sm text-gray-600">
                    {showOriginal ? transformation.original : maskValue(transformation.original, transformation.piiType)}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="font-mono text-sm text-green-700">{transformation.protected}</div>
                </td>
                <td className="px-4 py-3">
                  <Badge className={getTechniqueBadgeColor(transformation.technique)}>{transformation.technique}</Badge>
                </td>
                <td className="px-4 py-3">
                  <Badge variant="default" className="text-xs">{transformation.piiType}</Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Transformation Details Drawer */}
      {selectedRow && (
        <div className="fixed right-0 top-0 h-full w-96 bg-white border-l border-gray-200 shadow-xl p-6 overflow-y-auto">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-gray-900">Transformation Details</h2>
            <button
              onClick={() => setSelectedRow(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              <EyeOff className="w-5 h-5" />
            </button>
          </div>

          <div className="space-y-6">
            {/* Field Info */}
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Field Information</h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Table</span>
                  <span className="text-sm font-medium text-gray-900">{selectedRow.table}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Column</span>
                  <span className="text-sm font-medium text-gray-900">{selectedRow.column}</span>
                </div>
              </div>
            </div>

            {/* Classification */}
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Classification</h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">PII Type</span>
                  <Badge variant="default" className="text-xs">{selectedRow.piiType}</Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Technique</span>
                  <Badge className={getTechniqueBadgeColor(selectedRow.technique)}>{selectedRow.technique}</Badge>
                </div>
              </div>
            </div>

            {/* Transformation */}
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Transformation</h3>
              <div className="space-y-3">
                <div>
                  <span className="text-xs text-gray-500">Original</span>
                  <div className="font-mono text-sm text-gray-600 bg-gray-50 p-2 rounded">
                    {showOriginal ? selectedRow.original : maskValue(selectedRow.original, selectedRow.piiType)}
                  </div>
                </div>
                <div>
                  <span className="text-xs text-gray-500">Protected</span>
                  <div className="font-mono text-sm text-green-700 bg-green-50 p-2 rounded">
                    {selectedRow.protected}
                  </div>
                </div>
              </div>
            </div>

            {/* Explanation */}
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Explanation</h3>
              <div className="space-y-2">
                <div>
                  <span className="text-xs text-gray-500">Detected as</span>
                  <div className="text-sm font-medium text-gray-900">{selectedRow.piiType}</div>
                </div>
                <div>
                  <span className="text-xs text-gray-500">Applied Policy</span>
                  <div className="text-sm font-medium text-gray-900">{selectedRow.technique}</div>
                </div>
                <div>
                  <span className="text-xs text-gray-500">Reason</span>
                  <div className="text-sm text-gray-600">{getTransformationExplanation(selectedRow.technique, selectedRow.piiType)}</div>
                </div>
              </div>
            </div>

            {/* Validation */}
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Validation</h3>
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 rounded-full bg-green-500" />
                  <span className="text-sm text-gray-600">Format Preserved</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 rounded-full bg-green-500" />
                  <span className="text-sm text-gray-600">Data Type Consistent</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 rounded-full bg-green-500" />
                  <span className="text-sm text-gray-600">Referential Integrity Maintained</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
