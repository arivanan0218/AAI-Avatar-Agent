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

const DOMAIN_DESCRIPTIONS: Record<InterviewDomain, string> = {
  software_engineering: 'Data structures, system design, distributed systems, algorithms',
  healthcare: 'Clinical AI, EHR systems, HIPAA, medical NLP, federated learning',
  finance: 'Fraud detection, credit risk, algorithmic trading, NLP on financial docs',
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
      className="fixed inset-0 z-10 mx-auto flex h-svh flex-col items-center justify-center bg-white dark:bg-black px-6"
    >
      {/* Logo + Title */}
      <div className="mb-8 text-center">
        <div className="w-14 h-14 mx-auto mb-5 rounded-2xl bg-indigo-600 flex items-center justify-center">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            className="w-8 h-8 text-white"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
            />
          </svg>
        </div>
        <h1 className="text-3xl font-bold text-black dark:text-white">InterviewAI</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-2 max-w-xs">
          AI-powered technical interviews with real-time avatar, NLP evaluation, and domain expertise
        </p>
      </div>

      {/* Domain Selection */}
      <div className="w-full max-w-sm mb-6">
        <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-3">
          Select Interview Domain
        </p>
        <div className="space-y-2">
          {(Object.keys(DOMAIN_LABELS) as InterviewDomain[]).map((domain) => (
            <button
              key={domain}
              onClick={() => setSelectedDomain(domain)}
              className={`w-full text-left px-4 py-3 rounded-xl border transition-all duration-150 ${
                selectedDomain === domain
                  ? 'border-indigo-600 bg-indigo-50 dark:bg-indigo-950 dark:border-indigo-400'
                  : 'border-gray-200 dark:border-gray-800 hover:border-gray-400 dark:hover:border-gray-600'
              }`}
            >
              <div className="flex items-center justify-between">
                <span
                  className={`font-medium text-sm ${
                    selectedDomain === domain
                      ? 'text-indigo-700 dark:text-indigo-300'
                      : 'text-black dark:text-white'
                  }`}
                >
                  {DOMAIN_LABELS[domain]}
                </span>
                {selectedDomain === domain && (
                  <svg
                    className="w-4 h-4 text-indigo-600 dark:text-indigo-400"
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
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                {DOMAIN_DESCRIPTIONS[domain]}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* AI Techniques Badges */}
      <div className="w-full max-w-sm mb-6">
        <div className="flex flex-wrap gap-1.5 justify-center">
          {[
            'NLP Pipeline',
            'RAG + Pinecone',
            'Few-Shot Learning',
            'Chain-of-Thought',
            'LLM (GPT-4o-mini)',
            'AI Avatar',
          ].map((tag) => (
            <span
              key={tag}
              className="text-xs px-2 py-1 rounded-full bg-gray-100 dark:bg-gray-900 text-gray-600 dark:text-gray-400"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>

      {/* Start Button */}
      <div className="w-full max-w-sm">
        <Button
          variant="primary"
          size="lg"
          onClick={() => onStartCall(selectedDomain)}
          className="w-full h-12 text-base font-semibold bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600 text-white rounded-xl transition-colors"
        >
          {startButtonText} — {DOMAIN_LABELS[selectedDomain]}
        </Button>
        <p className="text-center text-xs text-gray-400 dark:text-gray-600 mt-3">
          8 questions • Difficulty progression • AI-scored feedback
        </p>
      </div>
    </div>
  );
};
