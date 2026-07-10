const { spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const rootDir = path.resolve(__dirname, "..");
const backendDir = path.join(rootDir, "backend");

function getPythonExecutable() {
  const venvPython = path.join(
    backendDir,
    ".venv",
    process.platform === "win32" ? path.join("Scripts", "python.exe") : path.join("bin", "python")
  );
  return fs.existsSync(venvPython) ? venvPython : "python";
}

function hasCommand(command) {
  const result = spawnSync(process.platform === "win32" ? "where" : "which", [command], {
    stdio: "ignore",
    shell: false,
  });
  return result.status === 0;
}

function ensureBootstrap() {
  const pythonExecutable = getPythonExecutable();
  const result = spawnSync(pythonExecutable, [path.join(backendDir, "bootstrap_piper.py")], {
    cwd: backendDir,
    stdio: "inherit",
    shell: false,
  });
  if (result.error) {
    throw result.error;
  }
  return result.status === 0;
}

function findVoiceModel() {
  const envPath = process.env.PIPER_VOICE_MODEL;
  if (envPath && fs.existsSync(envPath)) return envPath;

  const candidates = [];
  const voicesDir = path.join(backendDir, "voices");
  if (fs.existsSync(voicesDir)) {
    const walk = (dir) => {
      if (!fs.existsSync(dir)) return;
      for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        const fullPath = path.join(dir, entry.name);
        if (entry.isDirectory()) {
          walk(fullPath);
        } else if (entry.isFile() && entry.name.toLowerCase().endsWith(".onnx")) {
          candidates.push(fullPath);
        }
      }
    };
    walk(voicesDir);
  }

  return candidates[0] || null;
}

function runCommand(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: backendDir,
    stdio: "inherit",
    shell: false,
    ...options,
  });
  if (result.error) {
    throw result.error;
  }
  if (result.status !== 0) {
    throw new Error(`${command} ${args.join(" ")} exited with code ${result.status}`);
  }
}

function main() {
  console.log("Checking audio generation prerequisites...");

  const pythonExecutable = getPythonExecutable();
  const hasFfmpeg = hasCommand("ffmpeg");
  const voiceModel = findVoiceModel();

  if (!hasFfmpeg) {
    console.log("Audio pre-generation skipped.");
    console.log("- ffmpeg was not found.");
    return;
  }

  const bootstrapOk = ensureBootstrap();
  if (!bootstrapOk) {
    console.log("Audio pre-generation skipped because Piper bootstrap failed.");
    return;
  }

  const resolvedVoiceModel = findVoiceModel();
  if (!resolvedVoiceModel) {
    console.log("Audio pre-generation skipped because a Piper voice model is still unavailable.");
    return;
  }

  console.log(`Using voice model: ${resolvedVoiceModel}`);
  runCommand(pythonExecutable, [path.join(backendDir, "generate_audio.py"), "--voice", resolvedVoiceModel]);
  runCommand(pythonExecutable, [path.join(backendDir, "generate_word_audio.py"), "--voice", resolvedVoiceModel]);
  console.log("Audio pre-generation complete.");
}

main();
