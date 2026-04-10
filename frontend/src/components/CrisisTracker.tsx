"use client";

import { useState, useEffect } from "react";
import { saveResume, saveLinkedIn, fetchGoalPlan, GoalPlan } from "@/lib/api";
import TodayPlanView from "./TodayPlanView";

type ProfileStatus = "idle" | "saving" | "saved" | "error";

function ProfileCard({
  title, description, placeholder, value, onChange, onSave, status, saveLabel,
}: {
  title: string;
  description: string;
  placeholder: string;
  value: string;
  onChange: (v: string) => void;
  onSave: () => void;
  status: ProfileStatus;
  saveLabel: string;
}) {
  const statusEl = status === "saving" ? (
    <span className="text-xs text-gray-400">Saving…</span>
  ) : status === "saved" ? (
    <span className="text-xs text-emerald-600 font-medium">Saved ✓</span>
  ) : status === "error" ? (
    <span className="text-xs text-red-500">Error — try again</span>
  ) : null;

  return (
    <div className="flex-1 rounded-xl border border-gray-200 bg-white overflow-hidden flex flex-col">
      <div className="flex items-center justify-between px-3.5 py-2.5 border-b border-gray-100">
        <div>
          <p className="text-xs font-semibold text-gray-900">{title}</p>
          <p className="text-xs text-gray-400 mt-0.5">{description}</p>
        </div>
        {statusEl}
      </div>
      <textarea
        className="flex-1 w-full px-3.5 py-2.5 text-xs text-gray-700 placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-inset"
        rows={5}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
      <div className="flex justify-end px-3.5 py-2 border-t border-gray-100 bg-gray-50">
        <button
          onClick={onSave}
          disabled={!value.trim() || status === "saving"}
          className="px-3.5 py-1.5 bg-violet-700 hover:bg-violet-800 disabled:opacity-40 text-white text-xs font-semibold rounded-lg transition-colors"
        >
          {saveLabel}
        </button>
      </div>
    </div>
  );
}

type Status = "completed" | "in-progress" | "needs-follow-up";

export interface TrackerEntry {
  id: string;
  date: string;
  time: string;
  topic: string;
  technique: string;
  status: Status;
  notes: string;
}


const STATUS_BADGE: Record<Status, { pill: string; dot: string; label: string }> = {
  completed: {
    pill: "bg-emerald-50 text-emerald-700",
    dot: "bg-emerald-500",
    label: "Done",
  },
  "in-progress": {
    pill: "bg-amber-50 text-amber-700",
    dot: "bg-amber-500",
    label: "In progress",
  },
  "needs-follow-up": {
    pill: "bg-rose-50 text-rose-700",
    dot: "bg-rose-500",
    label: "Follow up",
  },
};

type Tab = "today" | "plan" | "log" | "progress";

export default function CrisisTracker({
  extraEntries = [],
  isLaidOff = false,
  onOfferReceived,
}: {
  extraEntries?: TrackerEntry[];
  isLaidOff?: boolean;
  onOfferReceived?: () => void;
}) {
  const [tab, setTab] = useState<Tab>("today");
  const [resume, setResume] = useState("");
  const [resumeStatus, setResumeStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [linkedin, setLinkedin] = useState("");
  const [linkedinStatus, setLinkedinStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");

  async function handleSaveResume() {
    if (!resume.trim()) return;
    setResumeStatus("saving");
    try {
      await saveResume(resume);
      setResumeStatus("saved");
      setTimeout(() => setResumeStatus("idle"), 2500);
    } catch {
      setResumeStatus("error");
      setTimeout(() => setResumeStatus("idle"), 3000);
    }
  }

  async function handleSaveLinkedIn() {
    if (!linkedin.trim()) return;
    setLinkedinStatus("saving");
    try {
      await saveLinkedIn(linkedin);
      setLinkedinStatus("saved");
      setTimeout(() => setLinkedinStatus("idle"), 2500);
    } catch {
      setLinkedinStatus("error");
      setTimeout(() => setLinkedinStatus("idle"), 3000);
    }
  }
  const [entries, setEntries] = useState<TrackerEntry[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<Omit<TrackerEntry, "id">>({
    date: "",
    time: "",
    topic: "",
    technique: "",
    status: "completed",
    notes: "",
  });

  const [plan, setPlan] = useState<GoalPlan | null>(null);
  const [planLoading, setPlanLoading] = useState(false);

  useEffect(() => {
    if (tab === "plan") {
      setPlanLoading(true);
      fetchGoalPlan().then((p) => {
        setPlan(p);
        setPlanLoading(false);
      });
    }
  }, [tab]);

  const allEntries = [...extraEntries, ...entries];

  function addEntry() {
    if (!form.topic.trim()) return;
    setEntries((prev) => [
      { ...form, id: Date.now().toString() },
      ...prev,
    ]);
    setForm({ date: "", time: "", topic: "", technique: "", status: "completed", notes: "" });
    setShowForm(false);
  }

  // Progress tab stats
  const done = allEntries.filter((e) => e.status === "completed").length;
  const followUp = allEntries.filter((e) => e.status === "needs-follow-up").length;
  const techniques = Array.from(new Set(allEntries.map((e) => e.technique).filter(Boolean)));

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      {/* Profile sections */}
      <div className="mx-6 mt-5 mb-1 flex gap-3">
          {/* Resume */}
          <ProfileCard
            title="Resume"
            description="Paste it here — I'll use it to tailor advice for you."
            placeholder="Paste your resume here…"
            value={resume}
            onChange={(v) => { setResume(v); setResumeStatus("idle"); }}
            onSave={handleSaveResume}
            status={resumeStatus}
            saveLabel="Save resume"
          />
          {/* LinkedIn */}
          <ProfileCard
            title="LinkedIn"
            description="Paste your LinkedIn summary or About section."
            placeholder="Paste your LinkedIn profile here…"
            value={linkedin}
            onChange={(v) => { setLinkedin(v); setLinkedinStatus("idle"); }}
            onSave={handleSaveLinkedIn}
            status={linkedinStatus}
            saveLabel="Save LinkedIn"
          />
        </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 px-6 pt-5 border-b border-gray-200">
        {(["today", "plan", "log", "progress"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium rounded-t-md transition-colors -mb-px ${
              tab === t
                ? "bg-white border border-b-white border-gray-200 text-violet-700 font-semibold"
                : "text-gray-400 hover:text-violet-500"
            }`}
          >
            {t === "today" ? "Today" : t === "plan" ? "My Plan" : t === "log" ? "What I've done" : "Progress"}
          </button>
        ))}

        <div className="ml-auto mb-1 flex items-center gap-2">
          {isLaidOff && onOfferReceived && (
            <button
              onClick={onOfferReceived}
              className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 transition-colors"
            >
              🎉 Got an offer!
            </button>
          )}
          {tab === "log" && (
            <button
              onClick={() => setShowForm((v) => !v)}
              className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-lg bg-violet-600 text-white hover:bg-violet-700 transition-colors"
            >
              <span className="text-base leading-none">+</span> Add entry
            </button>
          )}
        </div>
      </div>

      {/* Table area */}
      <div className="flex-1 overflow-auto px-6 py-4">
        {tab === "today" && <TodayPlanView />}

        {tab === "log" && (
          <>
            {showForm && (
              <div className="mb-4 p-4 bg-violet-50 border border-violet-200 rounded-xl grid grid-cols-6 gap-2 text-sm">
                <input
                  className="col-span-1 border border-violet-200 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-violet-400 bg-white"
                  placeholder="Date"
                  value={form.date}
                  onChange={(e) => setForm({ ...form, date: e.target.value })}
                />
                <input
                  className="col-span-1 border border-violet-200 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-violet-400 bg-white"
                  placeholder="Time"
                  value={form.time}
                  onChange={(e) => setForm({ ...form, time: e.target.value })}
                />
                <input
                  className="col-span-1 border border-violet-200 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-violet-400 bg-white"
                  placeholder="Topic"
                  value={form.topic}
                  onChange={(e) => setForm({ ...form, topic: e.target.value })}
                />
                <input
                  className="col-span-1 border border-violet-200 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-violet-400 bg-white"
                  placeholder="Technique"
                  value={form.technique}
                  onChange={(e) => setForm({ ...form, technique: e.target.value })}
                />
                <select
                  className="col-span-1 border border-violet-200 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-violet-400 bg-white"
                  value={form.status}
                  onChange={(e) =>
                    setForm({ ...form, status: e.target.value as Status })
                  }
                >
                  <option value="completed">Done</option>
                  <option value="in-progress">In progress</option>
                  <option value="needs-follow-up">Follow up</option>
                </select>
                <div className="col-span-1 flex gap-1">
                  <input
                    className="flex-1 border border-violet-200 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-violet-400 bg-white"
                    placeholder="Notes"
                    value={form.notes}
                    onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  />
                  <button
                    onClick={addEntry}
                    className="px-3 py-1.5 bg-violet-600 text-white rounded-lg text-sm hover:bg-violet-700 transition-colors"
                  >
                    Save
                  </button>
                </div>
              </div>
            )}

            {allEntries.length === 0 && !showForm ? (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mb-4">
                  <span className="text-2xl">📋</span>
                </div>
                <p className="text-sm font-medium text-gray-700 mb-1">Nothing logged yet</p>
                <p className="text-xs text-gray-400 max-w-xs leading-relaxed">
                  As you work through things with your coach, your sessions will appear here. You can also add entries manually.
                </p>
              </div>
            ) : (
            <table className="w-full text-sm border-separate border-spacing-y-0.5">
              <thead>
                <tr>
                  {["Date", "Time", "Topic", "Technique", "Status", "Notes"].map(
                    (h, i) => (
                      <th
                        key={h}
                        className={`text-left px-3 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider bg-gray-50 ${
                          i === 0 ? "rounded-l-lg" : i === 5 ? "rounded-r-lg" : ""
                        }`}
                      >
                        {h}
                      </th>
                    )
                  )}
                </tr>
              </thead>
              <tbody>
                {allEntries.map((e) => {
                  const badge = STATUS_BADGE[e.status];
                  return (
                    <tr
                      key={e.id}
                      className="group hover:bg-violet-50/60 transition-colors"
                    >
                      <td className="px-3 py-2.5 text-gray-600 whitespace-nowrap text-xs border-b border-violet-50">
                        {e.date}
                      </td>
                      <td className="px-3 py-2.5 text-gray-400 whitespace-nowrap text-xs border-b border-violet-50">
                        {e.time}
                      </td>
                      <td className="px-3 py-2.5 text-gray-800 font-medium border-b border-violet-50">
                        {e.topic}
                      </td>
                      <td className="px-3 py-2.5 text-gray-600 border-b border-violet-50">
                        {e.technique}
                      </td>
                      <td className="px-3 py-2.5 border-b border-violet-50">
                        <span
                          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${badge.pill}`}
                        >
                          <span className={`w-1.5 h-1.5 rounded-full ${badge.dot}`} />
                          {badge.label}
                        </span>
                      </td>
                      <td className="px-3 py-2.5 text-gray-400 text-xs border-b border-violet-50">
                        {e.notes}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            )}
          </>
        )}

        {tab === "plan" && (
          <div className="py-2">
            {planLoading ? (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="w-8 h-8 rounded-full border-2 border-violet-200 border-t-violet-600 animate-spin mb-4" />
                <p className="text-xs text-gray-400">Loading your plan…</p>
              </div>
            ) : !plan ? (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="w-12 h-12 rounded-full bg-violet-50 flex items-center justify-center mb-4">
                  <span className="text-2xl">🗺️</span>
                </div>
                <p className="text-sm font-semibold text-gray-800 mb-1">Your plan is being built</p>
                <p className="text-xs text-gray-400 max-w-xs leading-relaxed">
                  As we talk, I&apos;ll put together a complete, personalized action plan for you right here.
                </p>
              </div>
            ) : (() => {
              const s = plan.goal_stratergy;
              const dp = s.current_daily_plan;
              return (
                <div className="space-y-4 pb-4">

                  {/* Header: mode + dates */}
                  <div className="flex flex-wrap items-center gap-2">
                    {s.mode && (
                      <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold tracking-wide border ${
                        s.mode === "URGENT"
                          ? "bg-red-50 border-red-200 text-red-600"
                          : "bg-amber-50 border-amber-200 text-amber-700"
                      }`}>
                        {s.mode === "URGENT" ? "🚨" : "⚡"} {s.mode}
                      </span>
                    )}
                    {plan.goal_committed_at && (
                      <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-violet-50 border border-violet-200 text-xs font-medium text-violet-700">
                        🎯 Committed {new Date(plan.goal_committed_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                      </span>
                    )}
                    {plan.next_revision_date && (
                      <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-amber-50 border border-amber-200 text-xs font-medium text-amber-700">
                        🔄 Check-in {new Date(plan.next_revision_date).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                      </span>
                    )}
                  </div>

                  {/* Scores + role targets */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="rounded-xl border border-gray-200 bg-white p-4">
                      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Profile scores</p>
                      <div className="space-y-2.5">
                        {[
                          { label: "📄 Resume", score: s.resume_score },
                          { label: "💼 LinkedIn", score: s.linkedin_score },
                        ].map(({ label, score }) => (
                          <div key={label}>
                            <div className="flex justify-between text-xs mb-1">
                              <span className="text-gray-600">{label}</span>
                              <span className="font-semibold text-gray-800">{score}/10</span>
                            </div>
                            <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                              <div
                                className="h-full rounded-full bg-violet-500 transition-all"
                                style={{ width: `${score * 10}%` }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="rounded-xl border border-gray-200 bg-white p-4">
                      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Role targets</p>
                      <div className="space-y-2">
                        {[
                          { emoji: "🚀", label: "Stretch", value: s.role_targets.stretch },
                          { emoji: "✅", label: "Realistic", value: s.role_targets.realistic },
                          { emoji: "🛡️", label: "Safety", value: s.role_targets.safety },
                        ].map(({ emoji, label, value }) => (
                          <div key={label}>
                            <p className="text-xs text-gray-400">{emoji} {label}</p>
                            <p className="text-xs font-medium text-gray-800 leading-tight">{value}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Daily targets */}
                  <div className="rounded-xl border border-gray-200 bg-white p-4">
                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Daily targets</p>
                    <div className="grid grid-cols-4 gap-2">
                      {[
                        { emoji: "📨", label: "Apps", value: s.daily_targets.applications },
                        { emoji: "🤝", label: "Network", value: s.daily_targets.networking_messages },
                        { emoji: "🔗", label: "Connects", value: s.daily_targets.linkedin_connects },
                        { emoji: "💻", label: "LeetCode", value: s.daily_targets.leetcode_problems },
                      ].map(({ emoji, label, value }) => (
                        <div key={label} className="text-center bg-gray-50 rounded-lg py-2.5 px-1">
                          <p className="text-base mb-0.5">{emoji}</p>
                          <p className="text-lg font-bold text-gray-900">{value}</p>
                          <p className="text-xs text-gray-400">{label}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Today's plan */}
                  {dp && (
                    <div className="rounded-xl border border-violet-200 bg-white overflow-hidden">
                      <div className="flex items-center justify-between px-4 py-3 border-b border-violet-100 bg-violet-50/50">
                        <div className="flex items-center gap-2">
                          <span className="text-base">📋</span>
                          <p className="text-sm font-semibold text-gray-900">Today&apos;s Plan</p>
                        </div>
                        <span className="text-xs text-violet-500 font-medium">{dp.date}</span>
                      </div>

                      {/* Coach note */}
                      {dp.coach_note && (
                        <div className="mx-4 mt-3 px-3 py-2.5 rounded-lg bg-amber-50 border border-amber-200">
                          <p className="text-xs text-amber-800 font-medium">💬 {dp.coach_note}</p>
                        </div>
                      )}

                      <div className="px-4 py-3 space-y-2.5">
                        {[
                          { emoji: "📨", label: "Job applications", value: `${dp.job_apps} apps` },
                          { emoji: "🤝", label: "Networking messages", value: `${dp.networking} messages` },
                          { emoji: "🏗️", label: "System design", value: `${dp.system_design} session` },
                        ].map(({ emoji, label, value }) => (
                          <div key={label} className="flex items-center justify-between">
                            <span className="text-xs text-gray-600">{emoji} {label}</span>
                            <span className="text-xs font-semibold text-gray-900">{value}</span>
                          </div>
                        ))}

                        {/* LeetCode */}
                        <div className="pt-1 border-t border-gray-100">
                          <div className="flex items-center justify-between mb-1.5">
                            <span className="text-xs text-gray-600">💻 LeetCode — {dp.leetcode_topic}</span>
                            <span className="text-xs font-semibold text-gray-900">{dp.leetcode_problems} problems</span>
                          </div>
                          {dp.leetcode_suggested?.length > 0 && (
                            <div className="flex flex-wrap gap-1.5">
                              {dp.leetcode_suggested.map((p) => (
                                <span key={p} className="px-2 py-0.5 rounded-md bg-violet-50 border border-violet-200 text-xs text-violet-700 font-medium">
                                  {p}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>

                        {/* Behavioral */}
                        {dp.behavioral_focus && (
                          <div className="flex items-start gap-2 pt-1 border-t border-gray-100">
                            <span className="text-xs shrink-0">🎤</span>
                            <p className="text-xs text-gray-700"><span className="font-semibold">Behavioral: </span>{dp.behavioral_focus}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Weekly milestones */}
                  {s.weekly_milestones?.length > 0 && (
                    <div className="rounded-xl border border-gray-200 bg-white overflow-hidden">
                      <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-100 bg-gray-50">
                        <span className="text-base">🗓️</span>
                        <p className="text-sm font-semibold text-gray-900">Weekly milestones</p>
                      </div>
                      <div className="divide-y divide-gray-100">
                        {s.weekly_milestones.map(({ week, goal }) => (
                          <div key={week} className="flex items-start gap-3 px-4 py-3">
                            <span className="shrink-0 mt-0.5 text-xs font-bold text-violet-600 bg-violet-50 border border-violet-200 px-2 py-0.5 rounded-md whitespace-nowrap">
                              Wk {week}
                            </span>
                            <p className="text-xs text-gray-700 leading-relaxed">{goal}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Technical focus */}
                  {s.technical_focus && (
                    <div className="flex items-start gap-3 px-4 py-3 rounded-xl border border-gray-200 bg-white">
                      <span className="text-base shrink-0">🧠</span>
                      <div>
                        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-0.5">Technical focus</p>
                        <p className="text-xs text-gray-700 leading-relaxed">{s.technical_focus}</p>
                      </div>
                    </div>
                  )}

                </div>
              );
            })()}
          </div>
        )}

        {tab === "progress" && (
          <div className="space-y-6">
            {allEntries.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mb-4">
                  <span className="text-2xl">📈</span>
                </div>
                <p className="text-sm font-medium text-gray-700 mb-1">No progress to show yet</p>
                <p className="text-xs text-gray-400 max-w-xs leading-relaxed">
                  Your progress and patterns will show up here once you start logging sessions.
                </p>
              </div>
            ) : (
            <>
            {/* Stat cards */}
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-violet-50 rounded-xl p-4 border border-violet-100">
                <div className="text-2xl font-bold text-violet-700">{done}</div>
                <div className="text-xs text-violet-400 mt-1">Sessions completed</div>
              </div>
              <div className="bg-emerald-50 rounded-xl p-4 border border-emerald-100">
                <div className="text-2xl font-bold text-emerald-600">
                  {techniques.length}
                </div>
                <div className="text-xs text-emerald-400 mt-1">Techniques tried</div>
              </div>
              <div className="bg-rose-50 rounded-xl p-4 border border-rose-100">
                <div className="text-2xl font-bold text-rose-600">{followUp}</div>
                <div className="text-xs text-rose-400 mt-1">Need follow-up</div>
              </div>
            </div>

            {/* Technique breakdown */}
            <div>
              <p className="text-xs font-semibold text-violet-500 uppercase tracking-wider mb-2">
                Technique breakdown
              </p>
              <table className="w-full text-sm border-separate border-spacing-y-0.5">
                <thead>
                  <tr>
                    {["Technique", "Times used", "Last used"].map((h, i) => (
                      <th
                        key={h}
                        className={`text-left px-3 py-2 text-xs font-semibold text-violet-500 uppercase tracking-wider bg-violet-50 ${
                          i === 0 ? "rounded-l-lg" : i === 2 ? "rounded-r-lg" : ""
                        }`}
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {techniques.map((technique) => {
                    const uses = allEntries.filter((e) => e.technique === technique);
                    return (
                      <tr
                        key={technique}
                        className="hover:bg-violet-50/60 transition-colors"
                      >
                        <td className="px-3 py-2.5 text-gray-800 border-b border-violet-50">
                          {technique}
                        </td>
                        <td className="px-3 py-2.5 text-gray-500 border-b border-violet-50">
                          {uses.length}
                        </td>
                        <td className="px-3 py-2.5 text-gray-400 text-xs border-b border-violet-50">
                          {uses[0]?.date}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
