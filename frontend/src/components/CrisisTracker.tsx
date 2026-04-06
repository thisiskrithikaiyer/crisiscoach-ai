"use client";

import { useState } from "react";

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

const SAMPLE: TrackerEntry[] = [
  {
    id: "1",
    date: "Apr 6",
    time: "9:15 AM",
    topic: "Work stress",
    technique: "Deep breathing",
    status: "completed",
    notes: "Felt calmer after 5 min",
  },
  {
    id: "2",
    date: "Apr 5",
    time: "3:30 PM",
    topic: "Anxiety",
    technique: "Grounding (5-4-3-2-1)",
    status: "completed",
    notes: "Reduced panic episode",
  },
  {
    id: "3",
    date: "Apr 4",
    time: "11:00 PM",
    topic: "Sleep issues",
    technique: "Progressive relaxation",
    status: "needs-follow-up",
    notes: "Partial relief, try again",
  },
  {
    id: "4",
    date: "Apr 3",
    time: "2:00 PM",
    topic: "Overwhelm",
    technique: "Box breathing",
    status: "completed",
    notes: "Back to focus in 10 min",
  },
  {
    id: "5",
    date: "Apr 2",
    time: "7:45 AM",
    topic: "Low mood",
    technique: "Behavioral activation",
    status: "in-progress",
    notes: "Journaling + short walk",
  },
];

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

type Tab = "log" | "progress";

export default function CrisisTracker({
  extraEntries = [],
}: {
  extraEntries?: TrackerEntry[];
}) {
  const [tab, setTab] = useState<Tab>("log");
  const [entries, setEntries] = useState<TrackerEntry[]>(SAMPLE);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<Omit<TrackerEntry, "id">>({
    date: "",
    time: "",
    topic: "",
    technique: "",
    status: "completed",
    notes: "",
  });

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
      {/* Tabs */}
      <div className="flex items-center gap-1 px-6 pt-5 border-b border-violet-100">
        {(["log", "progress"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium rounded-t-md transition-colors -mb-px ${
              tab === t
                ? "bg-white border border-b-white border-violet-200 text-violet-700"
                : "text-violet-400 hover:text-violet-600"
            }`}
          >
            {t === "log" ? "What I've done" : "Progress"}
          </button>
        ))}

        {tab === "log" && (
          <button
            onClick={() => setShowForm((v) => !v)}
            className="ml-auto mb-1 flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-lg bg-violet-600 text-white hover:bg-violet-700 transition-colors"
          >
            <span className="text-base leading-none">+</span> Add entry
          </button>
        )}
      </div>

      {/* Table area */}
      <div className="flex-1 overflow-auto px-6 py-4">
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

            <table className="w-full text-sm border-separate border-spacing-y-0.5">
              <thead>
                <tr>
                  {["Date", "Time", "Topic", "Technique", "Status", "Notes"].map(
                    (h, i) => (
                      <th
                        key={h}
                        className={`text-left px-3 py-2 text-xs font-semibold text-violet-500 uppercase tracking-wider bg-violet-50 ${
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
          </>
        )}

        {tab === "progress" && (
          <div className="space-y-6">
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
          </div>
        )}
      </div>
    </div>
  );
}
