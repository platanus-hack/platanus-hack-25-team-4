import { ArrowLeft, User, MapPin, Shield, Bell, LogOut, Sparkles } from 'lucide-react';
import { Button } from './ui/button';
import { ImageWithFallback } from './figma/ImageWithFallback';

interface ProfileProps {
  onBack: () => void;
}

export function Profile({ onBack }: ProfileProps) {
  const interests = [
    'Tennis', 'AI & Technology', 'Outdoor Sports', 
    'Coffee Culture', 'Startups', 'Fitness'
  ];

  return (
    <div className="h-full flex flex-col bg-[#F6F7FC]">
      {/* Header */}
      <div className="bg-gradient-to-r from-[#5B5FEE] to-[#FF8A3D] px-6 pt-16 pb-24">
        <button
          onClick={onBack}
          className="w-10 h-10 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center mb-6"
        >
          <ArrowLeft className="w-5 h-5 text-white" />
        </button>
        <h1 className="text-white">Profile</h1>
      </div>

      {/* Content */}
      <div className="flex-1 px-6 -mt-16 overflow-auto pb-6">
        {/* Profile Card */}
        <div className="bg-white rounded-3xl shadow-lg p-6 mb-6">
          <div className="flex items-start gap-4 mb-6">
            <ImageWithFallback
              src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400"
              alt="Profile"
              className="w-20 h-20 rounded-full object-cover"
            />
            <div className="flex-1">
              <h2 className="text-[#1A1A1A] mb-1">Jordan Smith</h2>
              <p className="text-[#525866] mb-3">28 years old • Buenos Aires</p>
              <Button
                variant="outline"
                className="h-9 rounded-xl border-[#5B5FEE] text-[#5B5FEE] hover:bg-[#5B5FEE]/5"
                size="sm"
              >
                Edit Profile
              </Button>
            </div>
          </div>

          {/* Agent Status */}
          <div className="bg-[#5B5FEE]/5 rounded-2xl p-4 border border-[#5B5FEE]/10">
            <div className="flex items-center gap-3 mb-2">
              <Sparkles className="w-5 h-5 text-[#5B5FEE]" />
              <span className="text-[#5B5FEE]">AI Agent Active</span>
            </div>
            <p className="text-[#525866]">
              Your agent is monitoring 2 active Circles and has made 3 successful matches this month.
            </p>
          </div>
        </div>

        {/* Interests */}
        <div className="bg-white rounded-2xl shadow-sm p-5 mb-6">
          <h3 className="text-[#1A1A1A] mb-4">Interests</h3>
          <div className="flex flex-wrap gap-2">
            {interests.map((interest) => (
              <div
                key={interest}
                className="px-4 py-2 bg-[#5B5FEE]/10 text-[#5B5FEE] rounded-full"
              >
                {interest}
              </div>
            ))}
          </div>
          <Button
            variant="ghost"
            className="w-full mt-4 text-[#5B5FEE] hover:bg-[#5B5FEE]/5"
            size="sm"
          >
            Manage Interests
          </Button>
        </div>

        {/* Settings */}
        <div className="bg-white rounded-2xl shadow-sm overflow-hidden mb-6">
          <button className="w-full flex items-center gap-4 p-5 hover:bg-[#F6F7FC] transition-colors border-b border-[#F6F7FC]">
            <MapPin className="w-5 h-5 text-[#525866]" />
            <div className="flex-1 text-left">
              <div className="text-[#1A1A1A]">Location Settings</div>
              <div className="text-[#525866]">Manage location permissions</div>
            </div>
          </button>

          <button className="w-full flex items-center gap-4 p-5 hover:bg-[#F6F7FC] transition-colors border-b border-[#F6F7FC]">
            <Shield className="w-5 h-5 text-[#525866]" />
            <div className="flex-1 text-left">
              <div className="text-[#1A1A1A]">Privacy & Safety</div>
              <div className="text-[#525866]">Control your data and boundaries</div>
            </div>
          </button>

          <button className="w-full flex items-center gap-4 p-5 hover:bg-[#F6F7FC] transition-colors border-b border-[#F6F7FC]">
            <Bell className="w-5 h-5 text-[#525866]" />
            <div className="flex-1 text-left">
              <div className="text-[#1A1A1A]">Notifications</div>
              <div className="text-[#525866]">Manage alerts and updates</div>
            </div>
          </button>

          <button className="w-full flex items-center gap-4 p-5 hover:bg-[#F6F7FC] transition-colors">
            <User className="w-5 h-5 text-[#525866]" />
            <div className="flex-1 text-left">
              <div className="text-[#1A1A1A]">Agent Settings</div>
              <div className="text-[#525866]">Customize your AI persona</div>
            </div>
          </button>
        </div>

        {/* Logout */}
        <Button
          variant="outline"
          className="w-full h-14 rounded-2xl border-2 border-[#FF8A3D]/20 text-[#FF8A3D] hover:bg-[#FF8A3D]/5"
          size="lg"
        >
          <LogOut className="mr-2 w-5 h-5" />
          Log Out
        </Button>
      </div>
    </div>
  );
}
