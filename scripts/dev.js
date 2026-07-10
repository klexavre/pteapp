const { spawn, spawnSync } = require("child_process");
const path = require("path");

const rootDir = path.resolve(__dirname, "..");
const backendDir = path.join(rootDir, "backend");
const frontendDir = path.join(rootDir, "frontend");

function getCommand(command) {
  return process.platform === "win32" ? `${command}.cmd` : command;
}

function getPythonExecutable() {
  const venvPython = path.join(
    backendDir,
    ".venv",
    process.platform === "win32" ? path.join("Scripts", "python.exe") : path.join("bin", "python")
  );
  return venvPython;
}

function killProcessOnPort(port) {
  if (process.platform !== "win32") return;

  const script = `
    $connections = Get-NetTCPConnection -LocalPort ${port} -ErrorAction SilentlyContinue
    if ($connections) {
      $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
      foreach ($pid in $pids) {
        try { Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue } catch {}
      }
    }
    Start-Sleep -Seconds 1
  `;

  spawnSync("powershell.exe", ["-NoProfile", "-Command", script], {
    stdio: "ignore",
    shell: false,
  });
}

function startFrontend() {
  return spawn(getCommand("npm"), ["run", "dev", "--", "--hostname", "127.0.0.1", "--port", "3000"], {
    cwd: frontendDir,
    stdio: "inherit",
    shell: process.platform === "win32",
    env: {
      ...process.env,
      PORT: "3000",
      HOST: "127.0.0.1",
      KMP_DUPLICATE_LIB_OK: "TRUE",
    },
  });
}

const backend = spawn(getPythonExecutable(), ["-m", "uvicorn", "server:app", "--reload", "--port", "8000"], {
  cwd: backendDir,
  stdio: "inherit",
  env: {
    ...process.env,
    KMP_DUPLICATE_LIB_OK: "TRUE",
  },
});

killProcessOnPort(3000);
const frontend = startFrontend();

function stopAll() {
  backend.kill("SIGTERM");
  frontend.kill("SIGTERM");
}

process.on("SIGINT", stopAll);
process.on("SIGTERM", stopAll);

backend.on("exit", (code) => {
  if (code !== 0 && code !== null) {
    console.error(`Backend exited with code ${code}`);
  }
  frontend.kill("SIGTERM");
});

frontend.on("exit", (code) => {
  if (code !== 0 && code !== null) {
    console.error(`Frontend exited with code ${code}`);
  }
  backend.kill("SIGTERM");
});
