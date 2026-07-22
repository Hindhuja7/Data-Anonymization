'use client';

import React from 'react';
import { Container } from '@/components/ui/container';
import { Check } from 'lucide-react';

export const TrustStrip = () => {
  const features = [
    'Read-only source connection',
    'AI + Regex PII detection',
    'Admin-controlled policies',
    'Consistent secure mappings',
    'Relationship preservation',
    'Separate anonymized database',
  ];

  return (
    <section className="py-12 bg-white border-b border-gray-200">
      <Container>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
          {features.map((feature, index) => (
            <div
              key={index}
              className="flex items-center space-x-2 text-sm text-gray-600"
            >
              <Check className="w-4 h-4 text-green-500 flex-shrink-0" />
              <span>{feature}</span>
            </div>
          ))}
        </div>
      </Container>
    </section>
  );
};
