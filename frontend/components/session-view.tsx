'use client';

import React, { useEffect, useState } from 'react';
import { RoomEvent } from 'livekit-client';
import { AnimatePresence, motion } from 'motion/react';
import {
  type AgentState,
  type ReceivedChatMessage,
  useRoomContext,
  useVoiceAssistant,
  useTranscriptions,
} from '@livekit/components-react';
import { toastAlert } from '@/components/alert-toast';
import { AgentControlBar } from '@/components/livekit/agent-control-bar/agent-control-bar';
import { ChatEntry } from '@/components/livekit/chat/chat-entry';
import { ChatMessageView } from '@/components/livekit/chat/chat-message-view';
import { MediaTiles } from '@/components/livekit/media-tiles';
import { type InterviewReport, ReportCard } from '@/components/report-card';
import useChatAndTranscription from '@/hooks/useChatAndTranscription';
import { useDebugMode } from '@/hooks/useDebug';
import type { AppConfig } from '@/lib/types';
import { cn } from '@/lib/utils';

function isAgentAvailable(agentState: AgentState) {
  return agentState == 'listening' || agentState == 'thinking' || agentState == 'speaking';
}

interface SessionViewProps {
  appConfig: AppConfig;
  disabled: boolean;
  sessionStarted: boolean;
}

export const SessionView = ({
  appConfig,
  disabled,
  sessionStarted,
  ref,
}: React.ComponentProps<'div'> & SessionViewProps) => {
  const { state: agentState } = useVoiceAssistant();
  const [chatOpen, setChatOpen] = useState(false);
  const [report, setReport] = useState<InterviewReport | null>(null);
  const { messages, send } = useChatAndTranscription();
  const transcriptions = useTranscriptions();
  const room = useRoomContext();

  useDebugMode();

  // Listen for the final interview report the agent publishes when the interview ends.
  useEffect(() => {
    const handleData = (payload: Uint8Array, _p?: unknown, _k?: unknown, topic?: string) => {
      console.log('[InterviewAI] data received, topic =', topic);
      if (topic && topic !== 'interview_report') return;
      try {
        const msg = JSON.parse(new TextDecoder().decode(payload));
        if (msg?.type === 'interview_report' && msg.report) {
          console.log('[InterviewAI] showing score card', msg.report);
          setReport(msg.report as InterviewReport);
        }
      } catch {
        // ignore non-JSON / unrelated data packets
      }
    };
    room.on(RoomEvent.DataReceived, handleData);
    return () => {
      room.off(RoomEvent.DataReceived, handleData);
    };
  }, [room]);

  async function handleSendMessage(message: string) {
    await send(message);
  }

  // Ask the agent to score the interview so far and show the result card.
  async function handleFinish() {
    try {
      const payload = new TextEncoder().encode(JSON.stringify({ type: 'request_report' }));
      await room.localParticipant.publishData(payload, { reliable: true, topic: 'request_report' });
      console.log('[InterviewAI] requested score (published request_report)');
    } catch (e) {
      console.error('[InterviewAI] failed to request interview report', e);
    }
  }

  useEffect(() => {
    if (sessionStarted) {
      const timeout = setTimeout(() => {
        if (!isAgentAvailable(agentState)) {
          const reason =
            agentState === 'connecting'
              ? 'Agent did not join the room. '
              : 'Agent connected but did not complete initializing. ';

          console.error('Agent timeout:', { agentState, reason });

          toastAlert({
            title: 'Session ended',
            description: (
              <p className="w-full">
                {reason}
                <a
                  target="_blank"
                  rel="noopener noreferrer"
                  href="https://docs.livekit.io/agents/start/voice-ai/"
                  className="whitespace-nowrap underline"
                >
                  See quickstart guide
                </a>
                .
              </p>
            ),
          });
          room.disconnect();
        }
      }, 30_000); // Increased timeout to 30 seconds

      return () => clearTimeout(timeout);
    }
  }, [agentState, sessionStarted, room]);

  const { supportsChatInput, supportsVideoInput, supportsScreenShare } = appConfig;
  const capabilities = {
    supportsChatInput,
    supportsVideoInput,
    supportsScreenShare,
  };

  return (
    <main
      ref={ref}
      inert={disabled}
      className={cn(
        'bg-white dark:bg-black min-h-screen',
        !chatOpen && 'max-h-svh overflow-hidden'
      )}
    >
      {/* Header */}
      <div className="fixed top-0 left-0 right-0 z-40 bg-white/80 dark:bg-black/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
              <svg viewBox="0 0 24 24" fill="none" className="w-4 h-4 text-white" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <div>
              <h1 className="text-lg font-semibold text-black dark:text-white">InterviewAI</h1>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <div className="hidden items-center space-x-1 text-sm text-gray-600 sm:flex dark:text-gray-400">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span>Connected</span>
            </div>
            <button
              type="button"
              onClick={handleFinish}
              className="rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-semibold text-white transition-colors hover:bg-indigo-700"
            >
              End &amp; See Score
            </button>
          </div>
        </div>
      </div>

      {/* Live Transcription Overlay */}
      {transcriptions.length > 0 && (
        <div className="fixed top-20 left-1/2 transform -translate-x-1/2 z-[60]">
          <div className="bg-black/80 dark:bg-white/80 text-white dark:text-black px-6 py-3 rounded-xl text-sm font-medium backdrop-blur-md border border-gray-300 dark:border-gray-700 shadow-lg">
            {transcriptions[transcriptions.length - 1].text}
          </div>
        </div>
      )}

      {/* Chat Messages */}
      <ChatMessageView
        className={cn(
          'mx-auto min-h-svh w-full max-w-2xl px-4 pt-24 pb-32 transition-[opacity,translate] duration-300 ease-out',
          chatOpen ? 'translate-y-0 opacity-100 delay-200' : 'translate-y-20 opacity-0'
        )}
      >
        <div className="space-y-4">
          <AnimatePresence>
            {messages.map((message: ReceivedChatMessage) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3, ease: 'easeOut' }}
              >
                <ChatEntry hideName key={message.id} entry={message} />
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </ChatMessageView>

      {/* Video Area */}
      <div className="pt-16 pb-24">
        <MediaTiles chatOpen={chatOpen} />
      </div>

      {/* Control Bar */}
      <div className="fixed right-0 bottom-0 left-0 z-50 px-4 pb-12">
        <motion.div
          key="control-bar"
          initial={{ opacity: 0, translateY: '100%' }}
          animate={{
            opacity: sessionStarted ? 1 : 0,
            translateY: sessionStarted ? '0%' : '100%',
          }}
          transition={{ duration: 0.3, delay: sessionStarted ? 0.5 : 0, ease: 'easeOut' }}
        >
          <div className="relative z-10 mx-auto w-full max-w-2xl">
            {appConfig.isPreConnectBufferEnabled && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{
                  opacity: sessionStarted && messages.length === 0 ? 1 : 0,
                  transition: {
                    ease: 'easeIn',
                    delay: messages.length > 0 ? 0 : 0.8,
                    duration: messages.length > 0 ? 0.2 : 0.5,
                  },
                }}
                aria-hidden={messages.length > 0}
                className={cn(
                  'absolute inset-x-0 -top-12 text-center',
                  sessionStarted && messages.length === 0 && 'pointer-events-none'
                )}
              >
                <div className="inline-flex items-center space-x-2 bg-gray-100/90 dark:bg-gray-900/90 backdrop-blur-sm px-4 py-2 rounded-full">
                  <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    AI Assistant is listening
                  </p>
                </div>
              </motion.div>
            )}

            <div className="bg-gray-100/90 dark:bg-gray-900/90 backdrop-blur-md rounded-2xl border border-gray-200 dark:border-gray-800 p-4">
              <AgentControlBar
                capabilities={capabilities}
                onChatOpenChange={setChatOpen}
                onSendMessage={handleSendMessage}
              />
            </div>
          </div>
        </motion.div>
      </div>

      {/* Final score card (shown when the agent publishes the interview report) */}
      <AnimatePresence>
        {report && <ReportCard report={report} onClose={() => setReport(null)} />}
      </AnimatePresence>
    </main>
  );
};
