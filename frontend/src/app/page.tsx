import ChatWindow from "@/components/ChatWindow";
import CrisisTracker from "@/components/CrisisTracker";

export default function Home() {
  return (
    <main className="flex h-screen bg-violet-50 overflow-hidden">
      {/* Left: Tracker panel */}
      <div className="flex flex-col flex-1 bg-white border-r border-violet-100 overflow-hidden">
        <header className="flex items-center gap-3 px-6 py-4 border-b border-violet-100 shrink-0">
          <div className="w-8 h-8 rounded-lg bg-violet-600 flex items-center justify-center shrink-0">
            <span className="text-white text-xs font-bold">CC</span>
          </div>
          <div>
            <h1 className="text-sm font-semibold text-gray-900">CrisisCoach AI</h1>
            <p className="text-xs text-violet-400">Compassionate support, available anytime</p>
          </div>
        </header>
        <CrisisTracker />
      </div>

      {/* Right: Chat panel */}
      <div className="flex flex-col w-80 bg-white overflow-hidden shrink-0">
        <header className="px-4 py-4 border-b border-violet-100 shrink-0">
          <h2 className="text-sm font-semibold text-violet-700">Chat</h2>
          <p className="text-xs text-violet-300">Talk to your coach</p>
        </header>
        <ChatWindow />
      </div>
    </main>
  );
}
