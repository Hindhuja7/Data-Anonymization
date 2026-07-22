'use client';

import React from 'react';
import { Container } from '@/components/ui/container';
import { Button } from '@/components/ui/button';
import { ArrowRight } from 'lucide-react';

export const CTASection = () => {
  return (
    <section className="py-24 bg-white">
      <Container>
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-4xl lg:text-5xl font-bold mb-6">
            Ready to make your production data safe?
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            Start protecting sensitive data today with AI-powered PII detection and governed anonymization policies.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" className="group">
              Start Free Trial
              <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Button>
            <Button variant="outline" size="lg">
              Schedule Demo
            </Button>
          </div>
        </div>
      </Container>
    </section>
  );
};
