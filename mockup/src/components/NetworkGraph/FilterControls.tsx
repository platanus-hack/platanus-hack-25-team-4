import { Card } from '../ui/card';
import { Switch } from '../ui/switch';
import { Label } from '../ui/label';
import type { EventCategory } from '../../types/observer.types';
import { graphTransformer } from '../../services/graphTransformer';

interface FilterControlsProps {
  activeFilters: Set<EventCategory>;
  onFilterChange: (category: EventCategory, enabled: boolean) => void;
  isPaused: boolean;
  onPauseToggle: () => void;
}

const FILTER_OPTIONS: Array<{
  category: EventCategory;
  label: string;
  icon: string;
}> = [
  { category: 'location', label: 'Location', icon: '📍' },
  { category: 'collision', label: 'Collision', icon: '💥' },
  { category: 'mission', label: 'Mission', icon: '🎯' },
  { category: 'agent_match', label: 'Agent Match', icon: '🤝' },
  { category: 'match', label: 'Match', icon: '❤️' },
  { category: 'conversation', label: 'Conversation', icon: '💬' },
  { category: 'chat', label: 'Chat', icon: '💭' },
];

export function FilterControls({
  activeFilters,
  onFilterChange,
  isPaused,
  onPauseToggle,
}: FilterControlsProps) {
  return (
    <Card className="p-4">
      <h3 className="text-sm font-semibold text-gray-900 mb-4">
        Event Filters
      </h3>

      <div className="space-y-3 mb-4">
        {FILTER_OPTIONS.map(({ category, label, icon }) => {
          const isActive = activeFilters.has(category);
          const color = graphTransformer.getCategoryColor(category);

          return (
            <div key={category} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span>{icon}</span>
                <Label
                  htmlFor={`filter-${category}`}
                  className="text-sm cursor-pointer"
                >
                  {label}
                </Label>
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: color }}
                />
              </div>
              <Switch
                id={`filter-${category}`}
                checked={isActive}
                onCheckedChange={(checked: boolean) =>
                  onFilterChange(category, checked)
                }
              />
            </div>
          );
        })}
      </div>

      <div className="border-t pt-4">
        <div className="flex items-center justify-between">
          <Label htmlFor="pause-polling" className="text-sm cursor-pointer">
            {isPaused ? 'Resume Updates' : 'Pause Updates'}
          </Label>
          <Switch
            id="pause-polling"
            checked={!isPaused}
            onCheckedChange={onPauseToggle}
          />
        </div>
        <p className="text-xs text-gray-500 mt-2">
          {isPaused
            ? 'Updates are paused'
            : 'Polling every 3-5 seconds'}
        </p>
      </div>

      <div className="border-t pt-4 mt-4">
        <button
          onClick={() => {
            const allCategories: EventCategory[] = [
              'location',
              'collision',
              'mission',
              'agent_match',
              'match',
              'conversation',
              'chat',
            ];
            allCategories.forEach((cat) => onFilterChange(cat, true));
          }}
          className="text-xs text-blue-600 hover:text-blue-700 font-medium"
        >
          Enable All
        </button>
        {' | '}
        <button
          onClick={() => {
            const allCategories: EventCategory[] = [
              'location',
              'collision',
              'mission',
              'agent_match',
              'match',
              'conversation',
              'chat',
            ];
            allCategories.forEach((cat) => onFilterChange(cat, false));
          }}
          className="text-xs text-gray-600 hover:text-gray-700 font-medium"
        >
          Disable All
        </button>
      </div>
    </Card>
  );
}
