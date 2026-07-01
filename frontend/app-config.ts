import type { AppConfig } from './lib/types';

export const APP_CONFIG_DEFAULTS: AppConfig = {
  companyName: 'InterviewAI',
  pageTitle: 'InterviewAI — AI-Powered Technical Interviews',
  pageDescription:
    'Practice technical interviews with an AI avatar powered by NLP, RAG, and Chain-of-Thought evaluation.',

  supportsChatInput: true,
  supportsVideoInput: true,
  supportsScreenShare: false,
  isPreConnectBufferEnabled: true,

  logo: '/interview_ai_logo.svg',
  accent: '#4F46E5',
  logoDark: '/interview_ai_logo.svg',
  accentDark: '#818CF8',
  startButtonText: 'Start Interview',
};
