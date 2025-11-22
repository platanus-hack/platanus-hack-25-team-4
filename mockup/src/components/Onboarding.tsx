import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Sparkles, MapPin, Shield, ArrowRight } from 'lucide-react';
import { Button } from './ui/button';

interface OnboardingProps {
  onComplete: () => void;
}

export function Onboarding({ onComplete }: OnboardingProps) {
  const [step, setStep] = useState(0);

  const screens = [
    {
      icon: Sparkles,
      title: 'Meet Through AI',
      description: 'Your personal AI agent finds meaningful connections based on your interests and real-world objectives.',
      color: '#5B5FEE',
    },
    {
      icon: MapPin,
      title: 'Location-Based Circles',
      description: 'Create Circles around you with specific goals. When Circles collide, your agents decide if it\'s worth connecting.',
      color: '#FF8A3D',
    },
    {
      icon: Shield,
      title: 'Privacy First',
      description: 'Your agent presents matches without exposing sensitive details. You\'re always in control of what you share.',
      color: '#34D1BF',
    },
  ];

  const currentScreen = screens[step];
  const Icon = currentScreen.icon;

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-[#5B5FEE] to-[#FF8A3D] relative overflow-hidden">
      {/* Decorative circles */}
      <div className="absolute top-20 right-10 w-40 h-40 rounded-full bg-white/10 blur-3xl" />
      <div className="absolute bottom-40 left-10 w-60 h-60 rounded-full bg-white/10 blur-3xl" />

      <div className="flex-1 flex flex-col items-center justify-center px-8 relative z-10">
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.4 }}
            className="flex flex-col items-center text-center"
          >
            <div className="w-24 h-24 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center mb-8">
              <Icon className="w-12 h-12 text-white" strokeWidth={1.5} />
            </div>
            <h1 className="text-white mb-4">{currentScreen.title}</h1>
            <p className="text-white/90 max-w-sm">{currentScreen.description}</p>
          </motion.div>
        </AnimatePresence>
      </div>

      <div className="px-8 pb-12 space-y-6">
        {/* Dots indicator */}
        <div className="flex justify-center gap-2">
          {screens.map((_, index) => (
            <div
              key={index}
              className={`h-2 rounded-full transition-all ${
                index === step ? 'w-8 bg-white' : 'w-2 bg-white/40'
              }`}
            />
          ))}
        </div>

        {/* Next/Get Started button */}
        <Button
          onClick={() => {
            if (step < screens.length - 1) {
              setStep(step + 1);
            } else {
              onComplete();
            }
          }}
          className="w-full bg-white text-[#5B5FEE] hover:bg-white/90 h-14 rounded-2xl"
          size="lg"
        >
          {step < screens.length - 1 ? (
            <>
              Next
              <ArrowRight className="ml-2 w-5 h-5" />
            </>
          ) : (
            'Get Started'
          )}
        </Button>
      </div>
    </div>
  );
}
