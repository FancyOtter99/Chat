self.addEventListener('install', (e) => {
    self.skipWaiting();
    console.log('Service Worker: Installed');
  });
  
  self.addEventListener('activate', (e) => {
    console.log('Service Worker: Activated');
  });
  
  self.addEventListener('fetch', (e) => {
    // Optionally handle fetch requests
  });
  