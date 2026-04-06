import { Message } from "@/lib/api";

export default function ChatBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-3`}>
      <div
        className={`max-w-[85%] rounded-2xl px-3 py-2 text-xs leading-relaxed whitespace-pre-wrap ${
          isUser
            ? "bg-violet-600 text-white rounded-br-sm"
            : "bg-violet-50 text-violet-900 rounded-bl-sm"
        }`}
      >
        {message.content}
      </div>
    </div>
  );
}
