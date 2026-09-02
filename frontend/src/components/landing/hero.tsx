'use client';

import React from 'react';
import { Button } from '@/components/ui/button';
import { Container } from '@/components/ui/container';
import { ArrowRight, Play } from 'lucide-react';
import { motion } from 'framer-motion';

const transformationExamples = [
  { original: 'Wakeeta Sabharwal', protected: 'Ananya Sharma' },
  { original: '+91 8323378925', protected: '+91 9765432108' },
  { original: '1675 7592 4075', protected: '1675 7592 XXXX' },
];

export const Hero = () => {
  return (
    <section className="pt-32 pb-20 gradient-bg overflow-hidden">
      <Container>
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left Content */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="space-y-8"
          >
            <h1 className="text-5xl lg:text-6xl font-bold leading-tight">
              Make production data{' '}
              <span className="gradient-text">safe to use.</span>
            </h1>
            <p className="text-xl text-gray-600 leading-relaxed">
              Discover sensitive data with AI, apply governed anonymization policies,
              and generate privacy-safe datasets without modifying your source database.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <Button size="lg" className="group">
                Start Protecting Data
                <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Button>
              <Button variant="outline" size="lg">
                <Play className="mr-2 w-5 h-5" />
                Watch How It Works
              </Button>
            </div>
          </motion.div>

          {/* Right Content - Pipeline Visualization */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="relative"
          >
            <div className="bg-white rounded-2xl shadow-2xl p-8 border border-gray-200">
              {/* Pipeline Flow */}
              <div className="space-y-4">
                {/* Production Database */}
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-lg bg-gray-200 flex items-center justify-center">
                      <span className="text-2xl">🗄️</span>
                    </div>
                    <div>
                      <div className="font-semibold text-gray-900">Production Database</div>
                      <div className="text-sm text-gray-500">Source (Read-Only)</div>
                    </div>
                  </div>
                </motion.div>

                {/* Arrow */}
                <div className="flex justify-center">
                  <motion.div
                    animate={{ y: [0, 5, 0] }}
                    transition={{ duration: 2, repeat: Infinity }}
                    className="text-gray-400"
                  >
                    ↓
                  </motion.div>
                </div>

                {/* Discover */}
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 }}
                  className="flex items-center justify-between p-4 bg-primary-50 rounded-lg border border-primary-200"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-lg bg-primary-500 flex items-center justify-center">
                      <span className="text-xl">🔍</span>
                    </div>
                    <div>
                      <div className="font-semibold text-gray-900">Discover</div>
                      <div className="text-sm text-gray-500">AI PII Detection</div>
                    </div>
                  </div>
                </motion.div>

                {/* Arrow */}
                <div className="flex justify-center">
                  <motion.div
                    animate={{ y: [0, 5, 0] }}
                    transition={{ duration: 2, repeat: Infinity, delay: 0.5 }}
                    className="text-gray-400"
                  >
                    ↓
                  </motion.div>
                </div>

                {/* Govern */}
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 }}
                  className="flex items-center justify-between p-4 bg-accent-50 rounded-lg border border-accent-200"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-lg bg-accent-500 flex items-center justify-center">
                      <span className="text-xl">⚖️</span>
                    </div>
                    <div>
                      <div className="font-semibold text-gray-900">Govern</div>
                      <div className="text-sm text-gray-500">Policy Approval</div>
                    </div>
                  </div>
                </motion.div>

                {/* Arrow */}
                <div className="flex justify-center">
                  <motion.div
                    animate={{ y: [0, 5, 0] }}
                    transition={{ duration: 2, repeat: Infinity, delay: 1 }}
                    className="text-gray-400"
                  >
                    ↓
                  </motion.div>
                </div>

                {/* Protect */}
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.6 }}
                  className="flex items-center justify-between p-4 bg-cyan-50 rounded-lg border border-cyan-200"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-lg bg-cyan-500 flex items-center justify-center">
                      <span className="text-xl">🛡️</span>
                    </div>
                    <div>
                      <div className="font-semibold text-gray-900">Protect</div>
                      <div className="text-sm text-gray-500">Secure Anonymization</div>
                    </div>
                  </div>
                </motion.div>

                {/* Arrow */}
                <div className="flex justify-center">
                  <motion.div
                    animate={{ y: [0, 5, 0] }}
                    transition={{ duration: 2, repeat: Infinity, delay: 1.5 }}
                    className="text-gray-400"
                  >
                    ↓
                  </motion.div>
                </div>

                {/* Safe Database */}
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.7 }}
                  className="flex items-center justify-between p-4 bg-green-50 rounded-lg border border-green-200"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-lg bg-green-500 flex items-center justify-center">
                      <span className="text-xl">✅</span>
                    </div>
                    <div>
                      <div className="font-semibold text-gray-900">Safe Database</div>
                      <div className="text-sm text-gray-500">Privacy-Safe Destination</div>
                    </div>
                  </div>
                </motion.div>
              </div>

              {/* Floating Transformation Cards */}
              <div className="mt-6 space-y-3">
                {transformationExamples.map((example, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.8 + index * 0.1 }}
                    className="flex items-center justify-between p-3 bg-white rounded-lg border border-gray-200 shadow-sm"
                  >
                    <span className="text-sm text-gray-600 font-mono">{example.original}</span>
                    <span className="text-gray-400">→</span>
                    <span className="text-sm text-gray-900 font-mono font-semibold">{example.protected}</span>
                  </motion.div>
                ))}
              </div>
            </div>

            {/* Decorative Elements */}
            <motion.div
              animate={{ scale: [1, 1.1, 1] }}
              transition={{ duration: 4, repeat: Infinity }}
              className="absolute -top-4 -right-4 w-24 h-24 bg-primary-200 rounded-full blur-3xl opacity-50"
            />
            <motion.div
              animate={{ scale: [1, 1.1, 1] }}
              transition={{ duration: 4, repeat: Infinity, delay: 2 }}
              className="absolute -bottom-4 -left-4 w-32 h-32 bg-accent-200 rounded-full blur-3xl opacity-50"
            />
          </motion.div>
        </div>
      </Container>
    </section>
  );
};
