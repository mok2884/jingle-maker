'use strict';
const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('jmNative', {
  info: () => ipcRenderer.invoke('jm:info'),
  mkdir: p => ipcRenderer.invoke('jm:mkdir', p),
  list: p => ipcRenderer.invoke('jm:list', p),
  stat: p => ipcRenderer.invoke('jm:stat', p),
  read: (p, start, end) => ipcRenderer.invoke('jm:read', p, start, end),
  write: (p, data) => ipcRenderer.invoke('jm:write', p, data),
  remove: p => ipcRenderer.invoke('jm:remove', p),
  pickFolder: def => ipcRenderer.invoke('jm:pickFolder', def),
  allow: p => ipcRenderer.invoke('jm:allow', p),
  openFolder: p => ipcRenderer.invoke('jm:openFolder', p),
  setRecording: v => ipcRenderer.send('jm:recording', v),
  setZoom: z => ipcRenderer.invoke('jm:zoom', z)
});
