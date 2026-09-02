'use client';

import React, { useState } from 'react';
import { Shield, CheckCircle, XCircle, Edit, X, ChevronRight, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { mockPolicy } from '@/lib/mock-data';
import { PolicyStatus, AnonymizationTechnique, PIIType } from '@/lib/types';

const getPolicyStatusColor = (status: PolicyStatus) => {
  switch (status) {
    case PolicyStatus.APPROVED:
      return 'bg-green-100 text-green-700';
    case PolicyStatus.REJECTED:
      return 'bg-red-100 text-red-700';
    case PolicyStatus.DRAFT:
    default:
      return 'bg-yellow-100 text-yellow-700';
  }
};

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

export default function PolicyStudioPage() {
  const [policy, setPolicy] = useState(mockPolicy);
  const [selectedColumn, setSelectedColumn] = useState<typeof policy.columns[0] | null>(null);
  const [newTechnique, setNewTechnique] = useState<AnonymizationTechnique>(AnonymizationTechnique.TOKENIZATION);
  const [showOverrideModal, setShowOverrideModal] = useState(false);
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [overrideReason, setOverrideReason] = useState('');
  const [approvalComments, setApprovalComments] = useState('');

  const handleOverride = () => {
    if (selectedColumn && overrideReason) {
      setPolicy({
        ...policy,
        columns: policy.columns.map((col) =>
          col.table === selectedColumn.table && col.column === selectedColumn.column
            ? { ...col, currentTechnique: newTechnique, overrideStatus: 'OVERRIDDEN', overrideReason }
            : col
        ),
        overrideCount: policy.overrideCount + 1,
      });
      setShowOverrideModal(false);
      setOverrideReason('');
      setSelectedColumn(null);
    }
  };

  const handleApprove = () => {
    setPolicy({
      ...policy,
      status: PolicyStatus.APPROVED,
      approvedBy: 'Admin User',
      approvedAt: new Date().toISOString(),
    });
    setShowApprovalModal(false);
  };

  const handleReject = () => {
    setPolicy({
      ...policy,
      status: PolicyStatus.REJECTED,
    });
  };

  const openOverrideModal = (column: typeof policy.columns[0]) => {
    setSelectedColumn(column);
    setNewTechnique(column.currentTechnique);
    setShowOverrideModal(true);
  };

  const techniqueOptions: AnonymizationTechnique[] = [
    AnonymizationTechnique.NO_CHANGE,
    AnonymizationTechnique.TOKENIZATION,
    AnonymizationTechnique.MASKING,
    AnonymizationTechnique.HASHING,
    AnonymizationTechnique.DIFFERENTIAL_PRIVACY,
    AnonymizationTechnique.REDACTION,
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Policy Studio</h1>
          <p className="text-gray-600 mt-1">Review and approve anonymization policies</p>
        </div>
        <Badge className={getPolicyStatusColor(policy.status)} variant="default">
          {policy.status}
        </Badge>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
          <div className="text-sm text-gray-500 mb-2">Total Columns</div>
          <div className="text-3xl font-bold text-gray-900">{policy.totalColumns}</div>
        </div>
        <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
          <div className="text-sm text-gray-500 mb-2">PII Columns</div>
          <div className="text-3xl font-bold text-gray-900">{policy.piiColumns}</div>
        </div>
        <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
          <div className="text-sm text-gray-500 mb-2">No Change</div>
          <div className="text-3xl font-bold text-gray-900">{policy.noChangeCount}</div>
        </div>
        <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
          <div className="text-sm text-gray-500 mb-2">Overrides</div>
          <div className="text-3xl font-bold text-gray-900">{policy.overrideCount}</div>
        </div>
      </div>

      {/* Policy Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Column Policies</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Table</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Column</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">PII Type</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Confidence</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Recommended</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Current</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Override</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {policy.columns.map((col) => (
                <tr key={`${col.table}-${col.column}`} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm text-gray-900">{col.table}</td>
                  <td className="px-4 py-3 text-sm text-gray-900">{col.column}</td>
                  <td className="px-4 py-3">
                    <Badge variant="default" className="text-xs">{col.piiType}</Badge>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{Math.round(col.confidence * 100)}%</td>
                  <td className="px-4 py-3">
                    <Badge className={getTechniqueBadgeColor(col.recommendedTechnique)}>{col.recommendedTechnique}</Badge>
                  </td>
                  <td className="px-4 py-3">
                    <Badge className={getTechniqueBadgeColor(col.currentTechnique)}>{col.currentTechnique}</Badge>
                  </td>
                  <td className="px-4 py-3">
                    {col.overrideStatus === 'OVERRIDDEN' ? (
                      <Badge variant="warning">Overridden</Badge>
                    ) : (
                      <span className="text-sm text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => openOverrideModal(col)}
                      className="text-primary-600 hover:text-primary-700 text-sm font-medium"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-between">
        <Button variant="outline" onClick={handleReject} className="text-red-600 hover:text-red-700 hover:bg-red-50">
          <XCircle className="w-4 h-4 mr-2" />
          Reject Policy
        </Button>
        <Button
          onClick={() => setShowApprovalModal(true)}
          disabled={policy.status === PolicyStatus.APPROVED}
        >
          <CheckCircle className="w-4 h-4 mr-2" />
          Approve Policy
        </Button>
      </div>

      {/* Override Modal */}
      {showOverrideModal && selectedColumn && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Override Technique</h3>
              <button
                onClick={() => {
                  setShowOverrideModal(false);
                  setOverrideReason('');
                  setSelectedColumn(null);
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Column</label>
                <div className="text-sm text-gray-900">{selectedColumn.table}.{selectedColumn.column}</div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Original Recommendation</label>
                <Badge className={getTechniqueBadgeColor(selectedColumn.recommendedTechnique)}>
                  {selectedColumn.recommendedTechnique}
                </Badge>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">New Technique</label>
                <select
                  value={newTechnique}
                  onChange={(e) => setNewTechnique(e.target.value as AnonymizationTechnique)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  {techniqueOptions.map((technique) => (
                    <option key={technique} value={technique}>
                      {technique}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Reason for Override</label>
                <textarea
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="Explain why you are changing the recommended technique..."
                  required
                />
              </div>
            </div>

            <div className="flex justify-end space-x-3">
              <Button
                variant="outline"
                onClick={() => {
                  setShowOverrideModal(false);
                  setOverrideReason('');
                  setSelectedColumn(null);
                }}
              >
                Cancel
              </Button>
              <Button onClick={handleOverride} disabled={!overrideReason}>
                Save Override
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Approval Modal */}
      {showApprovalModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Approve Policy</h3>
              <button
                onClick={() => setShowApprovalModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="mb-4">
              <p className="text-gray-600 mb-4">Are you sure you want to approve this anonymization policy?</p>
              
              <div className="bg-gray-50 rounded-lg p-4 space-y-2 mb-4">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">PII Columns</span>
                  <span className="font-medium text-gray-900">{policy.piiColumns}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Admin Overrides</span>
                  <span className="font-medium text-gray-900">{policy.overrideCount}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Tokenized</span>
                  <span className="font-medium text-gray-900">
                    {policy.columns.filter(c => c.currentTechnique === AnonymizationTechnique.TOKENIZATION).length}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Masked</span>
                  <span className="font-medium text-gray-900">
                    {policy.columns.filter(c => c.currentTechnique === AnonymizationTechnique.MASKING).length}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Hashed</span>
                  <span className="font-medium text-gray-900">
                    {policy.columns.filter(c => c.currentTechnique === AnonymizationTechnique.HASHING).length}
                  </span>
                </div>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Approval Comments</label>
                <textarea
                  value={approvalComments}
                  onChange={(e) => setApprovalComments(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="Add any notes about this approval..."
                />
              </div>
            </div>

            <div className="flex justify-end space-x-3">
              <Button variant="outline" onClick={() => setShowApprovalModal(false)}>
                Cancel
              </Button>
              <Button onClick={handleApprove}>
                Approve & Continue
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
