"use client";

import { useEffect, useState } from "react";
import { fetchSyncStatus, runSyncData } from "@/lib/api";

export default function SyncDataPanel({ compact = false }) {
  const [status, setStatus] = useState({ status: "idle", percent: 0, message: "No sync run yet." });
  const [loading, setLoading] = useState(false);
  const [shouldPoll, setShouldPoll] = useState(false);
  const [plan, setPlan] = useState(null);

  useEffect(() => {
    if (!shouldPoll) return;

    let cancelled = false;
    const poll = async () => {
      try {
        const data = await fetchSyncStatus();
        if (!cancelled) {
          setStatus(data);
          if (data?.status !== "running") setShouldPoll(false);
        }
      } catch {
        // Ignore initial status errors.
      }
    };

    poll();
    const timer = setInterval(poll, 1000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [shouldPoll]);

  useEffect(() => {
    let cancelled = false;
    const fetchPlan = async () => {
      try {
        const res = await fetch('/api/sync-data/plan');
        if (!res.ok) return;
        const data = await res.json();
        if (!cancelled) setPlan(data);
      } catch (e) {
        // ignore
      }
    };
    fetchPlan();
    return () => { cancelled = true; };
  }, []);

  const handleSync = async () => {
    setLoading(true);

    try {
      const data = await runSyncData();
      setStatus(data);
      setShouldPoll(data?.status === "running");
    } catch (err) {
      setStatus({ status: "error", percent: 0, message: err.message });
      setShouldPoll(false);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`sync-panel ${compact ? "compact" : ""}`}>
      <div className="sync-header">
        <strong>Sync data</strong>
        <button className="view-btn" onClick={handleSync} disabled={loading || status.status === "running"}>
          {loading || status.status === "running" ? "Syncing..." : "Run sync"}
        </button>
      </div>

      <div className="progress-track" aria-label="sync progress">
        <div
          className="progress-fill"
          style={{
            width: `${Math.max(
              4,
              (() => {
                if (typeof status.percent === "number" && status.percent > 0) return status.percent;
                if (typeof status.completed === "number" && typeof status.total === "number" && status.total > 0)
                  return Math.round((status.completed / status.total) * 100);
                return 0;
              })()
            )}%`,
          }}
        />
      </div>

      <div className="sync-meta">
        <span>{status.message || "Waiting for sync..."}</span>
        <span>
          {(() => {
            const pct = typeof status.percent === "number" && status.percent >= 0
              ? status.percent
              : typeof status.completed === "number" && typeof status.total === "number" && status.total > 0
              ? Math.round((status.completed / status.total) * 100)
              : 0;
            return `${pct}%`;
          })()}
        </span>
      </div>

      {plan && status.status !== 'running' && (
        <div className="sync-meta secondary">
          <span>Will generate {plan.total_items_to_generate} files</span>
        </div>
      )}

      {(status.status === "running" || status.completed != null) && (
        <div className="sync-meta secondary">
          <span>
            {typeof status.completed_items === "number" && typeof status.total_items_to_generate === "number"
              ? `${status.completed_items}/${status.total_items_to_generate} files`
              : typeof status.completed === "number" && typeof status.total === "number"
              ? `${status.completed}/${status.total} items`
              : "Preparing..."}
          </span>
          <span>
            {typeof status.estimated_remaining_seconds === "number" && status.estimated_remaining_seconds > 0 ? (
              (() => {
                const seconds = status.estimated_remaining_seconds;
                const mins = Math.floor(seconds / 60);
                const secs = seconds % 60;
                const pad = (n) => String(n).padStart(2, "0");
                const eta = new Date(Date.now() + seconds * 1000);
                return `${mins}:${pad(secs)} remaining (ETA ${eta.toLocaleTimeString()})`;
              })()
            ) : (
              "Estimating..."
            )}
          </span>
        </div>
      )}
    </div>
  );
}
