const { contextBridge } = require("electron");

contextBridge.exposeInMainWorld("senzDesktop", {
  isDesktop: true,
  platform: process.platform,
});
