"use client";

import { useState, useRef, useEffect } from "react";
import { MessageSquare, X, Send, Sparkles } from "lucide-react";
import api from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";

const WELCOME_MESSAGE = {
  id: "welcome",
  text: "Hi! I'm your JobSync AI Assistant. Ask me anything about job requirements, career tracks, or preparation guides!",
  isBot: true
};

export default function ChatWidget() {
  const { isAuthenticated, user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Reset chat history whenever the logged-in user changes (logout / switch account)
  useEffect(() => {
    setMessages([WELCOME_MESSAGE]);
    setInput("");
    setIsOpen(false);
  }, [user?.id]);

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isOpen]);

  // Don't show the widget unless logged in
  if (!isAuthenticated) return null;


  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = {
      id: String(Date.now()),
      text: input,
      isBot: false
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const { data } = await api.post("/api/ai/knowledge/query", {
        query: userMessage.text,
        limit: 3
      });

      const botMessage = {
        id: String(Date.now() + 1),
        text: data.answer || "I parsed the database but couldn't find a detailed match. Try asking about skills, job roles, or interview prep guides!",
        isBot: true,
        sources: data.sources || []
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: String(Date.now() + 1),
          text: "Sorry, I ran into an error connecting to the knowledge base. Please try again later.",
          isBot: true
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 font-sans">
      {/* Floating Toggle Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white p-4 rounded-full shadow-lg shadow-blue-500/20 hover:scale-110 active:scale-95 transition-all duration-300 flex items-center justify-center relative group"
        >
          <MessageSquare size={24} />
          <span className="absolute right-14 bg-gray-900 text-white text-xs font-semibold px-3 py-1.5 rounded-lg whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none shadow-md">
            Ask JobSync AI
          </span>
          <span className="absolute top-0 right-0 h-3 w-3 rounded-full bg-green-400 border-2 border-white animate-pulse"></span>
        </button>
      )}

      {/* Expanded Chat Window */}
      {isOpen && (
        <div className="bg-white/95 backdrop-blur-md w-[380px] h-[500px] rounded-2xl shadow-2xl border border-gray-100 flex flex-col overflow-hidden animate-in slide-in-from-bottom-5 fade-in duration-300">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-5 py-4 flex items-center justify-between shadow-sm">
            <div className="flex items-center gap-2.5">
              <div className="bg-white/10 p-1.5 rounded-lg">
                <Sparkles size={18} className="text-blue-100" />
              </div>
              <div>
                <h3 className="font-bold text-sm tracking-wide">JobSync AI Support</h3>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-green-400 animate-ping"></span>
                  <span className="text-[10px] text-blue-100 font-medium">Active & connected</span>
                </div>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="text-white/80 hover:text-white hover:bg-white/10 p-1 rounded-lg transition-all"
            >
              <X size={18} />
            </button>
          </div>

          {/* Messages Stream */}
          <div className="flex-1 overflow-y-auto p-5 space-y-4 bg-gray-50/50">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex flex-col max-w-[80%] ${
                  msg.isBot ? "self-start items-start" : "self-end items-end ml-auto"
                }`}
              >
                <div
                  className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                    msg.isBot
                      ? "bg-white text-gray-800 rounded-tl-none border border-gray-100 shadow-sm"
                      : "bg-blue-600 text-white rounded-tr-none shadow-md shadow-blue-500/10"
                  }`}
                >
                  {msg.text}

                  {/* Document Source Reference tags */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-2.5 pt-2 border-t border-gray-100 text-[10px] text-gray-400">
                      <span className="font-bold text-gray-500 uppercase tracking-wider block mb-1">Sources:</span>
                      <div className="flex flex-wrap gap-1">
                        {msg.sources.map((src, i) => (
                          <span key={i} className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded border border-gray-200">
                            {src.split('/').pop() || src}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
            
            {loading && (
              <div className="flex items-center gap-1 bg-white border border-gray-100 shadow-sm px-4 py-3 rounded-2xl rounded-tl-none max-w-[60%]">
                <span className="h-1.5 w-1.5 rounded-full bg-gray-400 animate-bounce [animation-delay:-0.3s]"></span>
                <span className="h-1.5 w-1.5 rounded-full bg-gray-400 animate-bounce [animation-delay:-0.15s]"></span>
                <span className="h-1.5 w-1.5 rounded-full bg-gray-400 animate-bounce"></span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Form */}
          <form onSubmit={handleSend} className="p-4 border-t border-gray-100 bg-white flex gap-2 items-center">
            <input
              type="text"
              placeholder="Ask a question..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
              className="flex-1 bg-gray-50 border border-gray-200 focus:border-blue-500 rounded-xl px-4 py-3 text-sm focus:outline-none transition-all disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={!input.trim() || loading}
              className="bg-blue-600 hover:bg-blue-700 text-white p-3 rounded-xl shadow-md shadow-blue-500/15 disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105 active:scale-95 transition-all duration-300"
            >
              <Send size={18} />
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
