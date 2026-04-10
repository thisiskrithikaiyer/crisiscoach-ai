"use client";

import { useState, useEffect } from "react";
import ChatWindow from "@/components/ChatWindow";
import CrisisTracker from "@/components/CrisisTracker";
import OnboardingWelcome from "@/components/OnboardingWelcome";
import AuthScreen from "@/components/AuthScreen";
import { getToken, clearToken } from "@/lib/api";

export default function Home() {
  const [hydrated, setHydrated] = useState(false);
  const [authed, setAuthed] = useState(false);
  const [isNewUser, setIsNewUser] = useState(true);
  const [isLaidOff, setIsLaidOff] = useState(false);
  const [pendingMessage, setPendingMessage] = useState<string | undefined>();

  useEffect(() => {
    if (getToken()) setAuthed(true);
    if (localStorage.getItem("cc_laid_off") === "1") {
      setIsLaidOff(true);
      setIsNewUser(false);
    }
    setHydrated(true);
  }, []);

  function markLaidOff() {
    localStorage.setItem("cc_laid_off", "1");
    setIsLaidOff(true);
  }

  function clearLaidOff() {
    localStorage.removeItem("cc_laid_off");
    setIsLaidOff(false);
  }

  function handleChipClick(text: string) {
    setIsNewUser(false);
    setPendingMessage(text);
    if (/job|laid.?off/i.test(text)) markLaidOff();
  }

  function handleSignOut() {
    clearToken();
    setAuthed(false);
    setIsNewUser(true);
    clearLaidOff();
    setPendingMessage(undefined);
  }

  if (!hydrated) return null;
  if (!authed) {
    return <AuthScreen onAuth={() => setAuthed(true)} />;
  }

  return (
    <main className="flex h-screen bg-white overflow-hidden">
      {/* Left panel */}
      <div className="flex flex-col flex-1 border-r border-gray-200 overflow-hidden">
        {/* Header */}
        <header className="flex items-center gap-3 px-6 py-4 border-b border-violet-200 shrink-0" style={{background: "linear-gradient(135deg, #4c1d95 0%, #6d28d9 50%, #a855f7 100%)"}}>
          <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center shrink-0">
            <span className="text-white text-xs font-bold tracking-tight">CC</span>
          </div>
          <div className="flex-1">
            <h1 className="text-sm font-semibold text-white">CrisisCoach AI</h1>
            <p className="text-xs text-purple-200">We&apos;re turning this into your success story.</p>
          </div>
          <button
            onClick={handleSignOut}
            className="text-xs text-purple-200 hover:text-white transition-colors"
          >
            Sign out
          </button>
        </header>

        {isNewUser ? (
          <OnboardingWelcome onChipClick={handleChipClick} />
        ) : (
          <CrisisTracker isLaidOff={isLaidOff} onOfferReceived={clearLaidOff} />
        )}
      </div>

      {/* Right: Chat panel */}
      <div className="flex flex-col w-80 bg-white border-l border-gray-200 overflow-hidden shrink-0">
        <header className="px-4 py-4 border-b border-violet-200 shrink-0" style={{background: "linear-gradient(135deg, #4c1d95 0%, #6d28d9 50%, #a855f7 100%)"}}>
          <h2 className="text-sm font-semibold text-white">Talk to me</h2>
          <p className="text-xs text-purple-200">Talk to your coach</p>
        </header>
        <ChatWindow
          pendingMessage={pendingMessage}
          onFirstMessage={() => setIsNewUser(false)}
          onPendingConsumed={() => setPendingMessage(undefined)}
          onHistoryLoaded={() => setIsNewUser(false)}
          onAuthError={handleSignOut}
        />
      </div>
    </main>
  );
}
