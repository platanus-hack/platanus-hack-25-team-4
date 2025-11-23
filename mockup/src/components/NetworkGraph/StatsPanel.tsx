import type { ObserverStats } from '../../types/observer.types';
import { Card } from '../ui/card';

interface StatsPanelProps {
  stats: ObserverStats | null;
  loading: boolean;
}

export function StatsPanel({ stats, loading }: StatsPanelProps) {
  if (loading || !stats) {
    return (
      <Card className="p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-3 gap-4">
            <div className="h-16 bg-gray-200 rounded"></div>
            <div className="h-16 bg-gray-200 rounded"></div>
            <div className="h-16 bg-gray-200 rounded"></div>
          </div>
        </div>
      </Card>
    );
  }

  const circuitStateColor = {
    closed: 'text-green-600 bg-green-50',
    open: 'text-red-600 bg-red-50',
    half_open: 'text-yellow-600 bg-yellow-50',
  }[stats.observer.circuitState];

  return (
    <Card className="p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        Network Statistics
      </h2>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-blue-50 rounded-lg p-4">
          <div className="text-2xl font-bold text-blue-600">
            {stats.stats.uniqueUsers.toLocaleString()}
          </div>
          <div className="text-sm text-blue-600/70">Active Users</div>
        </div>

        <div className="bg-purple-50 rounded-lg p-4">
          <div className="text-2xl font-bold text-purple-600">
            {stats.stats.totalEvents.toLocaleString()}
          </div>
          <div className="text-sm text-purple-600/70">Total Events</div>
        </div>

        <div className="bg-green-50 rounded-lg p-4">
          <div className="text-2xl font-bold text-green-600">
            {stats.stats.activeConversations.toLocaleString()}
          </div>
          <div className="text-sm text-green-600/70">Conversations</div>
        </div>
      </div>

      <div className="border-t pt-4 space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Observer Status</span>
          <span
            className={`px-2 py-1 rounded-full text-xs font-medium ${circuitStateColor}`}
          >
            {stats.observer.circuitState.replace('_', ' ').toUpperCase()}
          </span>
        </div>

        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Buffer Size</span>
          <span className="font-medium text-gray-900">
            {stats.observer.bufferSize}
          </span>
        </div>

        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Success Rate</span>
          <span className="font-medium text-gray-900">
            {stats.observer.successCount + stats.observer.failureCount > 0
              ? (
                  (stats.observer.successCount /
                    (stats.observer.successCount +
                      stats.observer.failureCount)) *
                  100
                ).toFixed(1)
              : '0.0'}
            %
          </span>
        </div>
      </div>
    </Card>
  );
}
