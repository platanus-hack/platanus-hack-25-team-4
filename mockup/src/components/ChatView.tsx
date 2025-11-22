import { useState } from 'react';
import { ArrowLeft, Send, Sparkles } from 'lucide-react';
import { Button } from './ui/button';
import { ImageWithFallback } from './figma/ImageWithFallback';

interface Match {
  id: string;
  name: string;
  avatar: string;
  suggestedOpener: string;
}

interface ChatViewProps {
  match: Match;
  onBack: () => void;
}

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'other' | 'agent';
  timestamp: Date;
}

export function ChatView({ match, onBack }: ChatViewProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: match.suggestedOpener,
      sender: 'user',
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(true);

  const suggestions = [
    "What time works best for you?",
    "Have you played at these courts before?",
    "What's your skill level?",
  ];

  const handleSend = (text?: string) => {
    const messageText = text || inputValue.trim();
    if (messageText) {
      setMessages([
        ...messages,
        {
          id: Date.now().toString(),
          text: messageText,
          sender: 'user',
          timestamp: new Date(),
        },
      ]);
      setInputValue('');
      setShowSuggestions(false);
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
  };

  return (
    <div className="h-full flex flex-col bg-[#F6F7FC]">
      {/* Header */}
      <div className="bg-white px-6 pt-16 pb-4 shadow-sm">
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="w-10 h-10 rounded-full bg-[#F6F7FC] flex items-center justify-center"
          >
            <ArrowLeft className="w-5 h-5 text-[#1A1A1A]" />
          </button>
          <div className="flex items-center gap-3 flex-1">
            <div className="relative">
              <ImageWithFallback
                src={match.avatar}
                alt={match.name}
                className="w-12 h-12 rounded-full object-cover"
              />
              <div className="absolute bottom-0 right-0 w-3 h-3 bg-[#34D1BF] rounded-full border-2 border-white" />
            </div>
            <div>
              <h3 className="text-[#1A1A1A]">{match.name}</h3>
              <span className="text-[#525866]">Online</span>
            </div>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 px-6 py-4 overflow-auto">
        <div className="space-y-4">
          {/* Info message */}
          <div className="flex justify-center">
            <div className="bg-[#5B5FEE]/10 rounded-full px-4 py-2">
              <span className="text-[#5B5FEE]">Chat started</span>
            </div>
          </div>

          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-[75%] ${message.sender === 'user' ? 'order-2' : ''}`}>
                <div
                  className={`rounded-3xl px-5 py-3 ${
                    message.sender === 'user'
                      ? 'bg-[#5B5FEE] text-white'
                      : message.sender === 'agent'
                      ? 'bg-[#FFD66B]/20 text-[#1A1A1A]'
                      : 'bg-white text-[#1A1A1A]'
                  }`}
                >
                  <p className="leading-relaxed">{message.text}</p>
                </div>
                <span className={`text-[#525866] mt-1 block ${
                  message.sender === 'user' ? 'text-right' : 'text-left'
                }`}>
                  {formatTime(message.timestamp)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* AI Suggestions */}
      {showSuggestions && (
        <div className="px-6 py-3">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-4 h-4 text-[#5B5FEE]" />
            <span className="text-[#5B5FEE]">Suggested replies</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => handleSend(suggestion)}
                className="px-4 py-2 bg-white text-[#1A1A1A] rounded-full border border-[#5B5FEE]/20 hover:border-[#5B5FEE] hover:bg-[#5B5FEE]/5 transition-colors"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="px-6 pb-8 pt-3">
        <div className="bg-white rounded-3xl shadow-sm flex items-center gap-3 px-4 py-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Type a message..."
            className="flex-1 bg-transparent border-0 outline-none text-[#1A1A1A] placeholder:text-[#525866] py-2"
          />
          <Button
            onClick={() => handleSend()}
            disabled={!inputValue.trim()}
            className="bg-[#5B5FEE] hover:bg-[#5B5FEE]/90 disabled:bg-[#525866]/20 w-10 h-10 rounded-full p-0"
            size="sm"
          >
            <Send className="w-5 h-5" />
          </Button>
        </div>
      </div>
    </div>
  );
}
