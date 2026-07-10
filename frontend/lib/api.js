const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export async function fetchQuestions() {
  const res = await fetch(`${BASE_URL}/api/questions`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load questions");
  return res.json();
}

export async function fetchQuestion(id) {
  const res = await fetch(`${BASE_URL}/api/questions/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load question");
  return res.json();
}

export async function submitRecording(questionId, audioBlob) {
  const formData = new FormData();
  formData.append("question_id", questionId);
  formData.append("audio", audioBlob, "recording.webm");

  const res = await fetch(`${BASE_URL}/api/score`, { method: "POST", body: formData });
  if (!res.ok) throw new Error("Failed to score recording");
  return res.json();
}

export async function fetchReadAloudFiltered({
  search = "",
  order = "newest",
  complexity = "",
  page = 1,
  limit = 10,
} = {}) {
  const params = new URLSearchParams({ search, order, complexity, page, limit });
  const res = await fetch(`${BASE_URL}/api/read-aloud?${params.toString()}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load Read Aloud passages");
  return res.json();
}

export async function fetchReadAloudItem(id) {
  const res = await fetch(`${BASE_URL}/api/read-aloud/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load passage");
  return res.json();
}

export async function submitReadAloudRecording(passageId, audioBlob) {
  const formData = new FormData();
  formData.append("passage_id", passageId);
  formData.append("audio", audioBlob, "recording.webm");

  const res = await fetch(`${BASE_URL}/api/read-aloud/score`, { method: "POST", body: formData });
  if (!res.ok) throw new Error("Failed to score recording");
  return res.json();
}

export async function fetchWords(difficulty = null, limit = 100) {
  const params = new URLSearchParams();
  if (difficulty) params.set("difficulty", difficulty);
  params.set("limit", limit);
  const res = await fetch(`${BASE_URL}/api/words?${params.toString()}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load word drills");
  return res.json();
}

export async function fetchWord(word) {
  const res = await fetch(`${BASE_URL}/api/words/${encodeURIComponent(word)}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load word");
  return res.json();
}

export async function submitWordRecording(word, audioBlob) {
  const formData = new FormData();
  formData.append("word", word);
  formData.append("audio", audioBlob, "recording.webm");

  const res = await fetch(`${BASE_URL}/api/words/score`, { method: "POST", body: formData });
  if (!res.ok) throw new Error("Failed to score word recording");
  return res.json();
}

export async function submitWordSetRecordings(words, audioBlobs) {
  const formData = new FormData();
  words.forEach((word) => formData.append("words", word));
  audioBlobs.forEach((blob, index) => {
    formData.append("audio", blob, `word-${index + 1}.webm`);
  });

  const res = await fetch(`${BASE_URL}/api/words/score-batch`, { method: "POST", body: formData });
  if (!res.ok) throw new Error("Failed to score word set");
  return res.json();
}

export async function runSyncData() {
  const res = await fetch(`${BASE_URL}/api/sync-data`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to start sync");
  return res.json();
}

export async function fetchSyncStatus() {
  const res = await fetch(`${BASE_URL}/api/sync-data/status`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load sync status");
  return res.json();
}
