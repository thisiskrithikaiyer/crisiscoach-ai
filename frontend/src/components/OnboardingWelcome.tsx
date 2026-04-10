"use client";

const CHIPS = [
  { label: "Lost my job recently", icon: "💼" },
  { label: "Overwhelmed at work", icon: "🔥" },
  { label: "Anxiety & stress", icon: "😰" },
  { label: "Burnout", icon: "😞" },
  { label: "Financial pressure", icon: "💸" },
  { label: "Career uncertainty", icon: "🧭" },
  { label: "Relationship difficulties", icon: "💔" },
  { label: "Just feeling lost", icon: "🌫️" },
];

export default function OnboardingWelcome({
  onChipClick,
}: {
  onChipClick: (text: string) => void;
}) {
  return (
    <div className="flex flex-col flex-1 overflow-hidden bg-white">
      {/* Hero */}
      <div className="px-8 pt-10 pb-7">
        <span className="inline-block text-xs font-semibold tracking-widest text-violet-500 uppercase mb-3">
          Your personal crisis coach
        </span>
        <h2 className="text-2xl font-bold text-gray-900 leading-snug mb-2.5">
          I&apos;m sorry you&apos;re going through this.
        </h2>
        <p className="text-sm text-gray-500 leading-relaxed max-w-lg">
          I&apos;m here to help you cut through the chaos, find clarity, and take back control — one step at a time. Let&apos;s figure this out together.
        </p>
      </div>

      <div className="mx-8 h-px bg-gray-100" />

      {/* Chips */}
      <div className="px-8 pt-6 pb-6 flex-1 overflow-y-auto">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-4">
          What&apos;s going on?
        </p>
        <div className="flex flex-wrap gap-2.5">
          {CHIPS.map(({ label, icon }) => (
            <button
              key={label}
              onClick={() => onChipClick(label)}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-full border border-gray-200 bg-white text-gray-700 text-sm font-medium hover:border-violet-600 hover:text-violet-700 hover:bg-violet-50 transition-all duration-150 shadow-sm"
            >
              <span className="text-base leading-none">{icon}</span>
              {label}
            </button>
          ))}
        </div>

        <p className="mt-7 text-xs text-gray-400">
          Or type anything in the chat — I&apos;m listening.
        </p>
      </div>
    </div>
  );
}
