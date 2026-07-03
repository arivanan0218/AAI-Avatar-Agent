'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import type { InterviewDomain } from '@/lib/types';
import { DOMAIN_LABELS } from '@/lib/types';

interface WelcomeProps {
  disabled: boolean;
  startButtonText: string;
  onStartCall: (domain: InterviewDomain) => void;
}

const DOMAIN_META: Record<InterviewDomain, { icon: string; description: string }> = {
  software_engineering: {
    icon: '💻',
    description: 'Data structures, system design, distributed systems, algorithms',
  },
  healthcare: {
    icon: '🩺',
    description: 'Clinical AI, EHR systems, HIPAA, medical NLP, federated learning',
  },
  finance: {
    icon: '📈',
    description: 'Fraud detection, credit risk, algorithmic trading, financial NLP',
  },
};

export const Welcome = ({
  disabled,
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeProps) => {
  const [selectedDomain, setSelectedDomain] = useState<InterviewDomain>('software_engineering');

  return (
    <div
      ref={ref}
      inert={disabled}
      className="fixed inset-0 z-10 flex h-svh flex-col items-center justify-center overflow-hidden bg-white px-6 dark:bg-black"
    >
      {/* Ambient gradient glow */}
      <div
        aria-hidden
        className="ia-glow pointer-events-none absolute top-[-10%] left-1/2 h-[520px] w-[520px] -translate-x-1/2 rounded-full opacity-60 blur-3xl dark:opacity-40"
      />

      <div className="ia-enter relative flex w-full max-w-sm flex-col items-center">
        {/* Logo + Title */}
        <div className="mb-8 text-center">
          <div className="relative mx-auto mb-5 h-16 w-16">
            <div
              aria-hidden
              className="absolute inset-0 rounded-[18px] bg-indigo-500/40 blur-xl"
            />
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/interview_ai_logo.svg"
              alt="InterviewAI"
              className="relative h-16 w-16 drop-shadow-lg"
            />
          </div>
          <h1 className="bg-gradient-to-r from-indigo-600 via-violet-600 to-indigo-500 bg-clip-text text-4xl font-bold tracking-tight text-transparent dark:from-indigo-300 dark:via-violet-300 dark:to-indigo-200">
            InterviewAI
          </h1>
          <p className="mx-auto mt-3 max-w-xs text-sm leading-relaxed text-gray-500 dark:text-gray-400">
            Real-time AI avatar interviews with NLP evaluation, RAG-grounded questions, and
            Chain-of-Thought scoring.
          </p>
        </div>

        {/* Domain Selection */}
        <div className="mb-6 w-full">
          <p className="mb-3 text-xs font-semibold tracking-wider text-gray-500 uppercase dark:text-gray-400">
            Choose your interview track
          </p>
          <div className="space-y-2.5">
            {(Object.keys(DOMAIN_LABELS) as InterviewDomain[]).map((domain) => {
              const isSelected = selectedDomain === domain;
              return (
                <button
                  key={domain}
                  type="button"
                  onClick={() => setSelectedDomain(domain)}
                  className={`group flex w-full items-center gap-3.5 rounded-2xl border px-4 py-3 text-left transition-all duration-200 ${
                    isSelected
                      ? 'border-indigo-500 bg-indigo-50 shadow-sm shadow-indigo-500/10 dark:border-indigo-400/70 dark:bg-indigo-950/60'
                      : 'border-gray-200 hover:border-indigo-300 hover:bg-gray-50 dark:border-gray-800 dark:hover:border-gray-600 dark:hover:bg-gray-950'
                  }`}
                >
                  <span
                    className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-lg transition-colors ${
                      isSelected
                        ? 'bg-indigo-600 shadow-sm'
                        : 'bg-gray-100 group-hover:bg-gray-200 dark:bg-gray-900 dark:group-hover:bg-gray-800'
                    }`}
                  >
                    {DOMAIN_META[domain].icon}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="flex items-center justify-between">
                      <span
                        className={`text-sm font-semibold ${
                          isSelected
                            ? 'text-indigo-700 dark:text-indigo-200'
                            : 'text-black dark:text-white'
                        }`}
                      >
                        {DOMAIN_LABELS[domain]}
                      </span>
                      {isSelected && (
                        <svg
                          className="h-5 w-5 text-indigo-600 dark:text-indigo-400"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                            clipRule="evenodd"
                          />
                        </svg>
                      )}
                    </span>
                    <span className="mt-0.5 block truncate text-xs text-gray-500 dark:text-gray-400">
                      {DOMAIN_META[domain].description}
                    </span>
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Start Button */}
        <div className="mt-1 w-full">
          <Button
            variant="primary"
            size="lg"
            onClick={() => onStartCall(selectedDomain)}
            className="h-12 w-full rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 text-base font-semibold text-white shadow-lg shadow-indigo-600/20 transition-all hover:from-indigo-700 hover:to-violet-700 hover:shadow-indigo-600/30 dark:from-indigo-500 dark:to-violet-500 dark:hover:from-indigo-600 dark:hover:to-violet-600"
          >
            {startButtonText} — {DOMAIN_LABELS[selectedDomain]}
          </Button>
        </div>
      </div>

      <style>{`
        .ia-glow {
          background: radial-gradient(circle at center, rgba(99,102,241,0.55), rgba(124,58,237,0.25) 45%, transparent 70%);
        }
        .ia-enter {
          animation: ia-fade-up 0.6s cubic-bezier(0.22, 1, 0.36, 1) both;
        }
        @keyframes ia-fade-up {
          from { opacity: 0; transform: translateY(16px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @media (prefers-reduced-motion: reduce) {
          .ia-enter { animation: none; }
        }
      `}</style>
    </div>
  );
};
