"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { Send, Mic } from "lucide-react";
import { api } from "../../lib/api";
import "./SupportButton.css";

const GREETING =
  "Hey! How are you doing? Let me know what help you need.";

function getAssistantVoice() {
  const voices = window.speechSynthesis.getVoices();

  const preferred = [
    "Google UK English Female",
    "Google US English",
    "Samantha",
    "Microsoft Zira Desktop",
    "Microsoft Zira",
    "Karen",
    "Daniel",
    "Victoria",
  ];

  for (const name of preferred) {
    const voice = voices.find((v) => v.name.includes(name));
    if (voice) return voice;
  }

  return voices.find((v) => v.lang.startsWith("en")) || voices[0] || null;
}

function speak(text) {
  if (!("speechSynthesis" in window)) return;

  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);

  utterance.rate = 1;
  utterance.pitch = 1.05;
  utterance.volume = 1;

  const voice = getAssistantVoice();
  if (voice) utterance.voice = voice;

  window.speechSynthesis.speak(utterance);
}

export default function SupportButton() {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);

  const inputRef = useRef(null);
  const msgsEndRef = useRef(null);
  const recognitionRef = useRef(null);

  // Refs to allow event listeners to access the latest state
  const openRef = useRef(open);
  const isListeningRef = useRef(isListening);

  useEffect(() => {
    openRef.current = open;
  }, [open]);

  useEffect(() => {
    isListeningRef.current = isListening;
  }, [isListening]);

  const toggle = useCallback(() => {
    const next = !openRef.current;
    setOpen(next);

    if (next) {
      setMessages([
        { text: "Hey! How are you doing?", from: "bot" },
        { text: "Let me know what help you need.", from: "bot" },
      ]);
      speak(GREETING);
      setTimeout(() => {
        inputRef.current?.focus();
      }, 300);
      setIsListening(true); // Automatically start listening for actual query when woken up
    } else {
      window.speechSynthesis.cancel();
      setIsListening(false);
      setMessages([]);
    }
  }, []);

  const toggleRef = useRef(toggle);
  useEffect(() => {
    toggleRef.current = toggle;
  }, [toggle]);

  useEffect(() => {
    window.speechSynthesis?.getVoices();

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;

      recognition.onresult = (event) => {
        let transcript = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript;
        }
        
        const lower = transcript.toLowerCase();

        if (!openRef.current) {
          // Listen for wake word
          if (lower.includes("hey sit") || lower.includes("hay sit") || lower.includes("hey site") || lower.includes("hey siri") || lower.includes("hey ai")) {
            recognition.stop(); // Stop to clear the transcript buffer
            toggleRef.current();
            // It will restart automatically via onend
          }
        } else {
          // If open and listening, populate the chat input
          if (isListeningRef.current) {
            setMessage(prev => prev + transcript);
          }
        }
      };

      recognition.onend = () => {
        // Keep the listener alive in the background
        try {
          recognition.start();
        } catch (e) {
          // ignore
        }
      };

      recognition.onerror = (event) => {
        console.error("Speech recognition error", event.error);
        if (event.error === 'not-allowed') {
           setIsListening(false);
        }
      };

      recognitionRef.current = recognition;
      try {
        recognition.start();
      } catch (e) {}
    }
  }, []);

  useEffect(() => {
    msgsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const close = () => {
    setOpen(false);
    setMessages([]);
    window.speechSynthesis.cancel();
    setIsListening(false);
  };

  const toggleListening = () => {
    if (!recognitionRef.current) {
      alert("Speech recognition is not supported in this browser.");
      return;
    }
    setIsListening(!isListeningRef.current);
  };

  async function askAI(userMessage) {
    try {
      const response = await api.post("/ai/chat", { message: userMessage });
      return response;
    } catch (err) {
      throw new Error("Failed to contact AI");
    }
  }

  const handleSend = async () => {
    const text = message.trim();

    if (!text || loading) return;

    if (isListening && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
    }

    setMessages((prev) => [
      ...prev,
      {
        text,
        from: "user",
      },
    ]);

    setMessage("");
    setLoading(true);

    setMessages((prev) => [
      ...prev,
      {
        text: "Thinking...",
        from: "bot",
        typing: true,
      },
    ]);

    try {
      const result = await askAI(text);

      setMessages((prev) => {
        const list = [...prev];

        list.pop();

        list.push({
          text: result.reply,
          from: "bot",
        });

        return list;
      });

      speak(result.reply);
    } catch (err) {
      setMessages((prev) => {
        const list = [...prev];

        list.pop();

        list.push({
          text: "Sorry, I couldn't reach the AI server.",
          from: "bot",
        });

        return list;
      });
    }

    setLoading(false);
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      <button
        className="support-button"
        onClick={toggle}
        aria-label="AI Support"
      >
        <img
          src="/logo.png"
          alt="AI"
          className="support-logo-img"
        />
      </button>

      {open && (
        <div
          className="support-text-overlay"
          onClick={close}
        >
          <div
            className="support-chat-popup"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="support-msgs-area">
              {messages.map((m, i) => (
                <div
                  key={i}
                  className={`support-msg support-msg-${m.from}`}
                >
                  {m.text}
                </div>
              ))}

              <div ref={msgsEndRef} />
            </div>

            <div className="support-input-row">
              <input
                ref={inputRef}
                className="support-input"
                placeholder="Ask AI Site Studio..."
                value={message}
                disabled={loading}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={handleKey}
              />

              <button
                className={`support-mic ${isListening ? "listening" : ""}`}
                onClick={toggleListening}
                disabled={loading}
                aria-label="Toggle Voice Input"
                style={{
                  background: 'none',
                  border: 'none',
                  color: isListening ? '#ef4444' : '#6b7280',
                  cursor: 'pointer',
                  padding: '4px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'color 0.2s ease',
                  animation: isListening ? 'pulse 1.5s infinite' : 'none'
                }}
              >
                <Mic size={18} />
              </button>

              <button
                className="support-send"
                onClick={handleSend}
                disabled={loading}
              >
                <Send size={16} />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}