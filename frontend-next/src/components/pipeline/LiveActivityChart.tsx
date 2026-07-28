'use client';

import { useEffect, useState } from 'react';

interface LiveActivityChartProps {
  isActive: boolean;
}

export default function LiveActivityChart({ isActive }: LiveActivityChartProps) {
  const [points, setPoints] = useState<number[]>(() =>
    Array.from({ length: 30 }, () => 20 + Math.random() * 60)
  );

  useEffect(() => {
    if (!isActive) return;

    const interval = setInterval(() => {
      setPoints((prev) => {
        const last = prev[prev.length - 1];
        const jitter = last + (Math.random() - 0.5) * 12;
        const clamped = Math.max(10, Math.min(85, jitter));
        return [...prev.slice(1), clamped];
      });
    }, 600);

    return () => clearInterval(interval);
  }, [isActive]);

  const width = 280;
  const height = 80;
  const padding = 4;

  const maxVal = 100;
  const minVal = 0;

  const pathPoints = points.map((val, i) => {
    const x = padding + (i / (points.length - 1)) * (width - padding * 2);
    const y = height - padding - ((val - minVal) / (maxVal - minVal)) * (height - padding * 2);
    return { x, y };
  });

  const linePath = pathPoints.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
  const areaPath = `${linePath} L ${pathPoints[pathPoints.length - 1].x} ${height} L ${pathPoints[0].x} ${height} Z`;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="w-full h-full"
      preserveAspectRatio="none"
    >
      <defs>
        <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="rgba(79,124,255,0.35)" />
          <stop offset="100%" stopColor="rgba(79,124,255,0)" />
        </linearGradient>
        <filter id="glow">
          <feGaussianBlur stdDeviation="2" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Grid lines */}
      {[0.25, 0.5, 0.75].map((ratio) => (
        <line
          key={ratio}
          x1={padding}
          y1={height * ratio}
          x2={width - padding}
          y2={height * ratio}
          stroke="rgba(255,255,255,0.04)"
          strokeWidth={1}
        />
      ))}

      {/* Area fill */}
      <path d={areaPath} fill="url(#chartGradient)" />

      {/* Line */}
      <path
        d={linePath}
        fill="none"
        stroke="#4F7CFF"
        strokeWidth={2}
        filter="url(#glow)"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* End dot */}
      {isActive && pathPoints.length > 0 && (
        <circle
          cx={pathPoints[pathPoints.length - 1].x}
          cy={pathPoints[pathPoints.length - 1].y}
          r={4}
          fill="#4F7CFF"
          className="animate-pulse"
        >
          <animate
            attributeName="r"
            values="3;5;3"
            dur="1.5s"
            repeatCount="indefinite"
          />
        </circle>
      )}
    </svg>
  );
}
