'use strict';
// JingleMaker - Electron main process
// Everything (settings, sessions, recordings, finished jingles) lives in the folder where the exe is placed.
const { app, BrowserWindow, ipcMain, dialog, powerSaveBlocker, session, shell } = require('electron');
const path = require('path');
const fs = require('fs');
const fsp = fs.promises;

const ROOT = process.env.PORTABLE_EXECUTABLE_DIR
  || (app.isPackaged ? path.dirname(process.execPath) : path.join(__dirname, 'devroot'));
const DIRS = {
  settings: path.join(ROOT, '設定'),
  oke: path.join(ROOT, 'ジングルオケ'),
  sessions: path.join(ROOT, 'セッション')
};

function prepareFolders() {
  try {
    fs.mkdirSync(DIRS.settings, { recursive: true });
    const probe = path.join(DIRS.settings, '.write_test');
    fs.writeFileSync(probe, 'ok'); fs.unlinkSync(probe);
    fs.mkdirSync(DIRS.oke, { recursive: true });
    fs.mkdirSync(DIRS.sessions, { recursive: true });
    return null;
  } catch (e) { return e; }
}
const folderError = prepareFolders();
if (!folderError) {
  // keep the app's own data (settings, cache) inside the folder too
  app.setPath('userData', path.join(DIRS.settings, 'app'));
  try { app.setPath('sessionData', path.join(DIRS.settings, 'app')); } catch (e) {}
}

let win = null;
let recording = false;

if (!app.requestSingleInstanceLock()) {
  app.quit();
} else {
  app.on('second-instance', () => { if (win) { if (win.isMinimized()) win.restore(); win.focus(); } });
  app.whenReady().then(start);
}

async function start() {
  if (folderError) {
    await dialog.showMessageBox({
      type: 'error', title: 'JingleMaker', message: 'この場所には保存できません',
      detail: `JingleMakerのフォルダを、書き込みできる場所（例：C:\\JingleMaker）に移してください。\n\n今の場所：${ROOT}`
    });
    app.quit(); return;
  }
  if (/onedrive|google ?drive|dropbox|[\\/]box[\\/]|icloud/i.test(ROOT)) {
    await dialog.showMessageBox({
      type: 'warning', title: 'JingleMaker', message: 'クラウドと同期しているフォルダに置かれているようです',
      detail: `録音が正しく保存されないことがあります。同期していない場所（例：C:\\JingleMaker）に移してください。\n\n今の場所：${ROOT}`
    });
  }
  // no system sleep, no display sleep, no screensaver while the app is open
  powerSaveBlocker.start('prevent-display-sleep');

  const ses = session.defaultSession;
  ses.setPermissionRequestHandler((wc, perm, cb) => cb(true));
  ses.setPermissionCheckHandler(() => true);
  ses.setDevicePermissionHandler(() => true);

  win = new BrowserWindow({
    width: 1400, height: 900, show: false, backgroundColor: '#15171A', title: 'JingleMaker',
    icon: path.join(__dirname, 'icon.png'), autoHideMenuBar: true,
    webPreferences: { preload: path.join(__dirname, 'preload.js'), contextIsolation: true, nodeIntegration: false, backgroundThrottling: false, spellcheck: false }
  });
  win.setMenuBarVisibility(false);
  win.once('ready-to-show', () => { win.maximize(); win.show(); });
  win.on('close', e => {
    if (recording) {
      e.preventDefault();
      dialog.showMessageBox(win, { type: 'warning', title: 'JingleMaker', message: '録音中です', detail: '録音を止めてから閉じてください。' });
    }
  });
  win.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  win.webContents.on('will-navigate', e => e.preventDefault());
  await win.loadFile(path.join(__dirname, 'app', 'index.html'));
}
app.on('window-all-closed', () => app.quit());

// ---------- file access for the page (limited to the app folder and folders the user picks) ----------
const allowed = new Set([path.resolve(ROOT)]);
function check(p) {
  const r = path.resolve(p);
  for (const a of allowed) if (r === a || r.startsWith(a + path.sep)) return r;
  throw new Error('この場所にはアクセスできません: ' + p);
}
ipcMain.handle('jm:info', () => ({ root: ROOT, dirs: DIRS, version: app.getVersion(), sep: path.sep }));
ipcMain.on('jm:recording', (e, v) => { recording = !!v; });
ipcMain.handle('jm:zoom', (e, z) => { const f = Math.max(0.5, Math.min(2, +z || 1)); e.sender.setZoomFactor(f); return f; });
ipcMain.handle('jm:mkdir', async (e, p) => { await fsp.mkdir(check(p), { recursive: true }); });
ipcMain.handle('jm:list', async (e, p) => {
  const ents = await fsp.readdir(check(p), { withFileTypes: true });
  return ents.map(d => ({ name: d.name, dir: d.isDirectory() }));
});
ipcMain.handle('jm:stat', async (e, p) => {
  try { const s = await fsp.stat(check(p)); return { size: s.size, mtime: s.mtimeMs, dir: s.isDirectory() }; } catch (err) { return null; }
});
ipcMain.handle('jm:read', async (e, p, start, end) => {
  const r = check(p);
  if (start == null) { const b = await fsp.readFile(r); return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength); }
  const fh = await fsp.open(r, 'r');
  try {
    const len = Math.max(0, end - start), b = Buffer.alloc(len);
    const { bytesRead } = await fh.read(b, 0, len, start);
    return b.buffer.slice(b.byteOffset, b.byteOffset + bytesRead);
  } finally { await fh.close(); }
});
ipcMain.handle('jm:write', async (e, p, data) => {
  // write to a temp file first, then swap it in, so a half-written file never replaces a good one
  const r = check(p), tmp = r + '.tmp';
  await fsp.writeFile(tmp, Buffer.from(data));
  await fsp.rename(tmp, r);
});
ipcMain.handle('jm:remove', async (e, p) => { await fsp.rm(check(p), { recursive: true, force: true }); });
ipcMain.handle('jm:pickFolder', async (e, def) => {
  const r = await dialog.showOpenDialog(win, { properties: ['openDirectory'], defaultPath: def || DIRS.oke });
  if (r.canceled || !r.filePaths[0]) return null;
  allowed.add(path.resolve(r.filePaths[0]));
  return r.filePaths[0];
});
ipcMain.handle('jm:allow', async (e, p) => { if (p && fs.existsSync(p)) { allowed.add(path.resolve(p)); return true; } return false; });
ipcMain.handle('jm:openFolder', async (e, p) => { await shell.openPath(check(p)); });
