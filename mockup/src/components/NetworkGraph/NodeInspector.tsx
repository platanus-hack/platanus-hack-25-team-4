import { Card } from '../ui/card';
import { ScrollArea } from '../ui/scroll-area';
import type { GraphNode } from '../../types/observer.types';
import { graphTransformer } from '../../services/graphTransformer';

interface NodeInspectorProps {
  node: GraphNode | null;
  onClose: () => void;
}

export function NodeInspector({ node, onClose }: NodeInspectorProps) {
  if (!node) return null;

  const color = graphTransformer.getCategoryColor(node.category);

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-white border-l border-gray-200 shadow-xl z-50">
      <Card className="h-full rounded-none border-0 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">
            Node Details
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
            aria-label="Close"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        <ScrollArea className="flex-1">
          <div className="p-4 space-y-4">
            {/* Node Identity */}
            <div>
              <div className="flex items-center gap-2 mb-2">
                <div
                  className="w-4 h-4 rounded-full"
                  style={{ backgroundColor: color }}
                />
                <h4 className="font-semibold text-gray-900">{node.label}</h4>
              </div>
              <div className="text-sm text-gray-500 space-y-1">
                <div>ID: {node.id}</div>
                <div>Type: {node.type}</div>
                <div>Category: {node.category}</div>
              </div>
            </div>

            {/* Activity Stats */}
            <div className="border-t pt-4">
              <h4 className="font-semibold text-gray-900 mb-2">Activity</h4>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Event Count</span>
                  <span className="font-medium text-gray-900">
                    {node.eventCount}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Last Active</span>
                  <span className="font-medium text-gray-900">
                    {new Date(node.lastActive).toLocaleString()}
                  </span>
                </div>
              </div>
            </div>

            {/* Metadata */}
            {Object.keys(node.metadata).length > 0 && (
              <div className="border-t pt-4">
                <h4 className="font-semibold text-gray-900 mb-2">Metadata</h4>
                <div className="bg-gray-50 rounded-lg p-3">
                  <pre className="text-xs text-gray-700 overflow-x-auto">
                    {JSON.stringify(node.metadata, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {/* Visual Properties */}
            <div className="border-t pt-4">
              <h4 className="font-semibold text-gray-900 mb-2">
                Visual Properties
              </h4>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Color</span>
                  <div className="flex items-center gap-2">
                    <div
                      className="w-4 h-4 rounded border"
                      style={{ backgroundColor: color }}
                    />
                    <span className="font-mono text-xs">{color}</span>
                  </div>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Radius</span>
                  <span className="font-medium text-gray-900">
                    {graphTransformer.getNodeRadius(node.eventCount)}px
                  </span>
                </div>
                {node.x !== undefined && node.y !== undefined && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Position</span>
                    <span className="font-mono text-xs">
                      ({Math.round(node.x)}, {Math.round(node.y)})
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </ScrollArea>
      </Card>
    </div>
  );
}
