'use client';

import { useEffect, useMemo, useState } from 'react';
import { Room, RoomEvent, DisconnectReason, ConnectionQuality, Participant } from 'livekit-client';
import { motion } from 'motion/react';
import { RoomAudioRenderer, RoomContext, StartAudio } from '@livekit/components-react';
import { toastAlert } from '@/components/alert-toast';
import { SessionView } from '@/components/session-view';
import { Toaster } from '@/components/ui/sonner';
import { Welcome } from '@/components/welcome';
import useConnectionDetails from '@/hooks/useConnectionDetails';
import type { AppConfig, InterviewDomain } from '@/lib/types';

const MotionWelcome = motion.create(Welcome);
const MotionSessionView = motion.create(SessionView);

interface AppProps {
  appConfig: AppConfig;
}

export function App({ appConfig }: AppProps) {
  const room = useMemo(() => new Room(), []);
  const [sessionStarted, setSessionStarted] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [selectedDomain, setSelectedDomain] = useState<InterviewDomain>('software_engineering');
  const { connectionDetails, refreshConnectionDetails } = useConnectionDetails(selectedDomain);

  useEffect(() => {
    const onDisconnected = (reason?: DisconnectReason) => {
      console.log('Room disconnected:', reason);
      
      // Auto-retry connection for certain disconnection reasons
      const shouldRetry = retryCount < 3 && (
        reason === DisconnectReason.STATE_MISMATCH ||
        reason === DisconnectReason.SIGNAL_CLOSE ||
        !reason // Unknown disconnection
      );
      
      if (shouldRetry && sessionStarted) {
        setRetryCount((prev: number) => prev + 1);

        console.log(`Attempting reconnection (${retryCount + 1}/3)...`);

        setTimeout(() => {
          refreshConnectionDetails();
        }, 2000);
        
        toastAlert({
          title: 'Reconnecting...',
          description: `Connection lost. Attempting to reconnect (${retryCount + 1}/3)`,
        });
      } else {
        setSessionStarted(false);
        setRetryCount(0);
        refreshConnectionDetails();
        
        // Show user-friendly message based on disconnection reason
        if (reason) {
          toastAlert({
            title: 'Session ended',
            description: `Connection lost. Please try again.`,
          });
        }
      }
    };
    
    const onMediaDevicesError = (error: Error) => {
      console.error('Media devices error:', error);
      toastAlert({
        title: 'Encountered an error with your media devices',
        description: `${error.name}: ${error.message}`,
      });
    };
    
    const onConnectionQualityChanged = (quality: ConnectionQuality, participant: Participant) => {
      console.log('Connection quality changed:', quality, participant?.identity);
      if (quality === ConnectionQuality.Poor) {
        console.warn('Poor connection quality detected');
      }
    };
    
    const onParticipantDisconnected = (participant: Participant) => {
      console.log('Participant disconnected:', participant?.identity);
      if (participant?.identity?.includes('agent')) {
        toastAlert({
          title: 'Agent disconnected',
          description: 'The AI agent has left the session. Reconnecting...',
        });
      }
    };
    
    room.on(RoomEvent.MediaDevicesError, onMediaDevicesError);
    room.on(RoomEvent.Disconnected, onDisconnected);
    room.on(RoomEvent.ConnectionQualityChanged, onConnectionQualityChanged);
    room.on(RoomEvent.ParticipantDisconnected, onParticipantDisconnected);
    
    return () => {
      room.off(RoomEvent.Disconnected, onDisconnected);
      room.off(RoomEvent.MediaDevicesError, onMediaDevicesError);
      room.off(RoomEvent.ConnectionQualityChanged, onConnectionQualityChanged);
      room.off(RoomEvent.ParticipantDisconnected, onParticipantDisconnected);
    };
  }, [room, refreshConnectionDetails, retryCount, sessionStarted]);

  useEffect(() => {
    let aborted = false;
    if (sessionStarted && room.state === 'disconnected' && connectionDetails) {
      Promise.all([
        room.localParticipant.setMicrophoneEnabled(true, undefined, {
          preConnectBuffer: appConfig.isPreConnectBufferEnabled,
        }),
        room.connect(connectionDetails.serverUrl, connectionDetails.participantToken),
      ]).catch((error) => {
        if (aborted) {
          // Once the effect has cleaned up after itself, drop any errors
          //
          // These errors are likely caused by this effect rerunning rapidly,
          // resulting in a previous run `disconnect` running in parallel with
          // a current run `connect`
          return;
        }

        toastAlert({
          title: 'There was an error connecting to the agent',
          description: `${error.name}: ${error.message}`,
        });
      });
    }
    return () => {
      aborted = true;
      room.disconnect();
    };
  }, [room, sessionStarted, connectionDetails, appConfig.isPreConnectBufferEnabled]);

  const { startButtonText } = appConfig;

  return (
    <>
      <MotionWelcome
        key="welcome"
        startButtonText={startButtonText}
        onStartCall={(domain: InterviewDomain) => {
            setSelectedDomain(domain);
            setSessionStarted(true);
          }}
        disabled={sessionStarted}
        initial={{ opacity: 0 }}
        animate={{ opacity: sessionStarted ? 0 : 1 }}
        transition={{ duration: 0.5, ease: 'linear', delay: sessionStarted ? 0 : 0.5 }}
      />

      <RoomContext.Provider value={room}>
        <RoomAudioRenderer />
        <StartAudio label="Start Audio" />
        {/* --- */}
        <MotionSessionView
          key="session-view"
          appConfig={appConfig}
          disabled={!sessionStarted}
          sessionStarted={sessionStarted}
          initial={{ opacity: 0 }}
          animate={{ opacity: sessionStarted ? 1 : 0 }}
          transition={{
            duration: 0.5,
            ease: 'linear',
            delay: sessionStarted ? 0.5 : 0,
          }}
        />
      </RoomContext.Provider>

      <Toaster />
    </>
  );
}
