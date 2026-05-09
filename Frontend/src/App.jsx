import React, { useState, useEffect, useRef } from 'react';
import {
  Book,
  Bot,
  Send,
  MapPin,
  MessageSquare,
  Loader2,
  AlertCircle,
  Mic,
  MicOff,
  Volume2
} from 'lucide-react';

import axios from 'axios';

const App = () => {

  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [response, setResponse] = useState('');
  const [sources, setSources] = useState([]);

  const [isListening, setIsListening] = useState(false);

  const recognitionRef = useRef(null);

  // ==============================
  // Speech Recognition Setup
  // ==============================

  useEffect(() => {

    const SpeechRecognition =
      window.SpeechRecognition ||
      window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      console.warn("Speech Recognition not supported.");
      return;
    }

    const recognition = new SpeechRecognition();

    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event) => {

      let transcript = '';

      for (let i = 0; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }

      setQuery(transcript);
    };

    recognition.onerror = (event) => {

      console.error("Speech Recognition Error:", event.error);

      setError(`Speech Recognition Error: ${event.error}`);

      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;

  }, []);

  // ==============================
  // Text To Speech
  // ==============================

  const speakAnswer = (text) => {

    if (!('speechSynthesis' in window)) {
      return;
    }

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);

    utterance.rate = 1;
    utterance.pitch = 1;
    utterance.volume = 1;

    const voices = window.speechSynthesis.getVoices();

    if (voices.length > 0) {
      utterance.voice = voices[0];
    }

    window.speechSynthesis.speak(utterance);
  };

  // ==============================
  // Voice Input Toggle
  // ==============================

  const toggleListening = () => {

    if (!recognitionRef.current) {

      setError("Speech Recognition not supported in this browser.");

      return;
    }

    if (isListening) {

      recognitionRef.current.stop();

      setIsListening(false);

    } else {

      setError(null);

      try {

        recognitionRef.current.start();

        setIsListening(true);

      } catch (err) {

        console.error(err);

        setError("Could not start microphone.");
      }
    }
  };

  // ==============================
  // Time Formatter
  // ==============================

  const formatTime = (seconds) => {

    if (seconds === undefined || seconds === null) {
      return "N/A";
    }

    const totalSeconds = Math.floor(seconds);

    const minutes = Math.floor(totalSeconds / 60);

    const secs = totalSeconds % 60;

    return `${minutes}:${secs < 10 ? '0' : ''}${secs}`;
  };

  // ==============================
  // Send Query
  // ==============================

  const handleSendQuery = async () => {

    if (!query.trim()) {

      setError("Please enter a question.");

      return;
    }

    setLoading(true);

    setError(null);

    setResponse('');

    setSources([]);

    try {

      const res = await axios.post(
        "http://localhost:5000/api/query",
        {
          query: query.trim()
        }
      );

      setResponse(res.data.answer);

      setSources(res.data.context_sources || []);

    } catch (err) {

      console.error(err);

      const errorMessage =
        err.response?.data?.error ||
        err.message;

      setError(errorMessage);

    } finally {

      setLoading(false);
    }
  };

  // ==============================
  // Enter Key Support
  // ==============================

  const handleKeyDown = (e) => {

    if (e.key === 'Enter' && !e.shiftKey) {

      e.preventDefault();

      handleSendQuery();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-600 to-purple-700 p-4 md:p-8">

      <div className="max-w-4xl mx-auto bg-white rounded-2xl shadow-2xl overflow-hidden">

        {/* Header */}

        <div className="bg-gradient-to-r from-blue-700 to-indigo-900 p-8 text-center text-white">

          <div className="inline-flex items-center gap-2 bg-white/20 px-4 py-2 rounded-full mb-4">
            <Book size={18} />
            <span>100 Days Python Course</span>
          </div>

          <h1 className="text-4xl font-bold flex items-center justify-center gap-3">
            <Bot size={40} />
            LectureLens AI
          </h1>

          <p className="mt-3 text-blue-100">
            Ask questions using text or voice
          </p>
        </div>

        {/* Main */}

        <div className="p-6 md:p-8">

          {/* Input */}

          <div className="relative">

            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask your course question..."
              className="w-full min-h-[120px] border-2 border-gray-200 rounded-xl p-4 pr-16 text-lg resize-none focus:outline-none focus:border-blue-500"
            />

            <button
              onClick={toggleListening}
              className={`absolute right-4 top-4 p-3 rounded-full transition-all ${
                isListening
                  ? 'bg-red-500 text-white'
                  : 'bg-gray-100 text-gray-600'
              }`}
            >
              {
                isListening
                  ? <MicOff size={22} />
                  : <Mic size={22} />
              }
            </button>
          </div>

          {/* Buttons */}

          <div className="flex gap-4 mt-4">

            <button
              onClick={handleSendQuery}
              disabled={loading}
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-semibold"
            >
              {
                loading
                  ? <Loader2 className="animate-spin" size={20} />
                  : <Send size={20} />
              }

              {
                loading
                  ? 'Thinking...'
                  : 'Get Answer'
              }
            </button>

            {
              response && (
                <button
                  onClick={() => speakAnswer(response)}
                  className="flex items-center gap-2 bg-gray-200 hover:bg-gray-300 px-6 py-3 rounded-xl font-semibold"
                >
                  <Volume2 size={20} />
                  Speak
                </button>
              )
            }
          </div>

          {/* Error */}

          {
            error && (
              <div className="mt-6 bg-red-100 text-red-700 p-4 rounded-xl flex items-center gap-3">
                <AlertCircle size={22} />
                {error}
              </div>
            )
          }

          {/* Response */}

          {
            response && (
              <div className="mt-8 space-y-6">

                <div className="bg-gray-50 border-l-4 border-blue-600 p-6 rounded-xl">

                  <div className="flex items-center gap-2 text-blue-700 font-bold mb-4">
                    <MessageSquare size={22} />
                    AI Response
                  </div>

                  <div className="text-lg leading-relaxed whitespace-pre-line">
                    {response}
                  </div>
                </div>

                {/* Sources */}

                {
                  sources.length > 0 && (
                    <div className="bg-slate-100 p-6 rounded-xl">

                      <div className="flex items-center gap-2 font-bold text-indigo-800 mb-4">
                        <MapPin size={20} />
                        Reference Sources
                      </div>

                      <div className="space-y-4">

                        {
                          sources.map((source, index) => (

                            <div
                              key={index}
                              className="bg-white p-4 rounded-xl border-l-4 border-cyan-400"
                            >

                              <div className="font-bold text-indigo-900">
                                Lecture {source.number}
                              </div>

                              <div className="text-sm text-gray-500 mb-2">
                                {source.title}
                              </div>

                              <div className="text-blue-600 font-mono">
                                {formatTime(source.start)} - {formatTime(source.end)}
                              </div>

                            </div>
                          ))
                        }

                      </div>

                    </div>
                  )
                }

              </div>
            )
          }

        </div>

      </div>

    </div>
  );
};

export default App;