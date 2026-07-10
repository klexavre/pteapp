"use client";

/**
 * attempts.js
 * ------------
 * Tracks attempted status in browser localStorage so the Read Aloud list can
 * show the same attempted/not attempted state as the other practice screens.
 */

const STORAGE_KEY = "pte_practice_attempts_v1";

function readStore() {
  if (typeof window === "undefined") return {};
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
  } catch {
    return {};
  }
}

function writeStore(store) {
  if (typeof window === "undefined") return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
}

function getEntry(id) {
  const store = readStore();
  return (
    store[id] || {
      attemptCount: 0,
      lastScore: null,
      history: [],
      tag: null,
      badgeColor: null,
      timeSpentSeconds: 0,
    }
  );
}

export function getAttempt(id) {
  return getEntry(id);
}

export function recordAttempt(id, overallScore) {
  const store = readStore();
  const entry = getEntry(id);
  entry.attemptCount += 1;
  entry.lastScore = overallScore;
  entry.history.push({ score: overallScore, at: new Date().toISOString() });
  store[id] = entry;
  writeStore(store);
  return entry;
}

export function addTimeSpent(id, seconds) {
  const store = readStore();
  const entry = getEntry(id);
  entry.timeSpentSeconds += seconds;
  store[id] = entry;
  writeStore(store);
  return entry;
}

export function setTag(id, tag) {
  const store = readStore();
  const entry = getEntry(id);
  entry.tag = tag;
  store[id] = entry;
  writeStore(store);
  return entry;
}

export function setBadgeColor(id, color) {
  const store = readStore();
  const entry = getEntry(id);
  entry.badgeColor = color;
  store[id] = entry;
  writeStore(store);
  return entry;
}

export function isAttempted(id) {
  return getEntry(id).attemptCount > 0;
}

export function formatTimeSpent(totalSeconds) {
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = Math.floor(totalSeconds % 60);
  return `${h}h ${m}m ${s}s`;
}
