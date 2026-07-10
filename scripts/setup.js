const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");

const rootDir = path.resolve(__dirname, "..");
const backendDir = path.join(rootDir, "backend");
const frontendDir = path.join(rootDir, "frontend");

function getPythonCommand() {
  const candidates = [
    "py -3.10",
    "python3.10",
    "python3.9",
    "python",
    "python3",
  ];

  for (const candidate of candidates) {
    try {
      const [cmd, ...args] = candidate.split(/\s+/);
      const result = spawnSync(cmd, [...args, "--version"], { stdio: "ignore" });
      if (result.status === 0) return candidate;
    } catch {
      // ignore and try next candidate
    }
  }
  throw new Error("Python 3.9+ was not found. Install Python 3.10 or 3.9 and try again.");
}

function getNpmCommand() {
  const command = process.platform === "win32" ? "npm.cmd" : "npm";
  return command;
}

function runCommand(command, args, options = {}) {
  const normalizedCommand = process.platform === "win32" && command === "py" ? "py" : command;
  return new Promise((resolve, reject) => {
    const child = spawn(normalizedCommand, args, {
      stdio: "inherit",
      shell: false,
      ...options,
    });

    child.on("error", reject);
    child.on("exit", (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`${command} ${args.join(" ")} exited with code ${code}`));
      }
    });
  });
}

function getVenvPythonPath() {
  const venvDir = path.join(backendDir, ".venv");
  const binDir = process.platform === "win32" ? path.join(venvDir, "Scripts") : path.join(venvDir, "bin");
  return path.join(binDir, process.platform === "win32" ? "python.exe" : "python");
}

function isCompatiblePythonVersion(pythonPath) {
  try {
    const result = spawnSync(pythonPath, ["--version"], { encoding: "utf8" });
    if (result.status !== 0) return false;
    const versionText = result.stdout || result.stderr || "";
    return /Python 3\.(9|10|11)/i.test(versionText);
  } catch {
    return false;
  }
}

async function main() {
  console.log("Setting up the PTE app...");

  const pythonCmd = getPythonCommand();
  const npmCmd = getNpmCommand();
  const venvPython = getVenvPythonPath();

  const pythonExecutable = process.platform === "win32" && pythonCmd.startsWith("py")
    ? "py"
    : pythonCmd.split(/\s+/)[0];
  const pythonArgs = process.platform === "win32" && pythonCmd.startsWith("py")
    ? ["-3.10", "-m", "venv", path.join(backendDir, ".venv")]
    : ["-m", "venv", path.join(backendDir, ".venv")];

  if (!fs.existsSync(venvPython) || !isCompatiblePythonVersion(venvPython)) {
    if (fs.existsSync(path.join(backendDir, ".venv"))) {
      fs.rmSync(path.join(backendDir, ".venv"), { recursive: true, force: true });
    }
    console.log("Creating Python virtual environment in backend/.venv...");
    await runCommand(pythonExecutable, pythonArgs);
  } else {
    console.log("Reusing existing backend virtual environment.");
  }

  console.log("Installing backend Python dependencies...");
  await runCommand(venvPython, ["-m", "pip", "install", "--upgrade", "pip", "setuptools<81", "wheel"]);
  await runCommand(venvPython, ["-m", "pip", "install", "--no-build-isolation", "-r", path.join(backendDir, "requirements.txt")]);

  console.log("Preparing question and word banks...");
  await runCommand(venvPython, [path.join(backendDir, "txt_to_questions.py"), path.join(backendDir, "repeat sentence.txt"), "--output", path.join(backendDir, "questions.json")]);
  await runCommand(venvPython, [path.join(backendDir, "word_extractor.py"), "--questions", path.join(backendDir, "questions.json"), "--output", path.join(backendDir, "word_bank.json")]);

  console.log("Installing frontend dependencies...");
  await runCommand(npmCmd, ["install"], { cwd: frontendDir, shell: process.platform === "win32" });

  console.log("\nSetup complete.");
  console.log("Run: npm run dev");
  console.log("Backend: http://localhost:8000");
  console.log("Frontend: http://localhost:3000");
}

const { spawnSync } = require("child_process");

main().catch((error) => {
  console.error("Setup failed:", error.message);
  process.exit(1);
});
