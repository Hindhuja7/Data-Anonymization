import { Navbar } from '@/components/landing/navbar';
import { Hero } from '@/components/landing/hero';
import { TrustStrip } from '@/components/landing/trust-strip';
import { FivePhasePipeline } from '@/components/landing/five-phase-pipeline';
import { ProductStory } from '@/components/landing/product-story';
import { VideoSection } from '@/components/landing/video-section';
import { CTASection } from '@/components/landing/cta-section';
import { Footer } from '@/components/landing/footer';

export default function LandingPage() {
  return (
    <main className="min-h-screen">
      <Navbar />
      <Hero />
      <TrustStrip />
      <FivePhasePipeline />
      <ProductStory />
      <VideoSection />
      <CTASection />
      <Footer />
    </main>
  );
}
