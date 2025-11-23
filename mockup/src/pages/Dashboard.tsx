import { useState, useMemo, useEffect } from 'react';
import { useObserverData } from '../hooks/useObserverData';
import { NetworkGraph } from '../components/NetworkGraph/NetworkGraph';
import { StatsPanel } from '../components/NetworkGraph/StatsPanel';
import { EventFeed } from '../components/NetworkGraph/EventFeed';
import { FilterControls } from '../components/NetworkGraph/FilterControls';
import { NodeInspector } from '../components/NetworkGraph/NodeInspector';
import type { EventCategory, GraphNode } from '../types/observer.types';

export function Dashboard() {
  const [activeFilters, setActiveFilters] = useState<Set<EventCategory>>(
    new Set(['location', 'collision', 'mission', 'agent_match', 'match', 'conversation', 'chat'])
  );
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  const {
    stats,
    events,
    loading,
    error,
    pause,
    resume,
    isPaused,
  } = useObserverData({
    statsInterval: 5000,
    eventsInterval: 3000,
    eventsLimit: 200,
    eventTypes: ['all'],
  });

  // Filter events based on active filters
  const filteredEvents = useMemo(() => {
    if (activeFilters.size === 0) return [];

    return events.filter((event) => {
      const category = event.eventType.split('.')[0] as EventCategory;
      return activeFilters.has(category);
    });
  }, [events, activeFilters]);

  const handleFilterChange = (category: EventCategory, enabled: boolean) => {
    setActiveFilters((prev) => {
      const next = new Set(prev);
      if (enabled) {
        next.add(category);
      } else {
        next.delete(category);
      }
      return next;
    });
  };

  const handlePauseToggle = () => {
    if (isPaused) {
      resume();
    } else {
      pause();
    }
  };

  const handleExportData = () => {
    const exportData = {
      timestamp: new Date().toISOString(),
      stats,
      events: filteredEvents.slice(0, 100),
    };

    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);

    const link = document.createElement('a');
    link.href = url;
    link.download = `network-data-${Date.now()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Space bar: pause/resume
      if (e.code === 'Space' && e.target === document.body) {
        e.preventDefault();
        handlePauseToggle();
      }
      // Escape: close node inspector
      if (e.code === 'Escape' && selectedNode) {
        setSelectedNode(null);
      }
      // E: export data
      if (e.code === 'KeyE' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        handleExportData();
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [isPaused, selectedNode]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b shadow-sm">
        <div className="max-w-screen-2xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Network Observatory
              </h1>
              <p className="text-sm text-gray-500 mt-1">
                Real-time visualization of network activity
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={handleExportData}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium flex items-center gap-2"
                title="Export data (Cmd/Ctrl + E)"
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                  />
                </svg>
                Export Data
              </button>

              {isPaused && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-2">
                  <div className="text-sm font-medium text-yellow-800">
                    Updates Paused
                  </div>
                </div>
              )}

              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-2">
                  <div className="text-sm font-medium text-red-800">
                    Error: {error.message}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Keyboard shortcuts help */}
          <div className="mt-3 pt-3 border-t">
            <div className="flex items-center gap-6 text-xs text-gray-500">
              <div className="flex items-center gap-1">
                <kbd className="px-2 py-0.5 bg-gray-100 border border-gray-300 rounded">Space</kbd>
                <span>Pause/Resume</span>
              </div>
              <div className="flex items-center gap-1">
                <kbd className="px-2 py-0.5 bg-gray-100 border border-gray-300 rounded">Esc</kbd>
                <span>Close Inspector</span>
              </div>
              <div className="flex items-center gap-1">
                <kbd className="px-2 py-0.5 bg-gray-100 border border-gray-300 rounded">⌘/Ctrl</kbd>
                <span>+</span>
                <kbd className="px-2 py-0.5 bg-gray-100 border border-gray-300 rounded">E</kbd>
                <span>Export</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-screen-2xl mx-auto px-6 py-6">
        {/* Stats Panel */}
        <div className="mb-6">
          <StatsPanel stats={stats} loading={loading} />
        </div>

        {/* Grid Layout */}
        <div className="grid grid-cols-12 gap-6">
          {/* Left Sidebar - Filters */}
          <div className="col-span-3">
            <FilterControls
              activeFilters={activeFilters}
              onFilterChange={handleFilterChange}
              isPaused={isPaused}
              onPauseToggle={handlePauseToggle}
            />
          </div>

          {/* Center - Graph */}
          <div className="col-span-6">
            <div className="bg-white rounded-lg shadow-sm p-4">
              {loading && events.length === 0 ? (
                <div className="flex items-center justify-center h-[600px]">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <div className="text-gray-600">Loading network data...</div>
                  </div>
                </div>
              ) : filteredEvents.length === 0 ? (
                <div className="flex items-center justify-center h-[600px]">
                  <div className="text-center text-gray-500">
                    <div className="text-6xl mb-4">📊</div>
                    <div className="font-medium">No events to display</div>
                    <div className="text-sm mt-2">
                      Adjust filters or wait for activity
                    </div>
                  </div>
                </div>
              ) : (
                <NetworkGraph
                  events={filteredEvents}
                  width={800}
                  height={600}
                  onNodeSelect={setSelectedNode}
                />
              )}
            </div>
          </div>

          {/* Right Sidebar - Events Feed */}
          <div className="col-span-3">
            <div className="h-[688px]">
              <EventFeed events={filteredEvents} maxEvents={100} />
            </div>
          </div>
        </div>
      </div>

      {/* Node Inspector Modal */}
      {selectedNode && (
        <NodeInspector
          node={selectedNode}
          onClose={() => setSelectedNode(null)}
        />
      )}
    </div>
  );
}
