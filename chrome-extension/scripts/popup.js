/**
 * Popup UI Script
 */

document.addEventListener('DOMContentLoaded', async () => {
  await loadStatus();
  await loadStats();
  
  // Event listeners
  document.getElementById('btn-settings').addEventListener('click', () => {
    chrome.runtime.openOptionsPage();
  });
  
  document.getElementById('btn-clear-cache').addEventListener('click', async () => {
    await chrome.runtime.sendMessage({ action: 'clearCache' });
    alert('Cache cleared successfully!');
    await loadStatus();
  });
  
  document.getElementById('btn-docs').addEventListener('click', () => {
    window.open('https://github.com/yourusername/linkedin-match', '_blank');
  });
});

async function loadStatus() {
  // Get API status
  const apiData = await chrome.storage.local.get(['apiStatus', 'modelLoaded', 'profileCache']);
  
  const apiStatus = document.getElementById('api-status');
  const modelStatus = document.getElementById('model-status');
  const cacheSize = document.getElementById('cache-size');
  
  // API Status
  if (apiData.apiStatus === 'healthy') {
    apiStatus.textContent = 'Online';
    apiStatus.className = 'status-badge badge-success';
  } else {
    apiStatus.textContent = 'Offline';
    apiStatus.className = 'status-badge badge-error';
  }
  
  // Model Status
  if (apiData.modelLoaded) {
    modelStatus.textContent = 'Loaded';
    modelStatus.className = 'status-badge badge-success';
  } else {
    modelStatus.textContent = 'Not Loaded';
    modelStatus.className = 'status-badge badge-error';
  }
  
  // Cache size
  const cacheCount = apiData.profileCache ? Object.keys(apiData.profileCache).length : 0;
  cacheSize.textContent = `${cacheCount} profile${cacheCount !== 1 ? 's' : ''}`;
}

async function loadStats() {
  const stats = await chrome.storage.local.get(['totalScans', 'highMatches']);
  
  document.getElementById('total-scans').textContent = stats.totalScans || 0;
  document.getElementById('high-matches').textContent = stats.highMatches || 0;
}
