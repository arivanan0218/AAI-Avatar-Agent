import { useCallback, useEffect, useState } from 'react';
import type { InterviewDomain } from '@/lib/types';
import { ConnectionDetails } from '@/app/api/connection-details/route';

export default function useConnectionDetails(domain: InterviewDomain = 'software_engineering') {
  const [connectionDetails, setConnectionDetails] = useState<ConnectionDetails | null>(null);

  const fetchConnectionDetails = useCallback(() => {
    setConnectionDetails(null);
    const url = new URL(
      process.env.NEXT_PUBLIC_CONN_DETAILS_ENDPOINT ?? '/api/connection-details',
      window.location.origin
    );
    url.searchParams.set('domain', domain);
    fetch(url.toString())
      .then((res) => res.json())
      .then((data) => {
        setConnectionDetails(data);
      })
      .catch((error) => {
        console.error('Error fetching connection details:', error);
      });
  }, [domain]);

  useEffect(() => {
    fetchConnectionDetails();
  }, [fetchConnectionDetails]);

  return { connectionDetails, refreshConnectionDetails: fetchConnectionDetails };
}
