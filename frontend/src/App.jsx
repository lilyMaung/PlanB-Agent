import { useEffect, useRef, useState } from "react";
import "./App.css";

const API_BASE = import.meta.env.VITE_API_BASE || "";
const POLL_INTERVAL_MS = 1500;

const REASONING_LINES = [
  "Reading what happened...",
  "Searching the web for a real option...",
  "Opening the page to verify a real contact...",
  "Drafting your outreach message...",
  "Almost ready...",
];

function InputScreen({ onSubmit }) {
  const [description, setDescription] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!description.trim()) return;
    onSubmit(description.trim());
  };

  return (
    <div className="screen input-screen">
      <h1>Plan B</h1>
      <p className="subtitle">Tell us what fell through. We'll find a way around it.</p>
      <form onSubmit={handleSubmit}>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="e.g. My flight to Chicago got cancelled and I have a meeting there tomorrow morning..."
          rows={6}
          autoFocus
        />
        <button type="submit" disabled={!description.trim()}>
          Find my plan B
        </button>
      </form>
    </div>
  );
}

function LoadingScreen() {
  const [lineIndex, setLineIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setLineIndex((i) => Math.min(i + 1, REASONING_LINES.length - 1));
    }, 2200);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="screen loading-screen">
      <div className="spinner" />
      <p className="reasoning-line" key={lineIndex}>
        {REASONING_LINES[lineIndex]}
      </p>
    </div>
  );
}

function OutreachDraft({ outreach }) {
  const [copied, setCopied] = useState(false);
  if (!outreach) return null;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(outreach.email_draft);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // clipboard access denied - user can still select text manually
    }
  };

  return (
    <div className="outreach">
      <div className="outreach-header">
        <span className="outreach-label">Drafted message</span>
        <button type="button" className="copy-btn" onClick={handleCopy}>
          {copied ? "Copied ✓" : "Copy"}
        </button>
      </div>
      <p className="outreach-body">{outreach.email_draft}</p>
      <p className="outreach-note">Review before sending — nothing has been sent.</p>
    </div>
  );
}

function ResultCard({ option }) {
  return (
    <div className="card">
      <div className="card-top">
        <h2>{option.title}</h2>
        <span className="verified-badge">✓ Verified</span>
      </div>
      <p className="card-description">{option.description}</p>
      <p className="why">{option.why_it_works}</p>
      {option.url && (
        <a className="option-link" href={option.url} target="_blank" rel="noreferrer">
          View source ↗
        </a>
      )}
      <OutreachDraft outreach={option.outreach} />
    </div>
  );
}

function ResultsScreen({ options, onRestart }) {
  return (
    <div className="screen results-screen">
      <h1>Here's your plan B</h1>
      <p className="subtitle">Checked for a real way to reach out before being shown to you.</p>
      <div className="card-stack">
        {options.map((option, i) => (
          <ResultCard option={option} key={i} />
        ))}
      </div>
      <button className="restart" onClick={onRestart}>
        Start over
      </button>
    </div>
  );
}

function ErrorScreen({ message, onRestart }) {
  return (
    <div className="screen error-screen">
      <h1>Something went wrong</h1>
      <p>{message}</p>
      <button onClick={onRestart}>Try again</button>
    </div>
  );
}

export default function App() {
  const [screen, setScreen] = useState("input");
  const [options, setOptions] = useState([]);
  const [error, setError] = useState("");
  const pollRef = useRef(null);

  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  useEffect(() => stopPolling, []);

  const startPolling = () => {
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/plan/status`);
        const data = await res.json();
        if (data.status === "done") {
          stopPolling();
          setOptions(data.options || []);
          setScreen("results");
        } else if (data.status === "error") {
          stopPolling();
          setError(data.error || "The pathfinder agent hit an error.");
          setScreen("error");
        }
      } catch {
        // transient network hiccup while polling - keep trying
      }
    }, POLL_INTERVAL_MS);
  };

  const handleSubmit = async (description) => {
    setScreen("loading");
    try {
      const res = await fetch(`${API_BASE}/api/plan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description }),
      });
      const data = await res.json();
      if (data.status === "error") {
        setError(data.error || "Could not reach the triage agent.");
        setScreen("error");
        return;
      }
      startPolling();
    } catch (err) {
      setError(err.message);
      setScreen("error");
    }
  };

  const handleRestart = () => {
    stopPolling();
    setOptions([]);
    setError("");
    setScreen("input");
  };

  return (
    <div className="app">
      {screen === "input" && <InputScreen onSubmit={handleSubmit} />}
      {screen === "loading" && <LoadingScreen />}
      {screen === "results" && <ResultsScreen options={options} onRestart={handleRestart} />}
      {screen === "error" && <ErrorScreen message={error} onRestart={handleRestart} />}
    </div>
  );
}
