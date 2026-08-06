"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth';
import { usePipelineStore } from '@/store/pipeline';
import { Shield, Lock, Mail, Eye, EyeOff, Sparkles } from 'lucide-react';
import Button from '@/components/ui/Button';

export default function LoginPage() {
  const router = useRouter();
  const loginStore = useAuthStore();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email || !password) {
      setError('Please fill in all fields.');
      return;
    }

    setIsLoading(true);

    try {
      // Connect to FastAPI login endpoint
      const response = await fetch('http://localhost:8000/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: email, password: password }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Invalid email or password.');
      }

      const data = await response.json();
      
      // Save token & active user email in localStorage and Zustand store
      if (typeof window !== 'undefined') {
        localStorage.setItem('datavault_user_email', email);
        localStorage.setItem('datavault_user_id', email);
        localStorage.setItem('datavault_active_user', email);
      }
      loginStore.setToken(data.token || data.access_token || null);
      loginStore.setUser({
        id: email,
        email: email,
        name: email.split('@')[0],
        role: "admin",
      });

      router.replace('/dashboard');

      // Preserve existing user runs and policies across login sessions
      try {
        usePipelineStore.getState().reset();
      } catch (err) {
        console.error("Pipeline store sync error:", err);
      }

      // Redirect to main console dashboard page
      router.push('/');
    } catch (err: any) {
      setError(err.message || 'Unable to connect to login server.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-screen bg-[#040816] text-white flex items-center justify-center relative p-6 font-sans selection:bg-[#4F7CFF]/30 selection:text-white">
      {/* Decorative Blur Background Vignette */}
      <div className="absolute inset-0 bg-radial-gradient(circle at center, rgba(79,124,255,0.06) 0%, transparent 60%) pointer-events-none" />

      <div className="w-full max-w-[450px] relative z-10">
        
        {/* Brand Header */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 bg-gradient-to-br from-emerald-500/20 to-[#4F7CFF]/20 border border-emerald-500 rounded-2xl flex items-center justify-center text-emerald-400 shadow-[0_0_30px_rgba(16,185,129,0.25)] mb-4">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <rect x="5" y="11" width="14" height="10" rx="2" ry="2"></rect>
              <path d="M8 11V7a4 4 0 0 1 8 0v4"></path>
              <text x="12" y="18" fontSize="8" fontWeight="bold" fill="currentColor" textAnchor="middle" stroke="none">D</text>
            </svg>
          </div>
          <h1 className="text-2xl font-extrabold tracking-tight">DataVault AI</h1>
          <p className="text-xs text-slate-400 mt-1 uppercase tracking-wider font-semibold">Secure. Anonymize. Comply.</p>
        </div>

        {/* Login Panel Card */}
        <div className="bg-[#0D1324]/85 border border-white/6 rounded-2xl p-8 shadow-2xl backdrop-blur-xl">
          <h2 className="text-lg font-bold text-white mb-1.5 flex items-center gap-2">
            Sign In to Console
          </h2>
          <p className="text-xs text-[#8C96B5] mb-6">Enter your administrator connection credentials below.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3 bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl text-xs font-semibold">
                {error}
              </div>
            )}

            {/* Email Field */}
            <div className="space-y-1.5">
              <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Email Address</label>
              <div className="relative">
                <Mail size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@datavault.ai"
                  className="w-full bg-[#050816]/75 border border-white/8 rounded-xl pl-10 pr-4 py-3 text-sm text-[#f8fafc] outline-none focus:border-[#4F7CFF] transition-all"
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="space-y-1.5">
              <div className="flex justify-between items-center">
                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Password</label>
                <a href="#" className="text-[10px] text-[#4F7CFF] hover:underline font-bold uppercase tracking-wider">Forgot Password?</a>
              </div>
              <div className="relative">
                <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-[#050816]/75 border border-white/8 rounded-xl pl-10 pr-10 py-3 text-sm text-[#f8fafc] outline-none focus:border-[#4F7CFF] transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* Remember Me Toggle */}
            <div className="flex items-center gap-2.5 pt-1.5">
              <input
                type="checkbox"
                id="remember"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="w-4 h-4 rounded border-white/8 bg-[#050816]/60 text-[#4F7CFF] focus:ring-[#4F7CFF]"
              />
              <label htmlFor="remember" className="text-xs text-slate-300 cursor-pointer">Remember me for 30 days</label>
            </div>

            {/* Submit Button */}
            <div className="pt-4">
              <Button
                type="submit"
                isLoading={isLoading}
                className="w-full bg-[#4F7CFF] hover:bg-[#3b66d8] text-white py-3 font-semibold rounded-xl flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(79,124,255,0.25)] hover-lift"
              >
                Sign In
              </Button>
            </div>
          </form>
        </div>

        {/* Footer info */}
        <p className="text-center text-[10px] text-slate-500 mt-6 leading-relaxed">
          Authorized console access only. Logins are audited.<br />
          DataVault AI conforms to the DPDP Act 2023.
        </p>

      </div>
    </div>
  );
}
