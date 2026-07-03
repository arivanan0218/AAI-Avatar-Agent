'use client';

import { motion } from 'motion/react';

export interface InterviewReport {
  average_score: number;
  recommendation: string;
  total_questions: number;
  duration_seconds: number;
  dimension_scores: {
    technical_accuracy?: number;
    completeness?: number;
    communication?: number;
  };
  strengths_count: number;
  improvements_count: number;
  domain: string;
}

interface ReportCardProps {
  report: InterviewReport;
  onClose: () => void;
}

const DIMENSION_LABELS: Record<string, string> = {
  technical_accuracy: 'Technical Accuracy',
  completeness: 'Completeness',
  communication: 'Communication',
};

function recommendationStyle(rec: string): { bg: string; text: string } {
  const r = rec.toLowerCase();
  if (r.includes('highly')) return { bg: 'bg-emerald-100 dark:bg-emerald-950', text: 'text-emerald-700 dark:text-emerald-300' };
  if (r.includes('not')) return { bg: 'bg-red-100 dark:bg-red-950', text: 'text-red-700 dark:text-red-300' };
  if (r.includes('borderline')) return { bg: 'bg-amber-100 dark:bg-amber-950', text: 'text-amber-700 dark:text-amber-300' };
  return { bg: 'bg-indigo-100 dark:bg-indigo-950', text: 'text-indigo-700 dark:text-indigo-300' };
}

function scoreColor(score: number): string {
  if (score >= 8) return 'text-emerald-500';
  if (score >= 6.5) return 'text-indigo-500';
  if (score >= 5) return 'text-amber-500';
  return 'text-red-500';
}

function barColor(score: number): string {
  if (score >= 8) return 'bg-emerald-500';
  if (score >= 6.5) return 'bg-indigo-500';
  if (score >= 5) return 'bg-amber-500';
  return 'bg-red-500';
}

export const ReportCard = ({ report, onClose }: ReportCardProps) => {
  const rec = recommendationStyle(report.recommendation);
  const minutes = Math.floor(report.duration_seconds / 60);
  const seconds = report.duration_seconds % 60;
  const domainLabel = report.domain.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.92, y: 16 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ type: 'spring', stiffness: 260, damping: 24 }}
        className="w-full max-w-md overflow-hidden rounded-3xl border border-gray-200 bg-white shadow-2xl dark:border-gray-800 dark:bg-gray-950"
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-indigo-600 to-violet-600 px-6 py-5 text-center">
          <p className="text-xs font-semibold uppercase tracking-wider text-indigo-100">
            Interview Complete
          </p>
          <p className="mt-1 text-sm text-indigo-100/90">{domainLabel}</p>
        </div>

        <div className="px-6 py-6">
          {/* Overall score */}
          <div className="text-center">
            <div className="flex items-end justify-center gap-1">
              <span className={`text-6xl font-bold tabular-nums ${scoreColor(report.average_score)}`}>
                {report.average_score.toFixed(1)}
              </span>
              <span className="mb-2 text-xl font-medium text-gray-400">/ 10</span>
            </div>
            <span
              className={`mt-3 inline-block rounded-full px-4 py-1.5 text-sm font-semibold ${rec.bg} ${rec.text}`}
            >
              {report.recommendation}
            </span>
          </div>

          {/* Dimension breakdown */}
          <div className="mt-6 space-y-3">
            {Object.entries(report.dimension_scores).map(([key, value]) => {
              const v = value ?? 0;
              return (
                <div key={key}>
                  <div className="mb-1 flex items-center justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">
                      {DIMENSION_LABELS[key] ?? key}
                    </span>
                    <span className="font-semibold tabular-nums text-black dark:text-white">
                      {v.toFixed(1)}
                    </span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-gray-100 dark:bg-gray-800">
                    <div
                      className={`h-full rounded-full ${barColor(v)}`}
                      style={{ width: `${Math.max(0, Math.min(100, (v / 10) * 100))}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Meta stats */}
          <div className="mt-6 grid grid-cols-3 gap-2 text-center">
            <Stat label="Questions" value={String(report.total_questions)} />
            <Stat label="Strengths" value={String(report.strengths_count)} />
            <Stat label="Duration" value={`${minutes}:${seconds.toString().padStart(2, '0')}`} />
          </div>

          <button
            type="button"
            onClick={onClose}
            className="mt-6 w-full rounded-xl bg-gray-100 py-3 text-sm font-semibold text-gray-700 transition-colors hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700"
          >
            Close
          </button>
        </div>
      </motion.div>
    </div>
  );
};

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-gray-50 py-3 dark:bg-gray-900">
      <div className="text-lg font-bold tabular-nums text-black dark:text-white">{value}</div>
      <div className="text-xs text-gray-500 dark:text-gray-400">{label}</div>
    </div>
  );
}
