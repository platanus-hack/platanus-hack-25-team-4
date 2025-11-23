import { ScrollArea } from '../ui/scroll-area';
import { Card } from '../ui/card';
import type { ObserverEvent } from '../../types/observer.types';
import { graphTransformer } from '../../services/graphTransformer';

interface EventFeedProps {
  events: ObserverEvent[];
  maxEvents?: number;
}

export function EventFeed({ events, maxEvents = 50 }: EventFeedProps) {
  const recentEvents = events.slice(0, maxEvents);

  const getEventIcon = (eventType: string): string => {
    if (eventType.includes('location')) return '📍';
    if (eventType.includes('collision')) return '💥';
    if (eventType.includes('mission')) return '🎯';
    if (eventType.includes('agent_match')) return '🤝';
    if (eventType.includes('match')) return '❤️';
    if (eventType.includes('conversation')) return '💬';
    if (eventType.includes('chat')) return '💭';
    return '📌';
  };

  const getEventCategory = (eventType: string): string => {
    if (eventType.startsWith('location.')) return 'location';
    if (eventType.startsWith('collision.')) return 'collision';
    if (eventType.startsWith('mission.')) return 'mission';
    if (eventType.startsWith('agent_match.')) return 'agent_match';
    if (eventType.startsWith('match.')) return 'match';
    if (eventType.startsWith('conversation.')) return 'conversation';
    if (eventType.startsWith('chat.')) return 'chat';
    return 'all';
  };

  const formatTimestamp = (timestamp: number): string => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);

    if (diffSecs < 60) return `${diffSecs}s ago`;
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return date.toLocaleTimeString();
  };

  return (
    <Card className="p-4 h-full flex flex-col">
      <h3 className="text-sm font-semibold text-gray-900 mb-3">
        Recent Events ({events.length})
      </h3>

      <ScrollArea className="flex-1">
        <div className="space-y-2">
          {recentEvents.length === 0 ? (
            <div className="text-center text-gray-500 text-sm py-8">
              No events yet. Waiting for activity...
            </div>
          ) : (
            recentEvents.map((event) => {
              const category = getEventCategory(event.eventType);
              const color = graphTransformer.getCategoryColor(category as any);

              return (
                <div
                  key={event.eventId}
                  className="flex items-start gap-2 p-2 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="text-lg flex-shrink-0">
                    {getEventIcon(event.eventType)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-2 h-2 rounded-full flex-shrink-0"
                        style={{ backgroundColor: color }}
                      />
                      <div className="text-xs font-medium text-gray-900 truncate">
                        {event.eventType}
                      </div>
                    </div>
                    <div className="text-xs text-gray-500 truncate mt-0.5">
                      User: {event.userId.slice(0, 12)}...
                    </div>
                    <div className="text-xs text-gray-400 mt-0.5">
                      {formatTimestamp(event.timestamp)}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </ScrollArea>
    </Card>
  );
}
