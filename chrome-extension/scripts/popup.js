/**
 * LinkedIn Match AI - Unified Popup Script
 * Consolidates profile setup, settings, and stats
 */

let userProfile = null;
let settings = null;

// Initialize popup
document.addEventListener('DOMContentLoaded', async () => {
  await loadUserProfile();
  await loadSettings();
  await loadStats();
  await loadFeedbackStats();  // NEW: Load feedback data
  setupEventListeners();
});

/**
 * Load user profile from storage
 */
async function loadUserProfile() {
  return new Promise((resolve) => {
    chrome.storage.local.get('userProfile', (result) => {
      userProfile = result.userProfile || {
        name: '',
        skills: [],
        experienceYears: 5,
        connections: 500,
        industry: '',
        seniority: '',
        location: '',
        headline: '',
        initialized: false
      };

      updateProfileUI();
      resolve();
    });
  });
}

/**
 * Update profile UI based on current profile
 */
function updateProfileUI() {
  const profileStatus = document.getElementById('profile-status');
  const profilePreview = document.getElementById('profile-preview');
  const linkedinUrl = document.getElementById('linkedin-url');

  if (userProfile.initialized) {
    // Show profile is set
    profileStatus.textContent = '✓ Set';
    profileStatus.classList.add('set');

    // Show profile preview
    document.getElementById('preview-name').textContent = userProfile.name;
    document.getElementById('preview-skills').textContent = userProfile.skills.slice(0, 3).join(', ') + (userProfile.skills.length > 3 ? '...' : '');
    document.getElementById('preview-experience').textContent = `${userProfile.experienceYears} years`;

    profilePreview.style.display = 'block';
    linkedinUrl.style.display = 'none';
    document.getElementById('btn-extract').style.display = 'none';
    document.querySelector('.divider').style.display = 'none';
    document.getElementById('btn-toggle-manual').style.display = 'none';
  } else {
    profileStatus.textContent = 'Not Set';
    profileStatus.classList.remove('set');
    profilePreview.style.display = 'none';
  }
}

/**
 * Load settings
 */
async function loadSettings() {
  return new Promise((resolve) => {
    chrome.storage.sync.get({
      apiEnabled: true,
      minScoreThreshold: 40
    }, (result) => {
      settings = result;

      // Update UI
      document.getElementById('toggle-enabled').checked = settings.apiEnabled;
      document.getElementById('threshold-slider').value = settings.minScoreThreshold;
      document.getElementById('threshold-value').textContent = settings.minScoreThreshold;

      resolve();
    });
  });
}

/**
 * Load statistics
 */
async function loadStats() {
  return new Promise((resolve) => {
    chrome.storage.local.get(['profileCache', 'totalScans'], (result) => {
      const cacheSize = result.profileCache ? Object.keys(result.profileCache).length : 0;
      const totalScans = result.totalScans || 0;

      // Calculate average score
      let avgScore = '-';
      if (result.profileCache && cacheSize > 0) {
        const scores = Object.values(result.profileCache).map(entry => entry.data.compatibility_score);
        const sum = scores.reduce((a, b) => a + b, 0);
        avgScore = (sum / scores.length).toFixed(1);
      }

      document.getElementById('stat-scans').textContent = totalScans;
      document.getElementById('stat-avg').textContent = avgScore;

      resolve();
    });
  });
}

/**
 * Load feedback statistics (NEW)
 */
async function loadFeedbackStats() {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage({ action: 'getFeedback' }, (response) => {
      if (response && response.success) {
        const stats = response.data.stats;
        document.getElementById('stat-feedback-total').textContent = stats.total;
        document.getElementById('stat-feedback-useful').textContent = stats.accuracy;
      }
      resolve();
    });
  });
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
  // Extract profile button
  document.getElementById('btn-extract').addEventListener('click', extractProfile);

  // Toggle manual entry
  document.getElementById('btn-toggle-manual').addEventListener('click', () => {
    const manualForm = document.getElementById('manual-form');
    manualForm.style.display = manualForm.style.display === 'none' ? 'block' : 'none';
  });

  // Save manual profile
  document.getElementById('btn-save-manual').addEventListener('click', saveManualProfile);

  // Edit profile
  document.getElementById('btn-edit-profile').addEventListener('click', editProfile);

  // Enable toggle
  document.getElementById('toggle-enabled').addEventListener('change', async (e) => {
    settings.apiEnabled = e.target.checked;
    await chrome.storage.sync.set({ apiEnabled: settings.apiEnabled });
    showMessage('Settings saved!', 'success');
  });

  // Threshold slider
  document.getElementById('threshold-slider').addEventListener('input', async (e) => {
    const value = parseInt(e.target.value);
    document.getElementById('threshold-value').textContent = value;
    settings.minScoreThreshold = value;
    await chrome.storage.sync.set({ minScoreThreshold: value });
  });

  // Clear cache
  document.getElementById('btn-clear-cache').addEventListener('click', async () => {
    if (confirm('Clear all cached compatibility scores?')) {
      await chrome.storage.local.set({ profileCache: {}, totalScans: 0 });
      await loadStats();
      showMessage('Cache cleared!', 'success');
    }
  });

  // NEW: Export feedback as CSV
  document.getElementById('btn-export-feedback').addEventListener('click', async () => {
    chrome.runtime.sendMessage({ action: 'exportFeedback' }, (response) => {
      if (response && response.success) {
        // Download CSV
        const blob = new Blob([response.csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `linkedin_match_feedback_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        URL.revokeObjectURL(url);
        showFeedbackMessage('✅ Feedback exported!', 'success');
      } else {
        showFeedbackMessage('No feedback data to export', 'error');
      }
    });
  });

  // NEW: Clear feedback data
  document.getElementById('btn-clear-feedback').addEventListener('click', async () => {
    if (confirm('Clear all collected feedback data? This cannot be undone.')) {
      chrome.runtime.sendMessage({ action: 'clearFeedback' }, async (response) => {
        if (response && response.success) {
          await loadFeedbackStats();
          showFeedbackMessage('✅ Feedback cleared!', 'success');
        }
      });
    }
  });
}

/**
 * Show message in feedback section
 */
function showFeedbackMessage(text, type) {
  const messageEl = document.getElementById('feedback-message');
  messageEl.textContent = text;
  messageEl.className = `message ${type}`;
  messageEl.style.display = 'block';

  setTimeout(() => {
    messageEl.style.display = 'none';
  }, 3000);
}

/**
 * Extract profile from LinkedIn URL
 */
async function extractProfile() {
  const urlInput = document.getElementById('linkedin-url');
  const url = urlInput.value.trim();

  if (!url) {
    showMessage('Please enter your LinkedIn profile URL', 'error');
    return;
  }

  if (!url.includes('linkedin.com/in/')) {
    showMessage('Invalid LinkedIn profile URL', 'error');
    return;
  }

  // Normalize URL
  let normalizedUrl = url;
  if (!normalizedUrl.startsWith('http')) {
    normalizedUrl = 'https://' + normalizedUrl;
  }

  showMessage('⏳ Extracting profile...', 'info');
  document.getElementById('btn-extract').disabled = true;

  try {
    // Check for existing tab
    const existingTabs = await chrome.tabs.query({ url: normalizedUrl });

    let targetTab;
    let createdNewTab = false;

    if (existingTabs.length > 0) {
      targetTab = existingTabs[0];
      await chrome.tabs.update(targetTab.id, { active: true });
      await chrome.tabs.reload(targetTab.id);
    } else {
      targetTab = await chrome.tabs.create({ url: normalizedUrl, active: false });
      createdNewTab = true;
    }

    // Wait for page load
    await waitForTabLoad(targetTab.id);
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Extract profile
    const response = await chrome.tabs.sendMessage(targetTab.id, {
      action: 'extractMyProfile'
    });

    // Close temp tab
    if (createdNewTab) {
      await chrome.tabs.remove(targetTab.id);
    }

    if (response.success) {
      // Save profile
      userProfile = {
        ...response.profile,
        initialized: true,
        lastUpdated: Date.now()
      };

      await chrome.storage.local.set({ userProfile });

      showMessage(`✅ Profile extracted! Found ${response.profile.skills.length} skills.`, 'success');
      updateProfileUI();
    } else {
      showMessage(`❌ ${response.error}`, 'error');
    }
  } catch (error) {
    console.error('Extraction error:', error);
    showMessage('❌ Failed to extract profile. Please try again.', 'error');
  } finally {
    document.getElementById('btn-extract').disabled = false;
  }
}

/**
 * Wait for tab to load
 */
function waitForTabLoad(tabId, timeout = 15000) {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();

    const checkStatus = () => {
      chrome.tabs.get(tabId, (tab) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
          return;
        }

        if (tab.status === 'complete') {
          resolve(tab);
        } else if (Date.now() - startTime > timeout) {
          reject(new Error('Tab loading timeout'));
        } else {
          setTimeout(checkStatus, 500);
        }
      });
    };

    checkStatus();
  });
}

/**
 * Save manual profile
 */
async function saveManualProfile() {
  const name = document.getElementById('input-name').value.trim();
  const skills = document.getElementById('input-skills').value.trim().split(',').map(s => s.trim()).filter(s => s);
  const experienceYears = parseInt(document.getElementById('input-experience').value) || 5;
  const connections = parseInt(document.getElementById('input-connections').value) || 500;

  if (!name || skills.length === 0) {
    showMessage('Please fill in at least name and skills', 'error');
    return;
  }

  userProfile = {
    name,
    skills,
    experienceYears,
    connections,
    industry: '',
    seniority: '',
    location: '',
    headline: '',
    initialized: true,
    lastUpdated: Date.now()
  };

  await chrome.storage.local.set({ userProfile });

  showMessage('✅ Profile saved!', 'success');
  document.getElementById('manual-form').style.display = 'none';
  updateProfileUI();
}

/**
 * Edit profile
 */
function editProfile() {
  document.getElementById('profile-preview').style.display = 'none';
  document.getElementById('linkedin-url').style.display = 'block';
  document.getElementById('btn-extract').style.display = 'block';
  document.querySelector('.divider').style.display = 'flex';
  document.getElementById('btn-toggle-manual').style.display = 'block';

  const profileStatus = document.getElementById('profile-status');
  profileStatus.textContent = 'Editing';
  profileStatus.classList.remove('set');
}

/**
 * Show message to user
 */
function showMessage(text, type) {
  const messageEl = document.getElementById('profile-message');
  messageEl.textContent = text;
  messageEl.className = `message ${type}`;
  messageEl.style.display = 'block';

  setTimeout(() => {
    messageEl.style.display = 'none';
  }, 5000);
}
