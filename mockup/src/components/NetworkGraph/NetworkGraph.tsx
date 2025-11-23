import { useState, useMemo } from 'react';
import { NetworkGraphCanvas } from './NetworkGraphCanvas';
import type {
  GraphData,
  GraphNode,
  ObserverEvent,
} from '../../types/observer.types';
import { graphTransformer } from '../../services/graphTransformer';

interface NetworkGraphProps {
  events: ObserverEvent[];
  width?: number;
  height?: number;
  onNodeSelect?: (node: GraphNode | null) => void;
}

export function NetworkGraph({
  events,
  width = 800,
  height = 600,
  onNodeSelect,
}: NetworkGraphProps) {
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);

  // Transform events to graph data
  const graphData: GraphData = useMemo(() => {
    return graphTransformer.transform(events);
  }, [events]);

  const handleNodeClick = (node: GraphNode) => {
    onNodeSelect?.(node);
  };

  const handleNodeHover = (node: GraphNode | null) => {
    setHoveredNode(node);
  };

  return (
    <div className="relative">
      <NetworkGraphCanvas
        data={graphData}
        width={width}
        height={height}
        onNodeClick={handleNodeClick}
        onNodeHover={handleNodeHover}
      />

      {/* Tooltip for hovered node */}
      {hoveredNode && (
        <div className="absolute top-4 left-4 bg-white border border-gray-200 rounded-lg shadow-lg p-3 max-w-xs z-10">
          <div className="text-sm font-semibold text-gray-900">
            {hoveredNode.label}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Type: {hoveredNode.type}
          </div>
          <div className="text-xs text-gray-500">
            Events: {hoveredNode.eventCount}
          </div>
          <div className="text-xs text-gray-500">
            Last active: {new Date(hoveredNode.lastActive).toLocaleTimeString()}
          </div>
        </div>
      )}

      {/* Graph info */}
      <div className="absolute bottom-4 left-4 bg-white/90 border border-gray-200 rounded-lg shadow px-3 py-2">
        <div className="text-xs text-gray-600">
          Nodes: <span className="font-semibold">{graphData.nodes.length}</span>{' '}
          | Edges: <span className="font-semibold">{graphData.edges.length}</span>
        </div>
      </div>

      {/* Instructions */}
      <div className="absolute bottom-4 right-4 bg-white/90 border border-gray-200 rounded-lg shadow px-3 py-2">
        <div className="text-xs text-gray-600">
          <div>Click & drag nodes to reposition</div>
          <div>Scroll to zoom • Click nodes for details</div>
        </div>
      </div>
    </div>
  );
}
