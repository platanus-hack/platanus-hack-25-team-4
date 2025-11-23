# Network Observatory Dashboard

An interactive web-based visualization of network activity built with React, D3.js, and TypeScript.

## Overview

The Network Observatory Dashboard provides real-time visualization of observer events from your backend API. It displays user locations, collisions, missions, matches, conversations, and chats in an interactive force-directed graph.

## Features

### Core Functionality
- **Real-time Updates**: Polls observer API every 3-5 seconds for new events
- **Interactive Graph**: D3.js force-directed layout with zoom, pan, and drag
- **Event Filtering**: Toggle event categories on/off to focus on specific activity
- **Live Statistics**: Displays unique users, total events, and active conversations
- **Event Feed**: Scrollable sidebar showing recent events in real-time
- **Node Inspector**: Click any node to view detailed information

### Visual Design
Event types are color-coded for easy identification:
- **Location** (📍): Blue (#3B82F6)
- **Collision** (💥): Red (#EF4444)
- **Mission** (🎯): Purple (#A855F7)
- **Agent Match** (🤝): Purple (#A855F7)
- **Match** (❤️): Pink (#EC4899)
- **Conversation** (💬): Green (#10B981)
- **Chat** (💭): Cyan (#06B6D4)

### Keyboard Shortcuts
- **Space**: Pause/Resume updates
- **Escape**: Close node inspector
- **Cmd/Ctrl + E**: Export data to JSON

## Getting Started

### Prerequisites
- Backend observer API running at `http://localhost:3000/api/observer`
- Node.js 18+ and npm installed

### Installation

Dependencies are already installed. If you need to reinstall:
```bash
cd /path/to/mockup
npm install
```

### Running the Dashboard

**Development mode:**
```bash
cd /path/to/mockup
npm run dev
```

Then navigate to `http://localhost:5173/dashboard`

**Production build:**
```bash
cd /path/to/mockup
npm run build
```

The built files will be in `mockup/build/`

## Architecture

### File Structure
```
mockup/src/
├── pages/
│   └── Dashboard.tsx              # Main dashboard page
├── components/
│   └── NetworkGraph/
│       ├── NetworkGraph.tsx       # Graph container with tooltips
│       ├── NetworkGraphCanvas.tsx # D3.js force simulation
│       ├── StatsPanel.tsx         # Aggregated metrics display
│       ├── EventFeed.tsx          # Live event stream
│       ├── FilterControls.tsx     # Event type filters
│       └── NodeInspector.tsx      # Node detail panel
├── hooks/
│   └── useObserverData.ts         # Polling hook for API data
├── services/
│   ├── observerApiClient.ts       # API client for observer endpoints
│   └── graphTransformer.ts        # Transform events to graph data
└── types/
    └── observer.types.ts          # TypeScript type definitions
```

### Data Flow

1. **Polling**: `useObserverData` hook fetches data every 3-5s
2. **Transform**: `graphTransformer` converts events to D3 nodes/edges
3. **Render**: `NetworkGraphCanvas` displays force-directed graph
4. **Interact**: User clicks, hovers, or filters
5. **Update**: Components re-render with new data

## API Configuration

The dashboard expects the following endpoints:

### GET `/api/observer/stats`
Returns aggregated statistics:
```json
{
  "stats": {
    "uniqueUsers": 42,
    "totalEvents": 1247,
    "activeConversations": 15
  },
  "observer": {
    "bufferSize": 23,
    "circuitState": "closed",
    "failureCount": 0,
    "successCount": 458
  }
}
```

### GET `/api/observer/events/:type?limit=N`
Returns recent events by type (`all`, `location`, `collision`, etc.):
```json
{
  "events": [
    {
      "eventId": "01HX...",
      "eventType": "collision.detected",
      "userId": "user-123",
      "timestamp": 1234567890,
      "metadata": { ... }
    }
  ],
  "count": 42,
  "type": "collision"
}
```

### GET `/api/observer/users/:userId/activity?limit=N`
Returns activity for a specific user.

### Changing API Base URL

Edit `mockup/src/services/observerApiClient.ts`:
```typescript
const observerApi = new ObserverApiClient('http://your-api-url/api/observer');
```

## Usage Guide

### Viewing the Dashboard

1. Start your backend server with observer enabled
2. Start the mockup dev server: `npm run dev`
3. Navigate to `http://localhost:5173/dashboard`

### Interacting with the Graph

**Zoom & Pan:**
- Scroll to zoom in/out
- Click and drag background to pan

**Nodes:**
- Click and drag nodes to reposition
- Click nodes to open inspector
- Hover for quick details

**Filters:**
- Use left sidebar to toggle event types
- Toggle "Pause Updates" to freeze the graph
- Click "Enable All" or "Disable All" for quick filtering

**Export:**
- Click "Export Data" button (or Cmd/Ctrl+E)
- Downloads JSON with current stats and events

### Understanding the Visualization

**Node Types:**
- **User nodes**: Circles representing users (most common)
- **Mission nodes**: Stars representing missions
- **Conversation nodes**: Speech bubbles for conversations

**Node Size:**
- Larger nodes = more events associated
- Size range: 5px to 20px radius

**Edge Thickness:**
- Thicker edges = more events between nodes
- Edge width: 1px to 5px

**Edge Types:**
- Solid lines: Most relationships
- Arrows indicate directionality

## Performance

- **Recommended max events**: 200 events (configurable in `useObserverData`)
- **Polling intervals**: 3s (events), 5s (stats)
- **Graph capacity**: Up to 10,000 nodes (D3 WebGL rendering)

To reduce load:
1. Decrease `eventsLimit` in Dashboard.tsx
2. Increase polling intervals in `useObserverData`
3. Enable fewer event filters

## Troubleshooting

### Dashboard shows "No events to display"
- Check backend is running at `http://localhost:3000`
- Verify observer endpoints are accessible
- Check browser console for API errors
- Ensure at least one event filter is enabled

### Graph is frozen
- Check if "Pause Updates" is enabled
- Press Space to resume
- Check for JavaScript errors in console

### Events not updating
- Verify polling is active (not paused)
- Check network tab for failed API requests
- Ensure backend observer system is processing events

### Build warnings about chunk size
- Normal with D3.js (~500KB minified)
- Optional: Implement code splitting for production

## Development

### Adding New Event Types

1. Add event type to `types/observer.types.ts`:
```typescript
export type EventType =
  | 'location.updated'
  | 'your.new.event'  // Add here
```

2. Add category mapping in `graphTransformer.ts`:
```typescript
private getEventCategory(eventType: string): EventCategory {
  if (eventType.startsWith('yournew.')) return 'yournew';
  // ...
}
```

3. Add color in `graphTransformer.ts`:
```typescript
getCategoryColor(category: EventCategory): string {
  const colorMap = {
    yournew: '#HEXCOLOR',
    // ...
  };
}
```

4. Add filter option in `FilterControls.tsx`

### Customizing Appearance

**Colors**: Edit `graphTransformer.ts` `getCategoryColor()`
**Node sizes**: Edit `graphTransformer.ts` `getNodeRadius()`
**Force strength**: Edit `NetworkGraphCanvas.tsx` force simulation params
**Polling intervals**: Edit `Dashboard.tsx` `useObserverData()` options

## Credits

Built with:
- **React 18**: UI framework
- **D3.js v7**: Data visualization
- **TypeScript**: Type safety
- **Vite**: Build tool
- **Axios**: HTTP client
- **Radix UI**: UI components
- **Tailwind CSS**: Styling

## License

Part of the Platanus Hack 2025 Team 4 project.
