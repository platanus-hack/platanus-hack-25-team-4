import { useState, useEffect, useCallback, useRef } from 'react';
import { observerApi } from '../services/observerApiClient';
import type {
  ObserverStats,
  ObserverEvent,
  EventCategory,
} from '../types/observer.types';

interface UseObserverDataOptions {
  statsInterval?: number; // Polling interval for stats in ms (default: 5000)
  eventsInterval?: number; // Polling interval for events in ms (default: 3000)
  eventsLimit?: number; // Max events to fetch (default: 200)
  eventTypes?: EventCategory[]; // Event types to fetch (default: ['all'])
  enabled?: boolean; // Enable/disable polling (default: true)
}

interface UseObserverDataReturn {
  stats: ObserverStats | null;
  events: ObserverEvent[];
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
  pause: () => void;
  resume: () => void;
  isPaused: boolean;
}

export function useObserverData(
  options: UseObserverDataOptions = {}
): UseObserverDataReturn {
  const {
    statsInterval = 5000,
    eventsInterval = 3000,
    eventsLimit = 200,
    eventTypes = ['all'],
    enabled = true,
  } = options;

  const [stats, setStats] = useState<ObserverStats | null>(null);
  const [events, setEvents] = useState<ObserverEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [isPaused, setIsPaused] = useState(!enabled);

  const statsIntervalRef = useRef<number | null>(null);
  const eventsIntervalRef = useRef<number | null>(null);

  // Fetch stats from API
  const fetchStats = useCallback(async () => {
    try {
      const data = await observerApi.getStats();
      setStats(data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch observer stats:', err);
      setError(err instanceof Error ? err : new Error('Unknown error'));
    }
  }, []);

  // Fetch events from API
  const fetchEvents = useCallback(async () => {
    try {
      if (eventTypes.length === 1) {
        const response = await observerApi.getEvents(
          eventTypes[0],
          eventsLimit
        );
        setEvents(response.events);
      } else {
        const responses = await observerApi.getEventsByCategories(
          eventTypes,
          eventsLimit
        );
        const allEvents = responses.flatMap((r) => r.events);
        // Sort by timestamp descending
        allEvents.sort((a, b) => b.timestamp - a.timestamp);
        // Take first eventsLimit items
        setEvents(allEvents.slice(0, eventsLimit));
      }
      setError(null);
    } catch (err) {
      console.error('Failed to fetch observer events:', err);
      setError(err instanceof Error ? err : new Error('Unknown error'));
    }
  }, [eventTypes, eventsLimit]);

  // Combined refetch function
  const refetch = useCallback(async () => {
    setLoading(true);
    await Promise.all([fetchStats(), fetchEvents()]);
    setLoading(false);
  }, [fetchStats, fetchEvents]);

  // Pause polling
  const pause = useCallback(() => {
    setIsPaused(true);
    if (statsIntervalRef.current) {
      clearInterval(statsIntervalRef.current);
      statsIntervalRef.current = null;
    }
    if (eventsIntervalRef.current) {
      clearInterval(eventsIntervalRef.current);
      eventsIntervalRef.current = null;
    }
  }, []);

  // Resume polling
  const resume = useCallback(() => {
    setIsPaused(false);
  }, []);

  // Initial fetch
  useEffect(() => {
    if (!isPaused) {
      void refetch();
    }
  }, [refetch, isPaused]);

  // Set up polling intervals
  useEffect(() => {
    if (isPaused) return;

    // Stats polling
    statsIntervalRef.current = setInterval(() => {
      void fetchStats();
    }, statsInterval) as unknown as number;

    // Events polling
    eventsIntervalRef.current = setInterval(() => {
      void fetchEvents();
    }, eventsInterval) as unknown as number;

    // Cleanup
    return () => {
      if (statsIntervalRef.current) {
        clearInterval(statsIntervalRef.current);
      }
      if (eventsIntervalRef.current) {
        clearInterval(eventsIntervalRef.current);
      }
    };
  }, [isPaused, fetchStats, fetchEvents, statsInterval, eventsInterval]);

  return {
    stats,
    events,
    loading,
    error,
    refetch,
    pause,
    resume,
    isPaused,
  };
}
