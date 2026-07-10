import { useState, useCallback, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';
import './SupportButton.css';

const GREETING = "Hey! How are you doing? Let me know what help you need.";

/** Pick the most assistant-like voice (Google Assistant / Siri style) */
function getAssistantVoice() {
  const voices = window.speechSynthesis.getVoices();
  // Best matches for Siri / Google Assistant / Alexa sound
  const preferred = [
    'Google UK English Female',       // closest to Google Assistant
    'Google US English',              // Google fallback
    'Samantha',                       // Siri voice (macOS/iOS)
    'Microsoft Zira Desktop',         // Windows clean female
    'Microsoft Zira',                 // Windows fallback
    'Karen',                          // Australian Siri-like
    'Daniel',                         // UK Siri male (fallback)
    'Tessa',                          // South African English
    'Victoria',                       // macOS fallback
  ];
  for (const name of preferred) {
    const v = voices.find(v => v.name.includes(name));
    if (v) return v;
  }
  return voices.find(v => v.lang.startsWith('en')) || voices[0] || null;
}

function speak(text) {
  if (!('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.rate = 1.0;     // natural pace like Siri/Assistant
  u.pitch = 1.05;   // slightly bright, assistant-like
  u.volume = 1.0;   // clear and confident
  const voice = getAssistantVoice();
  if (voice) u.voice = voice;
  window.speechSynthesis.speak(u);
}

export default function SupportButton() {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([]);
  const inputRef = useRef(null);
  const msgsEndRef = useRef(null);

  // load voices
  useEffect(() => {
    window.speechSynthesis?.getVoices();
    const handler = () => {};
    window.speechSynthesis?.addEventListener?.('voiceschanged', handler);
    return () => window.speechSynthesis?.removeEventListener?.('voiceschanged', handler);
  }, []);

  // auto-scroll
  useEffect(() => {
    msgsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const toggle = useCallback(() => {
    const nextOpen = !open;
    setOpen(nextOpen);
    if (nextOpen) {
      setMessages([
        { text: 'Hey! How are you doing?', from: 'bot' },
        { text: 'Let me know what help you need.', from: 'bot' },
      ]);
      speak(GREETING);
      setTimeout(() => inputRef.current?.focus(), 350);
    } else {
      window.speechSynthesis?.cancel();
      setMessages([]);
    }
  }, [open]);

  const close = () => {
    setOpen(false);
    window.speechSynthesis?.cancel();
    setMessages([]);
  };

  const handleSend = () => {
    const text = message.trim();
    if (!text) return;
    setMessages(prev => [...prev, { text, from: 'user' }]);
    setMessage('');
    setTimeout(() => {
      const reply = "Thanks for your message! We'll get back to you shortly.";
      setMessages(prev => [...prev, { text: reply, from: 'bot' }]);
      speak(reply);
    }, 600);
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      <button className="support-button" onClick={toggle} aria-label="AI Support">
        <img src="/logo.png" alt="AI" className="support-logo-img" />
      </button>

      {open && (
        <div className="support-text-overlay" onClick={close}>
          <div className="support-chat-popup" onClick={e => e.stopPropagation()}>
            <div className="support-msgs-area">
              {messages.map((m, i) => (
                <div
                  key={i}
                  className={`support-msg support-msg-${m.from}`}
                  style={{ animationDelay: `${i * 0.08}s` }}
                >
                  {m.text}
                </div>
              ))}
              <div ref={msgsEndRef} />
            </div>
            <div className="support-input-row">
              <input
                ref={inputRef}
                type="text"
                className="support-input"
                value={message}
                onChange={e => setMessage(e.target.value)}
                onKeyDown={handleKey}
                placeholder="Type your message…"
              />
              <button className="support-send" onClick={handleSend} aria-label="Send">
                <Send size={16} />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
