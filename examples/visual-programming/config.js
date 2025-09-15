// EDPMT Visual Programming Configuration
// Carries both HTTP and WebSocket URLs and keeps them in sync.

function httpToWs(url) {
  if (!url) return '';
  let ws = url.trim();
  ws = ws.replace(/^https:\/\//i, 'wss://').replace(/^http:\/\//i, 'ws://');
  // Ensure trailing /ws path
  if (!/\/ws(\/?|$)/i.test(ws)) {
    ws = ws.replace(/\/?$/, '') + '/ws';
  }
  return ws;
}

function normalizeHttp(url) {
  if (!url) return '';
  let http = url.trim();
  // If given a ws URL, convert back to http(s)
  http = http.replace(/^wss:\/\//i, 'https://').replace(/^ws:\/\//i, 'http://');
  // Strip trailing /ws if present
  http = http.replace(/\/ws\/?$/i, '');
  return http;
}

function loadConfig() {
  // Defaults
  let httpUrl = 'https://localhost:8888';
  let wsUrl = httpToWs(httpUrl);

  // Runtime override injected by start-all.sh (highest priority)
  try {
    if (typeof window !== 'undefined' && window.EDPMT_RUNTIME) {
      if (window.EDPMT_RUNTIME.httpUrl) httpUrl = window.EDPMT_RUNTIME.httpUrl;
      if (window.EDPMT_RUNTIME.wsUrl) wsUrl = window.EDPMT_RUNTIME.wsUrl;
    }
  } catch (_) {}

  // localStorage overrides
  try {
    const saved = JSON.parse(localStorage.getItem('edpmtConfig') || '{}');
    if (saved.httpUrl) httpUrl = saved.httpUrl;
    if (saved.wsUrl) wsUrl = saved.wsUrl;
  } catch (_) {}

  // URL param overrides
  const params = new URLSearchParams(window.location.search);
  const serverUrlParam = params.get('serverUrl'); // accepts http(s) or ws(s)
  const edpmtPortParam = params.get('edpmtPort');
  if (serverUrlParam) {
    if (/^wss?:\/\//i.test(serverUrlParam)) {
      wsUrl = serverUrlParam;
      httpUrl = normalizeHttp(wsUrl);
    } else {
      httpUrl = serverUrlParam;
      wsUrl = httpToWs(httpUrl);
    }
  }
  if (edpmtPortParam) {
    // Replace or append port on httpUrl
    if (/^https?:\/\//i.test(httpUrl)) {
      // Handle host[:port]
      const url = new URL(httpUrl);
      url.port = edpmtPortParam;
      httpUrl = url.toString().replace(/\/$/, '');
    } else {
      httpUrl = httpUrl.replace(/:\d+/, '') + ':' + edpmtPortParam;
    }
    wsUrl = httpToWs(httpUrl);
  }

  const config = { httpUrl, wsUrl };
  try { localStorage.setItem('edpmtConfig', JSON.stringify(config)); } catch (_) {}
  return config;
}

const CONFIG = loadConfig();
export default CONFIG;
