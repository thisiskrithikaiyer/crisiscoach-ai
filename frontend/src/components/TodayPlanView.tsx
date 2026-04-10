"use client";

import { useState, useEffect } from "react";
import { fetchTodayPlan, generatePlan, TodayPlan } from "@/lib/api";

const PRIORITY_STYLES: Record<string, { bg: string; border: string; text: string; emoji: string }> = {
  urgent:   { bg: "bg-red-50",    border: "border-red-200",    text: "text-red-700",    emoji: "🚨" },
  standard: { bg: "bg-violet-50", border: "border-violet-200", text: "text-violet-700", emoji: "⚡" },
  recovery: { bg: "bg-blue-50",   border: "border-blue-200",   text: "text-blue-700",   emoji: "🌊" },
};

const BLOCK_META = {
  morning: { emoji: "🌅", label: "Morning" },
  midday:  { emoji: "☀️",  label: "Midday"  },
  evening: { emoji: "🌙", label: "Evening" },
};

export default function TodayPlanView() {
  const [plan, setPlan] = useState<TodayPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    fetchTodayPlan().then((p) => {
      setPlan(p);
      setLoading(false);
    });
  }, []);

  async function handleGenerate() {
    setGenerating(true);
    const p = await generatePlan();
    setPlan(p);
    setGenerating(false);
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <div className="w-8 h-8 rounded-full border-2 border-violet-200 border-t-violet-600 animate-spin mb-4" />
        <p className="text-xs text-gray-400">Loading today&apos;s plan…</p>
      </div>
    );
  }

  if (!plan) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="w-12 h-12 rounded-full bg-violet-50 flex items-center justify-center mb-4">
          <span className="text-2xl">📋</span>
        </div>
        <p className="text-sm font-semibold text-gray-800 mb-1">No plan for today yet</p>
        <p className="text-xs text-gray-400 max-w-xs leading-relaxed mb-5">
          Generate your personalized daily plan based on your goals and current progress.
        </p>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="px-5 py-2 bg-violet-700 hover:bg-violet-800 disabled:opacity-50 text-white text-sm font-semibold rounded-lg transition-colors shadow-sm"
        >
          {generating ? "Building your plan…" : "Generate today's plan"}
        </button>
      </div>
    );
  }

  const mode = plan.priority_mode?.toLowerCase() ?? "standard";
  const modeStyle = PRIORITY_STYLES[mode] ?? PRIORITY_STYLES.standard;

  return (
    <div className="space-y-4 pb-6">

      {/* Header row */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-base font-bold text-gray-900">Today&apos;s Plan</p>
          <p className="text-xs text-gray-400 mt-0.5">{plan.date}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${modeStyle.bg} ${modeStyle.border} ${modeStyle.text}`}>
            {modeStyle.emoji} {plan.priority_mode?.toUpperCase()}
          </span>
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="text-xs text-violet-600 hover:text-violet-800 font-medium disabled:opacity-40 transition-colors"
          >
            {generating ? "Rebuilding…" : "↻ Rebuild"}
          </button>
        </div>
      </div>

      {/* Coach note */}
      {plan.coach_note && (
        <div className="flex items-start gap-3 px-4 py-3 rounded-xl bg-amber-50 border border-amber-200">
          <span className="text-lg shrink-0">💬</span>
          <p className="text-sm text-amber-900 leading-relaxed font-medium">{plan.coach_note}</p>
        </div>
      )}

      {/* Quick stats */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-white border border-gray-200 rounded-xl p-3.5 text-center">
          <p className="text-2xl font-bold text-gray-900">{plan.job_apps}</p>
          <p className="text-xs text-gray-400 mt-0.5">📨 Job apps today</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-3.5 text-center">
          <p className="text-2xl font-bold text-gray-900">{plan.leetcode_problems}</p>
          <p className="text-xs text-gray-400 mt-0.5">💻 {plan.leetcode_topic || "LeetCode"}</p>
        </div>
      </div>

      {/* Schedule blocks */}
      {plan.schedule && (
        <div className="space-y-3">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest">Schedule</p>
          {(["morning", "midday", "evening"] as const).map((key) => {
            const block = plan.schedule[key];
            if (!block?.tasks?.length) return null;
            const meta = BLOCK_META[key];
            return (
              <div key={key} className="bg-white border border-gray-200 rounded-xl overflow-hidden">
                <div className="flex items-center gap-2 px-4 py-2.5 border-b border-gray-100 bg-gray-50">
                  <span className="text-base">{meta.emoji}</span>
                  <p className="text-xs font-semibold text-gray-700">{block.time || meta.label}</p>
                </div>
                <ul className="px-4 py-3 space-y-2">
                  {block.tasks.map((task, i) => (
                    <li key={i} className="flex items-start gap-2.5">
                      <span className="mt-0.5 w-4 h-4 rounded-full bg-violet-100 text-violet-700 text-xs font-bold flex items-center justify-center shrink-0 leading-none">
                        {i + 1}
                      </span>
                      <span className="text-xs text-gray-700 leading-relaxed">{task}</span>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
