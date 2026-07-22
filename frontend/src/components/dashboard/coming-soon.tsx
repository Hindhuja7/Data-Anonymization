'use client';

import React from 'react';
import { Clock, Calendar } from 'lucide-react';

export const ComingSoon = ({ featureName, description }: { featureName: string; description?: string }) => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] text-center">
      <div className="w-20 h-20 rounded-full bg-gradient-to-br from-primary-100 to-accent-100 flex items-center justify-center mb-6">
        <Clock className="w-10 h-10 text-primary-600" />
      </div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Coming Soon</h2>
      <p className="text-gray-600 mb-4 max-w-md">
        {description || `${featureName} will be available in the next phase of DataGuard.`}
      </p>
      <div className="flex items-center space-x-2 text-sm text-gray-500">
        <Calendar className="w-4 h-4" />
        <span>Planned for Phase 3</span>
      </div>
    </div>
  );
};
