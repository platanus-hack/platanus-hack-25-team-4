import { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Home } from './components/Home';
import { CreateCircle } from './components/CreateCircle';
import { MatchCard } from './components/MatchCard';
import { ChatView } from './components/ChatView';
import { Onboarding } from './components/Onboarding';
import { Profile } from './components/Profile';
import { Dashboard } from './pages/Dashboard';

type View = 'onboarding' | 'home' | 'create-circle' | 'match' | 'chat' | 'profile';

interface Circle {
  id: string;
  objective: string;
  radius: number;
  expiresAt: Date;
  status: 'active' | 'paused';
}

interface Match {
  id: string;
  name: string;
  age: number;
  avatar: string;
  explanation: string;
  compatibility: number;
  type: 'match' | 'soft-match';
  suggestedOpener: string;
}

function MobileApp() {
  const [currentView, setCurrentView] = useState<View>('onboarding');
  const [circles, setCircles] = useState<Circle[]>([]);
  const [selectedMatch, setSelectedMatch] = useState<Match | null>(null);

  const handleOnboardingComplete = () => {
    setCurrentView('home');
  };

  const handleCreateCircle = (circle: Omit<Circle, 'id' | 'status'>) => {
    const newCircle: Circle = {
      ...circle,
      id: Math.random().toString(36).substring(7),
      status: 'active',
    };
    setCircles([...circles, newCircle]);
    setCurrentView('home');
  };

  const handleMatchFound = (match: Match) => {
    setSelectedMatch(match);
    setCurrentView('match');
  };

  const handleAcceptMatch = () => {
    if (selectedMatch) {
      setCurrentView('chat');
    }
  };

  const handleDeclineMatch = () => {
    setSelectedMatch(null);
    setCurrentView('home');
  };

  const handleNavigation = (view: View) => {
    setCurrentView(view);
  };

  // Mock match for demo purposes
  const mockMatch: Match = {
    id: '1',
    name: 'Alex',
    age: 28,
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400',
    explanation: "I found someone nearby who also wants to play tennis this evening. They're roughly your age, live in your area, and share interests like outdoor sports and fitness. I think there's a good chance you'll get along if you play together today.",
    compatibility: 92,
    type: 'match',
    suggestedOpener: "Hey! I saw we're both looking to play tennis this evening. Want to hit some balls at the Palermo courts around 6pm?"
  };

  return (
    <div className="min-h-screen bg-[#F6F7FC] flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-3xl shadow-2xl overflow-hidden" style={{ height: '844px' }}>
        {currentView === 'onboarding' && (
          <Onboarding onComplete={handleOnboardingComplete} />
        )}
        {currentView === 'home' && (
          <Home
            circles={circles}
            onCreateCircle={() => setCurrentView('create-circle')}
            onMatchFound={() => handleMatchFound(mockMatch)}
            onNavigate={handleNavigation}
          />
        )}
        {currentView === 'create-circle' && (
          <CreateCircle
            onBack={() => setCurrentView('home')}
            onCreate={handleCreateCircle}
          />
        )}
        {currentView === 'match' && selectedMatch && (
          <MatchCard
            match={selectedMatch}
            onAccept={handleAcceptMatch}
            onDecline={handleDeclineMatch}
          />
        )}
        {currentView === 'chat' && selectedMatch && (
          <ChatView
            match={selectedMatch}
            onBack={() => setCurrentView('home')}
          />
        )}
        {currentView === 'profile' && (
          <Profile onBack={() => setCurrentView('home')} />
        )}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MobileApp />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
