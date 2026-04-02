import { useState, useEffect, useCallback, useRef } from 'react';

interface ScanProgressEvent {
  event: 'progress' | 'complete' | 'info' | 'error';
  stage?: string;
  pct?: number;
  message?: string;
  findings_count?: number;
  status?: string;
  summary?: any;
}

export const useScanSocket = (scanId: string | null) => {
  const [stage, setStage] = useState<string>('initializing');
  const [pct, setPct] = useState<number>(0);
  const [message, setMessage] = useState<string>('Connecting to scan feed...');
  const [findingsCount, setFindingsCount] = useState<number>(0);
  const [isComplete, setIsComplete] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  const socketRef = useRef<WebSocket | null>(null);
  const retryCountRef = useRef<number>(0);
  const maxRetries = 3;

  const connect = useCallback(() => {
    if (!scanId) return;

    // Determine WS protocol based on current location
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/api/v1/ws/scan/${scanId}`;

    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onopen = () => {
      console.log('Scan WebSocket connected');
      retryCountRef.current = 0;
      setError(null);
    };

    socket.onmessage = (event) => {
      const data: ScanProgressEvent = JSON.parse(event.data);
      
      switch (data.event) {
        case 'info':
          if (data.status) setStage(data.status);
          if (data.findings_count !== undefined) setFindingsCount(data.findings_count);
          break;
        case 'progress':
          if (data.stage) setStage(data.stage);
          if (data.pct !== undefined) setPct(data.pct);
          if (data.message) setMessage(data.message);
          if (data.findings_count !== undefined) setFindingsCount(data.findings_count);
          break;
        case 'complete':
          setPct(100);
          setStage('complete');
          setMessage('Scan completed successfully.');
          setIsComplete(true);
          if (data.summary?.total_findings !== undefined) {
              setFindingsCount(data.summary.total_findings);
          }
          break;
        case 'error':
          setError(data.message || 'An unknown error occurred');
          break;
      }
    };

    socket.onclose = (event) => {
      console.log('Scan WebSocket closed', event);
      if (!isComplete && retryCountRef.current < maxRetries) {
        const timeout = Math.pow(2, retryCountRef.current) * 1000;
        retryCountRef.current += 1;
        setTimeout(connect, timeout);
      }
    };

    socket.onerror = (err) => {
      console.error('Scan WebSocket error', err);
    };
  }, [scanId, isComplete]);

  useEffect(() => {
    connect();
    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [connect]);

  return { stage, pct, message, findingsCount, isComplete, error };
};
