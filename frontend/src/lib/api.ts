export interface Message {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  reply: string;
  chips: string[];
  intent: string;
  agent: string;
  sources?: string[];
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const TOKEN_KEY = "cc_token";
const TOKEN_VERSION_KEY = "cc_token_v";
const TOKEN_VERSION = "2"; // bump this whenever auth system changes

// --- Token helpers ---
export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  // If token is from a previous auth system, discard it
  if (localStorage.getItem(TOKEN_VERSION_KEY) !== TOKEN_VERSION) {
    localStorage.removeItem(TOKEN_KEY);
    return null;
  }
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(TOKEN_VERSION_KEY, TOKEN_VERSION);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(TOKEN_VERSION_KEY);
}

// --- Auth ---
export async function login(email: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `Login failed: ${res.status}`);
  }

  return res.json();
}

export async function register(email: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `Registration failed: ${res.status}`);
  }

  return res.json();
}

// --- Profile ---
export async function saveResume(text: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/profile/resume`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${getToken()}`,
    },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `Failed to save resume: ${res.status}`);
  }
}

export async function saveLinkedIn(text: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/profile/linkedin`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${getToken()}`,
    },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `Failed to save LinkedIn: ${res.status}`);
  }
}

export interface GoalPlan {
  id: string;
  date: string;
  created_at: string;
  goal_committed_at: string | null;
  next_revision_date: string | null;
  goal_stratergy: {
    mode: string;
    resume_score: number;
    linkedin_score: number;
    role_targets: { stretch: string; realistic: string; safety: string };
    daily_targets: { applications: number; networking_messages: number; linkedin_connects: number; leetcode_problems: number };
    weekly_milestones: { week: string; goal: string }[];
    leetcode_tier: string;
    technical_focus: string;
    current_daily_plan: {
      date: string;
      job_apps: number;
      networking: number;
      leetcode_problems: number;
      leetcode_topic: string;
      leetcode_suggested: string[];
      behavioral_focus: string;
      system_design: number;
      coach_note: string;
    };
  };
  revision_analytics: unknown;
}

export async function fetchGoalPlan(): Promise<GoalPlan | null> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/api/goal-plan/recent`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) return null;
  return res.json();
}

export interface ScheduleBlock {
  time: string;
  tasks: string[];
}

export interface TodayPlan {
  plan_id: string;
  date: string;
  coach_note: string;
  priority_mode: string;
  schedule: {
    morning: ScheduleBlock;
    midday: ScheduleBlock;
    evening: ScheduleBlock;
  };
  job_apps: number;
  leetcode_problems: number;
  leetcode_topic: string;
  [key: string]: unknown;
}

export async function fetchTodayPlan(): Promise<TodayPlan | null> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/api/plan/today`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) return null;
  return res.json();
}

export async function generatePlan(): Promise<TodayPlan | null> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/api/plan/generate`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) return null;
  return res.json();
}

export class AuthError extends Error {}

function handleUnauthorized(res: Response) {
  if (res.status === 401) {
    clearToken();
    throw new AuthError("Session expired. Please sign in again.");
  }
}

// --- Chat ---
export async function fetchChatHistory(limit = 10): Promise<Message[]> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/api/chat/history?limit=${limit}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) return [];
  const rows: { role: string; content: string }[] = await res.json();
  return rows.map((r) => ({ role: r.role as "user" | "assistant", content: r.content }));
}

export async function sendMessage(messages: Message[]): Promise<ChatResponse> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ messages }),
  });

  handleUnauthorized(res);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `Request failed: ${res.status}`);
  }

  return res.json();
}
