import { motion } from 'motion/react';
import { Sparkles, MapPin, Check, X, MessageCircle } from 'lucide-react';
import { Button } from './ui/button';
import { ImageWithFallback } from './figma/ImageWithFallback';

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

interface MatchCardProps {
  match: Match;
  onAccept: () => void;
  onDecline: () => void;
}

export function MatchCard({ match, onAccept, onDecline }: MatchCardProps) {
  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-[#5B5FEE]/5 to-[#FF8A3D]/5">
      {/* Header */}
      <div className="px-6 pt-16 pb-6">
        <div className="flex items-center gap-2 mb-2">
          <Sparkles className="w-5 h-5 text-[#5B5FEE]" />
          <span className="text-[#5B5FEE]">
            {match.type === 'match' ? 'Match Found' : 'Soft Match'}
          </span>
        </div>
        <h1 className="text-[#1A1A1A]">Your agent found someone</h1>
      </div>

      {/* Content */}
      <div className="flex-1 px-6 overflow-auto">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4 }}
          className="space-y-6"
        >
          {/* Profile Card */}
          <div className="bg-white rounded-3xl overflow-hidden shadow-lg">
            {/* Avatar */}
            <div className="relative h-80 bg-gradient-to-br from-[#5B5FEE] to-[#FF8A3D]">
              <ImageWithFallback
                src={match.avatar}
                alt={match.name}
                className="w-full h-full object-cover"
              />
              {/* Compatibility badge */}
              <div className="absolute top-4 right-4 bg-white/95 backdrop-blur-sm rounded-full px-4 py-2 shadow-lg">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-[#34D1BF]" />
                  <span className="text-[#1A1A1A]">{match.compatibility}% Match</span>
                </div>
              </div>
            </div>

            {/* Info */}
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-[#1A1A1A] mb-1">{match.name}</h2>
                  <div className="flex items-center gap-2 text-[#525866]">
                    <span>{match.age} years old</span>
                    <span>•</span>
                    <div className="flex items-center gap-1">
                      <MapPin className="w-4 h-4" />
                      <span>Nearby</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Agent explanation */}
              <div className="bg-[#5B5FEE]/5 rounded-2xl p-4 border border-[#5B5FEE]/10">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-[#5B5FEE] flex items-center justify-center flex-shrink-0 mt-1">
                    <Sparkles className="w-4 h-4 text-white" />
                  </div>
                  <div>
                    <div className="text-[#5B5FEE] mb-2">Your Agent Says</div>
                    <p className="text-[#1A1A1A] leading-relaxed">{match.explanation}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Suggested opener */}
          <div className="bg-white rounded-2xl p-5 shadow-sm">
            <div className="flex items-center gap-2 mb-3">
              <MessageCircle className="w-5 h-5 text-[#FF8A3D]" />
              <span className="text-[#1A1A1A]">Suggested Opener</span>
            </div>
            <p className="text-[#525866] leading-relaxed">{match.suggestedOpener}</p>
          </div>

          {/* Type indicator */}
          {match.type === 'soft-match' && (
            <div className="bg-[#FFD66B]/10 rounded-2xl p-4 border border-[#FFD66B]/20">
              <p className="text-[#525866]">
                This is a soft match. They haven't created a Circle for this activity, but it aligns with their interests. They'll need to accept before you can chat.
              </p>
            </div>
          )}
        </motion.div>
      </div>

      {/* Actions */}
      <div className="px-6 pb-8 pt-4">
        <div className="flex gap-3">
          <Button
            onClick={onDecline}
            variant="outline"
            className="flex-1 h-14 rounded-2xl border-2 border-[#525866]/20 text-[#525866] hover:bg-[#525866]/5"
            size="lg"
          >
            <X className="mr-2 w-5 h-5" />
            Not Now
          </Button>
          <Button
            onClick={onAccept}
            className="flex-1 bg-[#34D1BF] hover:bg-[#34D1BF]/90 h-14 rounded-2xl"
            size="lg"
          >
            <Check className="mr-2 w-5 h-5" />
            Connect
          </Button>
        </div>
      </div>
    </div>
  );
}
