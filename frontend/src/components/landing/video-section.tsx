'use client';

import React from 'react';
import { Container } from '@/components/ui/container';
import { Play } from 'lucide-react';
import { motion } from 'framer-motion';

export const VideoSection = () => {
  return (
    <section className="py-24 gradient-bg">
      <Container>
        <div className="text-center mb-12">
          <h2 className="text-4xl lg:text-5xl font-bold mb-4">
            See the privacy pipeline in action
          </h2>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Watch how DataGuard transforms sensitive production data into privacy-safe datasets
            in just 90 seconds.
          </p>
        </div>

        <div className="relative max-w-4xl mx-auto">
          {/* Video Preview */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="relative bg-gray-900 rounded-2xl aspect-video overflow-hidden shadow-2xl border border-gray-200"
          >
            {/* Placeholder Gradient */}
            <div className="absolute inset-0 bg-gradient-to-br from-primary-600 via-accent-600 to-cyan-600 opacity-90" />
            
            {/* Play Button */}
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              className="absolute inset-0 flex items-center justify-center"
            >
              <div className="w-20 h-20 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center border-2 border-white/40">
                <Play className="w-10 h-10 text-white fill-white ml-1" />
              </div>
            </motion.button>

            {/* Video Info Overlay */}
            <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-black/60 to-transparent">
              <div className="text-white">
                <div className="text-sm font-medium mb-1">Product Demo</div>
                <div className="text-xs text-white/80">1:30 • Watch the complete pipeline</div>
              </div>
            </div>
          </motion.div>

          {/* Decorative Elements */}
          <motion.div
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 4, repeat: Infinity }}
            className="absolute -top-8 -left-8 w-32 h-32 bg-primary-200 rounded-full blur-3xl opacity-50"
          />
          <motion.div
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 4, repeat: Infinity, delay: 2 }}
            className="absolute -bottom-8 -right-8 w-40 h-40 bg-accent-200 rounded-full blur-3xl opacity-50"
          />
        </div>
      </Container>
    </section>
  );
};
