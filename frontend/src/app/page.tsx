import ChatWindow from "@/components/ChatWindow";

export default function Home() {
  return (
    <main className="flex flex-col items-center justify-center min-h-screen bg-gray-50">
      <div className="w-full max-w-2xl h-[90vh] bg-white rounded-2xl shadow-lg flex flex-col overflow-hidden">
        <header className="bg-blue-600 text-white px-6 py-4">
          <h1 className="text-lg font-semibold">CrisisCoach AI</h1>
          <p className="text-xs opacity-75">
            Compassionate support, available anytime
          </p>
        </header>
        <ChatWindow />
      </div>
    </main>
  );
}
