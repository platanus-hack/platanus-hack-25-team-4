import { useState } from 'react';
import { ArrowLeft, MapPin, Clock, Target } from 'lucide-react';
import { Button } from './ui/button';
import { Slider } from './ui/slider';

interface CreateCircleProps {
  onBack: () => void;
  onCreate: (circle: { objective: string; radius: number; expiresAt: Date }) => void;
}

export function CreateCircle({ onBack, onCreate }: CreateCircleProps) {
  const [objective, setObjective] = useState('');
  const [radius, setRadius] = useState([500]);
  const [duration, setDuration] = useState([2]);

  const handleCreate = () => {
    if (objective.trim()) {
      const expiresAt = new Date();
      expiresAt.setHours(expiresAt.getHours() + duration[0]);
      
      onCreate({
        objective: objective.trim(),
        radius: radius[0],
        expiresAt,
      });
    }
  };

  const isValid = objective.trim().length > 10;

  return (
    <div className="h-full flex flex-col bg-[#F6F7FC]">
      {/* Header */}
      <div className="bg-gradient-to-r from-[#5B5FEE] to-[#FF8A3D] px-6 pt-16 pb-8">
        <button
          onClick={onBack}
          className="w-10 h-10 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center mb-6"
        >
          <ArrowLeft className="w-5 h-5 text-white" />
        </button>
        <h1 className="text-white mb-2">Create Circle</h1>
        <p className="text-white/80">Define your objective and let your AI agent find the right connections.</p>
      </div>

      {/* Form */}
      <div className="flex-1 px-6 py-6 overflow-auto">
        <div className="space-y-6">
          {/* Objective */}
          <div className="bg-white rounded-2xl p-5 shadow-sm">
            <div className="flex items-center gap-2 mb-3">
              <Target className="w-5 h-5 text-[#5B5FEE]" />
              <label className="text-[#1A1A1A]">What's your objective?</label>
            </div>
            <textarea
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              placeholder="E.g., Find someone to play tennis in Palermo between 6pm-8pm"
              className="w-full h-32 px-4 py-3 bg-[#F6F7FC] rounded-xl border-0 resize-none text-[#1A1A1A] placeholder:text-[#525866]"
              maxLength={200}
            />
            <div className="flex justify-between mt-2">
              <span className="text-[#525866]">Be specific to help your agent</span>
              <span className={`${
                objective.length < 10 ? 'text-[#FF8A3D]' : 'text-[#34D1BF]'
              }`}>
                {objective.length}/200
              </span>
            </div>
          </div>

          {/* Radius */}
          <div className="bg-white rounded-2xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <MapPin className="w-5 h-5 text-[#5B5FEE]" />
                <label className="text-[#1A1A1A]">Radius</label>
              </div>
              <span className="text-[#5B5FEE]">{radius[0]}m</span>
            </div>
            <Slider
              value={radius}
              onValueChange={setRadius}
              min={100}
              max={3000}
              step={100}
              className="w-full"
            />
            <div className="flex justify-between mt-2 text-[#525866]">
              <span>100m</span>
              <span>3000m</span>
            </div>
          </div>

          {/* Duration */}
          <div className="bg-white rounded-2xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Clock className="w-5 h-5 text-[#5B5FEE]" />
                <label className="text-[#1A1A1A]">Duration</label>
              </div>
              <span className="text-[#5B5FEE]">
                {duration[0] < 24 ? `${duration[0]}h` : `${Math.floor(duration[0] / 24)}d`}
              </span>
            </div>
            <Slider
              value={duration}
              onValueChange={setDuration}
              min={1}
              max={168}
              step={1}
              className="w-full"
            />
            <div className="flex justify-between mt-2 text-[#525866]">
              <span>1h</span>
              <span>7d</span>
            </div>
          </div>

          {/* Info card */}
          <div className="bg-[#FFD66B]/10 rounded-2xl p-4 border border-[#FFD66B]/20">
            <p className="text-[#525866]">
              Your AI agent will monitor this Circle and notify you when it finds promising connections that match your objective.
            </p>
          </div>
        </div>
      </div>

      {/* Create button */}
      <div className="px-6 pb-8">
        <Button
          onClick={handleCreate}
          disabled={!isValid}
          className="w-full bg-[#5B5FEE] hover:bg-[#5B5FEE]/90 disabled:bg-[#525866]/20 h-14 rounded-2xl"
          size="lg"
        >
          Create Circle
        </Button>
      </div>
    </div>
  );
}
