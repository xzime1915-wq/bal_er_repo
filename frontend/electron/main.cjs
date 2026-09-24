const { app, BrowserWindow, shell, session } = require("electron");
const { spawn } = require("child_process");
const path = require("path");
const http = require("http");

const isDev = !app.isPackaged && process.env.SENZ_PROD !== "1";
const ROOT = path.join(__dirname, "../..");
const BACKEND_DIR = path.join(ROOT, "backend");
const PORT = process.env.SENZ_PORT || "8765";

let mainWindow = null;
let backendProcess = null;

function startBackend() {
  if (backendProcess) return;

  const python = process.platform === "win32" ? "python" : "python3";
  backendProcess = spawn(python, ["main.py"], {
    cwd: BACKEND_DIR,
    env: { ...process.env, SENZ_PORT: PORT },
    windowsHide: true,
    stdio: ["ignore", "pipe", "pipe"],
  });

  backendProcess.stdout?.on("data", (d) => {
    if (isDev) process.stdout.write(`[SENZ backend] ${d}`);
  });
  backendProcess.stderr?.on("data", (d) => {
    if (isDev) process.stderr.write(`[SENZ backend] ${d}`);
  });

  backendProcess.on("error", (err) => {
    console.error("Backend failed to start:", err.message);
    if (mainWindow) {
      mainWindow.webContents.send("senz-backend-error", err.message);
    }
  });
}

function stopBackend() {
  if (!backendProcess) return;
  const proc = backendProcess;
  backendProcess = null;
  if (process.platform === "win32") {
    spawn("taskkill", ["/pid", String(proc.pid), "/f", "/t"], { windowsHide: true });
  } else {
    proc.kill("SIGTERM");
  }
}

function waitForBackend(maxMs = 30000) {
  const deadline = Date.now() + maxMs;
  return new Promise((resolve) => {
    const tryOnce = () => {
      const req = http.get(`http://127.0.0.1:${PORT}/api/health`, (res) => {
        res.resume();
        if (res.statusCode === 200) resolve(true);
        else if (Date.now() < deadline) setTimeout(tryOnce, 400);
        else resolve(false);
      });
      req.on("error", () => {
        if (Date.now() < deadline) setTimeout(tryOnce, 400);
        else resolve(false);
      });
      req.setTimeout(2000, () => {
        req.destroy();
        if (Date.now() < deadline) setTimeout(tryOnce, 400);
        else resolve(false);
      });
    };
    tryOnce();
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1600,
    height: 960,
    minWidth: 1200,
    minHeight: 720,
    backgroundColor: "#050a12",
    title: "SENZ",
    autoHideMenuBar: true,
    show: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, "preload.cjs"),
    },
  });

  // Desktop app only — don't open links in external browser unless user wants
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith("http")) shell.openExternal(url);
    return { action: "deny" };
  });

  mainWindow.once("ready-to-show", () => mainWindow.show());

  if (isDev) {
    mainWindow.loadURL("http://localhost:5173");
  } else {
    mainWindow.loadFile(path.join(__dirname, "../dist/index.html"));
  }
}

async function boot() {
  session.defaultSession.setPermissionRequestHandler((_wc, permission, callback) => {
    const ok = ["media", "microphone", "audioCapture", "speechRecognition"].includes(permission);
    callback(ok);
  });
  session.defaultSession.setPermissionCheckHandler((_wc, permission) => {
    return ["media", "microphone", "audioCapture", "speechRecognition"].includes(permission);
  });

  startBackend();
  const ok = await waitForBackend();
  if (!ok) {
    console.warn("SENZ backend slow to start — UI will retry connection");
  }
  createWindow();
}

const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
} else {
  app.on("second-instance", () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });

  app.whenReady().then(boot);

  app.on("window-all-closed", () => {
    stopBackend();
    if (process.platform !== "darwin") app.quit();
  });

  app.on("before-quit", () => stopBackend());
}
