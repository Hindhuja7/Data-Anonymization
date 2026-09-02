'use client';

import React, { useState } from 'react';
import { Container } from '@/components/ui/container';
import { motion } from 'framer-motion';
import { Database, Search, Shield, Lock, CheckCircle } from 'lucide-react';

const phases = [
  {
    name: 'CONNECT',
    icon: Database,
    color: 'from-gray-500 to-gray-600',
    bgColor: 'bg-gray-50',
    borderColor: 'border-gray-200',
    steps: [
      'Database connection',
      'Schema extraction',
      'Sample extraction',
      'Enterprise detection',
    ],
  },
  {
    name: 'DISCOVER',
    icon: Search,
    color: 'from-primary-500 to-primary-600',
    bgColor: 'bg-primary-50',
    borderColor: 'border-primary-200',
    steps: [
      'Privacy-safe sampling',
      'LLM detection',
      'Regex detection',
      'Combined PII classification',
    ],
  },
  {
    name: 'GOVERN',
    icon: Shield,
    color: 'from-accent-500 to-accent-600',
    bgColor: 'bg-accent-50',
    borderColor: 'border-accent-200',
    steps: [
      'Policy generation',
      'Admin review',
      'Overrides',
      'Approval',
    ],
  },
  {
    name: 'PROTECT',
    icon: Lock,
    color: 'from-cyan-500 to-cyan-600',
    bgColor: 'bg-cyan-50',
    borderColor: 'border-cyan-200',
    steps: [
      'Change processing',
      'Redis consistent mapping',
      'Chunk processing',
      'Anonymization',
      'Destination database writing',
    ],
  },
  {
    name: 'ASSURE',
    icon: CheckCircle,
    color: 'from-green-500 to-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    steps: [
      'Validation',
      'Privacy risk assessment',
      'Audit report',
      'Admin outputs',
    ],
  },
];

export const FivePhasePipeline = () => {
  const [activePhase, setActivePhase] = useState(0);

  return (
    <section className="py-24 bg-white" id="how-it-works">
      <Container>
        <div className="text-center mb-16">
          <h2 className="text-4xl lg:text-5xl font-bold mb-4">
            Connect. Discover. Govern. Protect. Assure.
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Our five-phase pipeline transforms sensitive production data into privacy-safe datasets
            while preserving the relationships your applications depend on.
          </p>
        </div>

        {/* Phase Cards */}
        <div className="grid md:grid-cols-5 gap-4 mb-8">
          {phases.map((phase, index) => (
            <motion.div
              key={phase.name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              onClick={() => setActivePhase(index)}
              className={`cursor-pointer transition-all ${
                activePhase === index
                  ? 'transform scale-105 shadow-lg'
                  : 'hover:shadow-md'
              }`}
            >
              <div
                className={`p-6 rounded-xl border-2 ${phase.bgColor} ${phase.borderColor} ${
                  activePhase === index ? 'border-current' : ''
                }`}
              >
                <div className={`w-12 h-12 rounded-lg bg-gradient-to-br ${phase.color} flex items-center justify-center mb-4`}>
                  {React.createElement(phase.icon, { className: 'w-6 h-6 text-white' })}
                </div>
                <h3 className="font-bold text-lg mb-2">{phase.name}</h3>
                <p className="text-sm text-gray-600">{phase.steps.length} steps</p>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Active Phase Details */}
        <motion.div
          key={activePhase}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-br from-gray-50 to-white rounded-2xl p-8 border border-gray-200"
        >
          <div className="flex items-start space-x-4 mb-6">
            <div
              className={`w-16 h-16 rounded-xl bg-gradient-to-br ${phases[activePhase].color} flex items-center justify-center flex-shrink-0`}
            >
              {React.createElement(phases[activePhase].icon, { className: 'w-8 h-8 text-white' })}
            </div>
            <div>
              <h3 className="text-2xl font-bold mb-2">{phases[activePhase].name}</h3>
              <p className="text-gray-600">
                {phases[activePhase].name === 'CONNECT' &&
                  'Establish secure read-only connections to your source database and extract schema metadata.'}
                {phases[activePhase].name === 'DISCOVER' &&
                  'Use AI-powered LLM detection combined with India-specific regex patterns to identify PII across your database.'}
                {phases[activePhase].name === 'GOVERN' &&
                  'Generate anonymization policies with AI recommendations, allow admin overrides, and enforce approval workflows.'}
                {phases[activePhase].name === 'PROTECT' &&
                  'Process data in secure chunks with Redis-based consistent mapping, ensuring referential integrity is preserved.'}
                {phases[activePhase].name === 'ASSURE' &&
                  'Validate anonymized data with privacy risk scoring, run penetration tests, and generate compliance audit reports.'}
              </p>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            {phases[activePhase].steps.map((step, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className="flex items-center space-x-3 p-3 bg-white rounded-lg border border-gray-200"
              >
                <div
                  className={`w-8 h-8 rounded-full bg-gradient-to-br ${phases[activePhase].color} flex items-center justify-center flex-shrink-0`}
                >
                  <span className="text-white text-sm font-bold">{index + 1}</span>
                </div>
                <span className="text-sm font-medium text-gray-700">{step}</span>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </Container>
    </section>
  );
};
