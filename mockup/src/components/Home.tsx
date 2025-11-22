import { MapPin, Plus, Zap, Clock, User } from 'lucide-react';
import { Button } from './ui/button';
import { motion } from 'motion/react';

interface Circle {
  id: string;
  objective: string;
  radius: number;
  expiresAt: Date;
  status: 'active' | 'paused';
}

interface HomeProps {
  circles: Circle[];
  onCreateCircle: () => void;
  onMatchFound: () => void;
  onNavigate: (view: 'home' | 'profile') => void;
}

export function Home({ circles, onCreateCircle, onMatchFound, onNavigate }: HomeProps) {
  const formatTimeRemaining = (expiresAt: Date) => {
    const now = new Date();
    const diff = expiresAt.getTime() - now.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 24) {
      return `${Math.floor(hours / 24)}d ${hours % 24}h`;
    }
    return `${hours}h ${minutes}m`;
  };

  return (
    <div className="h-full flex flex-col bg-[#F6F7FC]">
      {/* Header */}
      <div className="bg-gradient-to-r from-[#5B5FEE] to-[#FF8A3D] px-6 pt-16 pb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-white/80 mb-1">Welcome back</h2>
            <h1 className="text-white">Your Circles</h1>
          </div>
          <button
            onClick={() => onNavigate('profile')}
            className="w-12 h-12 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center"
          >
            <User className="w-6 h-6 text-white" />
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-white/20 backdrop-blur-sm rounded-2xl p-4">
            <div className="text-white/80 mb-1">Active</div>
            <div className="text-white">{circles.filter(c => c.status === 'active').length}</div>
          </div>
          <div className="bg-white/20 backdrop-blur-sm rounded-2xl p-4">
            <div className="text-white/80 mb-1">Matches</div>
            <div className="text-white">3</div>
          </div>
          <div className="bg-white/20 backdrop-blur-sm rounded-2xl p-4">
            <div className="text-white/80 mb-1">Nearby</div>
            <div className="text-white">12</div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 px-6 py-6 overflow-auto">
        {circles.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full py-12">
            <div className="w-20 h-20 rounded-full bg-[#5B5FEE]/10 flex items-center justify-center mb-6">
              <MapPin className="w-10 h-10 text-[#5B5FEE]" />
            </div>
            <h3 className="text-[#1A1A1A] mb-2">No Active Circles</h3>
            <p className="text-[#525866] text-center max-w-xs mb-8">
              Create your first Circle to start connecting with people nearby who share your objectives.
            </p>
            <Button
              onClick={onCreateCircle}
              className="bg-[#5B5FEE] hover:bg-[#5B5FEE]/90 h-14 px-8 rounded-2xl"
              size="lg"
            >
              <Plus className="mr-2 w-5 h-5" />
              Create Circle
            </Button>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[#1A1A1A]">Active Circles</h3>
              <Button
                onClick={onCreateCircle}
                className="bg-[#5B5FEE] hover:bg-[#5B5FEE]/90 h-10 px-4 rounded-xl"
                size="sm"
              >
                <Plus className="w-4 h-4" />
              </Button>
            </div>

            <div className="space-y-3">
              {circles.map((circle, index) => (
                <motion.div
                  key={circle.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="bg-white rounded-2xl p-5 shadow-sm border border-[#5B5FEE]/10"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <p className="text-[#1A1A1A] mb-2">{circle.objective}</p>
                      <div className="flex items-center gap-4 text-[#525866]">
                        <div className="flex items-center gap-1">
                          <MapPin className="w-4 h-4" />
                          <span>{circle.radius}m</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          <span>{formatTimeRemaining(circle.expiresAt)}</span>
                        </div>
                      </div>
                    </div>
                    <div className={`px-3 py-1 rounded-full ${
                      circle.status === 'active' 
                        ? 'bg-[#34D1BF]/10 text-[#34D1BF]' 
                        : 'bg-[#525866]/10 text-[#525866]'
                    }`}>
                      {circle.status}
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-3 border-t border-[#F6F7FC]">
                    <div className="flex items-center gap-2 text-[#525866]">
                      <Zap className="w-4 h-4 text-[#FFD66B]" />
                      <span>2 potential matches nearby</span>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Demo match button */}
            <Button
              onClick={onMatchFound}
              className="w-full mt-6 bg-[#FF8A3D] hover:bg-[#FF8A3D]/90 h-14 rounded-2xl"
              size="lg"
            >
              <Zap className="mr-2 w-5 h-5" />
              View Match (Demo)
            </Button>
          </>
        )}
      </div>
    </div>
  );
}
