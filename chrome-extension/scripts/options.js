/**
 * Options Page Script
 */

let settings = {};

document.addEventListener('DOMContentLoaded', async () => {
  await loadSettings();
  setupEventListeners();
});

async function loadSettings() {
  settings = await chrome.storage.sync.get({
    apiEnabled: true,
    showScoreOverlay: true,
    cacheEnabled: true,
    analyticsEnabled: true,
    minScoreThreshold: 40
  });
  
  // Update UI
  updateToggle('toggle-api', settings.apiEnabled);
  updateToggle('toggle-overlay', settings.showScoreOverlay);
  updateToggle('toggle-cache', settings.cacheEnabled);
  updateToggle('toggle-analytics', settings.analyticsEnabled);
  
  document.getElementById('slider-threshold').value = settings.minScoreThreshold;
  document.getElementById('threshold-value').textContent = settings.minScoreThreshold;
}

function updateToggle(id, active) {
  const toggle = document.getElementById(id);
  if (active) {
    toggle.classList.add('active');
  } else {
    toggle.classList.remove('active');
  }
}

function setupEventListeners() {
  // Toggle switches
  document.getElementById('toggle-api').addEventListener('click', function() {
    this.classList.toggle('active');
    settings.apiEnabled = this.classList.contains('active');
  });
  
  document.getElementById('toggle-overlay').addEventListener('click', function() {
    this.classList.toggle('active');
    settings.showScoreOverlay = this.classList.contains('active');
  });
  
  document.getElementById('toggle-cache').addEventListener('click', function() {
    this.classList.toggle('active');
    settings.cacheEnabled = this.classList.contains('active');
  });
  
  document.getElementById('toggle-analytics').addEventListener('click', function() {
    this.classList.toggle('active');
    settings.analyticsEnabled = this.classList.contains('active');
  });
  
  // Threshold slider
  document.getElementById('slider-threshold').addEventListener('input', function() {
    const value = this.value;
    document.getElementById('threshold-value').textContent = value;
    settings.minScoreThreshold = parseInt(value);
  });
  
  // Save button
  document.getElementById('btn-save').addEventListener('click', saveSettings);
  
  // Reset button
  document.getElementById('btn-reset').addEventListener('click', resetSettings);
}

async function saveSettings() {
  await chrome.storage.sync.set(settings);
  showToast();
}

async function resetSettings() {
  if (confirm('Reset all settings to defaults?')) {
    settings = {
      apiEnabled: true,
      showScoreOverlay: true,
      cacheEnabled: true,
      analyticsEnabled: true,
      minScoreThreshold: 40
    };
    
    await chrome.storage.sync.set(settings);
    await loadSettings();
    showToast('Settings reset to defaults');
  }
}

function showToast(message = 'Settings saved successfully!') {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.classList.add('show');
  
  setTimeout(() => {
    toast.classList.remove('show');
  }, 3000);
}
