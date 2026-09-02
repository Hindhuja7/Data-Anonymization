'use client';

interface StepIllustrationProps {
  stepId: number;
}

export default function StepIllustration({ stepId }: StepIllustrationProps) {
  return (
    <div className="relative w-full h-full flex items-center justify-center">
      {/* Glow platform */}
      <div className="absolute bottom-2 left-1/2 -translate-x-1/2 w-[140px] h-[40px] bg-[#4F7CFF]/10 rounded-full blur-xl" />

      <svg viewBox="0 0 180 120" className="w-full h-full relative z-10">
        <defs>
          <linearGradient id="platformGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#e2e8f0" />
            <stop offset="100%" stopColor="#cbd5e1" />
          </linearGradient>
          <linearGradient id="dbGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#3b82f6" />
            <stop offset="100%" stopColor="#2563eb" />
          </linearGradient>
          <filter id="isoGlow">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Isometric platform */}
        <polygon
          points="90,95 30,65 150,65"
          fill="url(#platformGrad)"
          stroke="rgba(79,124,255,0.3)"
          strokeWidth={1}
        />
        <polygon
          points="30,65 90,35 150,65 90,95"
          fill="rgba(79,124,255,0.08)"
          stroke="rgba(79,124,255,0.2)"
          strokeWidth={1}
        />

        {/* Database cylinder (isometric) */}
        <ellipse cx="70" cy="58" rx="18" ry="8" fill="url(#dbGrad)" filter="url(#isoGlow)" />
        <rect x="52" y="50" width="36" height="24" fill="url(#dbGrad)" opacity="0.9" />
        <ellipse cx="70" cy="50" rx="18" ry="8" fill="#60a5fa" />
        <ellipse cx="70" cy="58" rx="18" ry="8" fill="none" stroke="rgba(255,255,255,0.2)" strokeWidth={0.5} />
        <ellipse cx="70" cy="66" rx="18" ry="8" fill="none" stroke="rgba(255,255,255,0.15)" strokeWidth={0.5} />
        <ellipse cx="70" cy="74" rx="18" ry="8" fill="#2563eb" />

        {/* Clock */}
        <circle cx="120" cy="52" r="16" fill="#f8fafc" stroke="#3b82f6" strokeWidth={1.5} filter="url(#isoGlow)" />
        <circle cx="120" cy="52" r="2" fill="#3b82f6" />
        <line x1="120" y1="52" x2="120" y2="42" stroke="#3b82f6" strokeWidth={1.5} strokeLinecap="round" />
        <line x1="120" y1="52" x2="128" y2="56" stroke="#10b981" strokeWidth={1.5} strokeLinecap="round" />

        {/* Data sheets floating */}
        <g transform="translate(105, 30)" opacity="0.85">
          <rect x="0" y="0" width="22" height="16" rx="2" fill="#f1f5f9" stroke="rgba(59,130,246,0.4)" strokeWidth={1} transform="rotate(-8)" />
          <line x1="4" y1="5" x2="16" y2="5" stroke="#3b82f6" strokeWidth={0.8} transform="rotate(-8)" />
          <line x1="4" y1="9" x2="14" y2="9" stroke="rgba(59,130,246,0.5)" strokeWidth={0.8} transform="rotate(-8)" />
        </g>
        <g transform="translate(88, 22)" opacity="0.7">
          <rect x="0" y="0" width="18" height="14" rx="2" fill="#f1f5f9" stroke="rgba(16,185,129,0.4)" strokeWidth={1} transform="rotate(12)" />
          <line x1="3" y1="4" x2="13" y2="4" stroke="#10b981" strokeWidth={0.8} transform="rotate(12)" />
          <line x1="3" y1="8" x2="11" y2="8" stroke="rgba(16,185,129,0.5)" strokeWidth={0.8} transform="rotate(12)" />
        </g>

        {/* Step number badge */}
        <rect x="4" y="4" width="32" height="16" rx="4" fill="rgba(79,124,255,0.15)" stroke="rgba(79,124,255,0.3)" strokeWidth={1} />
        <text x="20" y="15" textAnchor="middle" fill="#4F7CFF" fontSize="9" fontWeight="bold">
          STEP {stepId}
        </text>
      </svg>
    </div>
  );
}
