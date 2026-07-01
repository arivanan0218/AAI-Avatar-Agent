import { NextRequest, NextResponse } from 'next/server';
import { AccessToken, type AccessTokenOptions, type VideoGrant } from 'livekit-server-sdk';

const API_KEY = process.env.LIVEKIT_API_KEY;
const API_SECRET = process.env.LIVEKIT_API_SECRET;
const LIVEKIT_URL = process.env.LIVEKIT_URL;

export const revalidate = 0;

const SUPPORTED_DOMAINS = ['software_engineering', 'healthcare', 'finance'] as const;
type InterviewDomain = (typeof SUPPORTED_DOMAINS)[number];

export type ConnectionDetails = {
  serverUrl: string;
  roomName: string;
  participantName: string;
  participantToken: string;
};

export async function GET(request: NextRequest) {
  try {
    if (!LIVEKIT_URL) throw new Error('LIVEKIT_URL is not defined');
    if (!API_KEY) throw new Error('LIVEKIT_API_KEY is not defined');
    if (!API_SECRET) throw new Error('LIVEKIT_API_SECRET is not defined');

    const { searchParams } = new URL(request.url);
    const rawDomain = searchParams.get('domain') ?? 'software_engineering';
    const domain: InterviewDomain = (SUPPORTED_DOMAINS as readonly string[]).includes(rawDomain)
      ? (rawDomain as InterviewDomain)
      : 'software_engineering';

    const participantIdentity = `candidate_${Math.floor(Math.random() * 10_000)}`;
    const roomName = `interview_${domain}_${Math.floor(Math.random() * 10_000)}`;

    const participantToken = await createParticipantToken(
      { identity: participantIdentity, name: 'Candidate' },
      roomName,
      JSON.stringify({ domain }),
    );

    const data: ConnectionDetails = {
      serverUrl: LIVEKIT_URL,
      roomName,
      participantToken,
      participantName: 'Candidate',
    };

    return NextResponse.json(data, {
      headers: { 'Cache-Control': 'no-store' },
    });
  } catch (error) {
    if (error instanceof Error) {
      console.error(error);
      return new NextResponse(error.message, { status: 500 });
    }
  }
}

function createParticipantToken(
  userInfo: AccessTokenOptions,
  roomName: string,
  metadata: string,
) {
  const at = new AccessToken(API_KEY, API_SECRET, { ...userInfo, ttl: '30m' });
  const grant: VideoGrant = {
    room: roomName,
    roomJoin: true,
    canPublish: true,
    canPublishData: true,
    canSubscribe: true,
  };
  at.addGrant(grant);
  at.metadata = metadata;
  return at.toJwt();
}
