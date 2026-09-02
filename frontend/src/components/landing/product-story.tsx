'use client';

import React from 'react';
import { Container } from '@/components/ui/container';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Brain, Shield as ShieldIcon, Zap, Link2 } from 'lucide-react';

const stories = [
  {
    icon: Brain,
    title: 'AI-Powered PII Discovery',
    description: 'Know where sensitive data lives.',
    content: (
      <div className="space-y-4">
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <div className="text-sm font-semibold text-gray-500 mb-3">customers</div>
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm font-mono">full_name</span>
              <div className="flex items-center space-x-2">
                <Badge variant="info">FULL_NAME</Badge>
                <Badge variant="success">99%</Badge>
              </div>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm font-mono">email</span>
              <div className="flex items-center space-x-2">
                <Badge variant="info">EMAIL</Badge>
                <Badge variant="success">98%</Badge>
              </div>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm font-mono">phone</span>
              <div className="flex items-center space-x-2">
                <Badge variant="info">PHONE</Badge>
                <Badge variant="success">98%</Badge>
              </div>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm font-mono">aadhaar</span>
              <div className="flex items-center space-x-2">
                <Badge variant="info">AADHAAR</Badge>
                <Badge variant="success">100%</Badge>
              </div>
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-2 text-sm text-gray-600">
          <Badge variant="success">Detected by AI</Badge>
          <Badge variant="info">Regex Verified</Badge>
          <Badge variant="warning">Confidence 99%</Badge>
        </div>
      </div>
    ),
  },
  {
    icon: ShieldIcon,
    title: 'Policy Governance',
    description: 'AI recommends. You stay in control.',
    content: (
      <div className="space-y-4">
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <div className="text-sm font-semibold text-gray-500 mb-3">Policy Studio</div>
          <div className="space-y-3">
            <div className="flex justify-between items-center p-2 bg-white rounded border border-gray-200">
              <div>
                <div className="text-sm font-medium">full_name</div>
                <div className="text-xs text-gray-500">FULL_NAME • 99% confidence</div>
              </div>
              <Badge variant="info">TOKENIZATION</Badge>
            </div>
            <div className="flex justify-between items-center p-2 bg-white rounded border border-gray-200">
              <div>
                <div className="text-sm font-medium">aadhaar</div>
                <div className="text-xs text-gray-500">AADHAAR • 100% confidence</div>
              </div>
              <Badge variant="info">MASKING</Badge>
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-2 text-sm text-gray-600">
          <span className="text-green-600">✓</span> Review detected PII
          <span className="text-green-600">✓</span> Override techniques
          <span className="text-green-600">✓</span> Approve policy
        </div>
      </div>
    ),
  },
  {
    icon: Zap,
    title: 'Secure Transformation',
    description: 'Protect millions of records without loading them all into memory.',
    content: (
      <div className="space-y-4">
        <div className="flex items-center justify-between space-x-2">
          <div className="flex-1 bg-gray-50 rounded-lg p-3 border border-gray-200 text-center">
            <div className="text-xs text-gray-500 mb-1">Source DB</div>
            <div className="text-sm font-semibold">Production</div>
          </div>
          <div className="text-gray-400">↓</div>
          <div className="flex-1 bg-primary-50 rounded-lg p-3 border border-primary-200 text-center">
            <div className="text-xs text-gray-500 mb-1">Chunk Processing</div>
            <div className="text-sm font-semibold">1K rows</div>
          </div>
          <div className="text-gray-400">↓</div>
          <div className="flex-1 bg-accent-50 rounded-lg p-3 border border-accent-200 text-center">
            <div className="text-xs text-gray-500 mb-1">Policy Engine</div>
            <div className="text-sm font-semibold">Apply Rules</div>
          </div>
        </div>
        <div className="flex items-center justify-between space-x-2">
          <div className="flex-1 bg-cyan-50 rounded-lg p-3 border border-cyan-200 text-center">
            <div className="text-xs text-gray-500 mb-1">Redis Mapping</div>
            <div className="text-sm font-semibold">Consistent</div>
          </div>
          <div className="text-gray-400">↓</div>
          <div className="flex-1 bg-cyan-50 rounded-lg p-3 border border-cyan-200 text-center">
            <div className="text-xs text-gray-500 mb-1">Anonymization</div>
            <div className="text-sm font-semibold">Transform</div>
          </div>
          <div className="text-gray-400">↓</div>
          <div className="flex-1 bg-green-50 rounded-lg p-3 border border-green-200 text-center">
            <div className="text-xs text-gray-500 mb-1">Destination DB</div>
            <div className="text-sm font-semibold">Safe Data</div>
          </div>
        </div>
      </div>
    ),
  },
  {
    icon: Link2,
    title: 'Relationship Preservation',
    description: 'Maintain referential integrity while protecting PII.',
    content: (
      <div className="space-y-4">
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="text-sm font-mono">customers.customer_id</div>
              <div className="text-gray-400">↓</div>
              <div className="text-sm font-mono">accounts.customer_id</div>
            </div>
            <div className="flex items-center justify-between">
              <div className="text-sm font-mono">accounts.account_id</div>
              <div className="text-gray-400">↓</div>
              <div className="text-sm font-mono">transactions.account_id</div>
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-2 text-sm text-green-600 font-medium">
          <span className="text-lg">✓</span>
          <span>Relationships preserved</span>
        </div>
        <p className="text-xs text-gray-600">
          Technical IDs remain consistent while sensitive PII is transformed
        </p>
      </div>
    ),
  },
];

export const ProductStory = () => {
  return (
    <section className="py-24 bg-white" id="product">
      <Container>
        <div className="text-center mb-16">
          <h2 className="text-4xl lg:text-5xl font-bold mb-4">
            Built for enterprise privacy compliance
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Every component designed for DPDP Act 2023 compliance and production reliability.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          {stories.map((story, index) => (
            <Card key={index} className="h-full">
              <CardHeader>
                <div className="flex items-center space-x-3 mb-2">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
                    <story.icon className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold">{story.title}</h3>
                    <p className="text-sm text-gray-600">{story.description}</p>
                  </div>
                </div>
              </CardHeader>
              <CardContent>{story.content}</CardContent>
            </Card>
          ))}
        </div>
      </Container>
    </section>
  );
};
