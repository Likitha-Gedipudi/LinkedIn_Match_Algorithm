/**
 * Options Page Script
 */

let settings = {};
let userProfile = {};

document.addEventListener('DOMContentLoaded', async () => {
  await loadSettings();
  await loadUserProfile();
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
  document.getElementById('toggle-api').addEventListener('click', function () {
    this.classList.toggle('active');
    settings.apiEnabled = this.classList.contains('active');
  });

  document.getElementById('toggle-overlay').addEventListener('click', function () {
    this.classList.toggle('active');
    settings.showScoreOverlay = this.classList.contains('active');
  });

  document.getElementById('toggle-cache').addEventListener('click', function () {
    this.classList.toggle('active');
    settings.cacheEnabled = this.classList.contains('active');
  });

  document.getElementById('toggle-analytics').addEventListener('click', function () {
    this.classList.toggle('active');
    settings.analyticsEnabled = this.classList.contains('active');
  });

  // Threshold slider
  document.getElementById('slider-threshold').addEventListener('input', function () {
    const value = this.value;
    document.getElementById('threshold-value').textContent = value;
    settings.minScoreThreshold = parseInt(value);
  });

  // Save button
  document.getElementById('btn-save').addEventListener('click', saveSettings);

  // Reset button
  document.getElementById('btn-reset').addEventListener('click', resetSettings);

  // Profile save button
  document.getElementById('btn-save-profile').addEventListener('click', saveUserProfileData);

  // Profile extraction button
  document.getElementById('btn-extract-profile').addEventListener('click', extractProfileFromLinkedIn);
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

      // Populate form fields
      document.getElementById('input-name').value = userProfile.name || '';
      document.getElementById('input-skills').value = (userProfile.skills || []).join(', ');
      document.getElementById('input-experience').value = userProfile.experienceYears || '';
      document.getElementById('input-connections').value = userProfile.connections || '';
      document.getElementById('input-industry').value = userProfile.industry || '';
      document.getElementById('input-seniority').value = userProfile.seniority || '';
      document.getElementById('input-location').value = userProfile.location || '';
      document.getElementById('input-headline').value = userProfile.headline || '';

      // Show status if profile is set
      if (userProfile.initialized) {
        showProfileStatus('✅ Profile configured successfully!', 'success');
      }

      resolve(userProfile);
    });
  });
}

/**
 * Save user profile data
 */
async function saveUserProfileData() {
  try {
    // Get form values
    const name = document.getElementById('input-name').value.trim();
    const skillsText = document.getElementById('input-skills').value.trim();
    const skills = skillsText ? skillsText.split(',').map(s => s.trim()).filter(s => s) : [];
    const experienceYears = parseInt(document.getElementById('input-experience').value) || 5;
    const connections = parseInt(document.getElementById('input-connections').value) || 500;
    const industry = document.getElementById('input-industry').value;
    const seniority = document.getElementById('input-seniority').value;
    const location = document.getElementById('input-location').value.trim();
    const headline = document.getElementById('input-headline').value.trim();

    // Validation
    if (!name) {
      showProfileStatus('⚠️ Please enter your name', 'error');
      return;
    }

    if (skills.length === 0) {
      showProfileStatus('⚠️ Please enter at least one skill', 'error');
      return;
    }

    if (!industry) {
      showProfileStatus('⚠️ Please select your industry', 'error');
      return;
    }

    if (!seniority) {
      showProfileStatus('⚠️ Please select your seniority level', 'error');
      return;
    }

    // Save profile
    userProfile = {
      name,
      skills,
      experienceYears,
      connections,
      industry,
      seniority,
      location,
      headline,
      initialized: true,
      lastUpdated: Date.now()
    };

    await chrome.storage.local.set({ userProfile });

    showProfileStatus('✅ Profile saved successfully! Compatibility scores will now be accurate.', 'success');
    showToast('Profile saved! Scores will now be personalized.');

  } catch (error) {
    console.error('Error saving profile:', error);
    showProfileStatus('❌ Error saving profile. Please try again.', 'error');
  }
}

/**
 * Show profile status message
 */
function showProfileStatus(message, type) {
  const statusDiv = document.getElementById('profile-status');
  statusDiv.textContent = message;
  statusDiv.className = `profile-status ${type}`;
  statusDiv.style.display = 'block';

  // Auto-hide success messages after 5 seconds
  if (type === 'success') {
    setTimeout(() => {
      statusDiv.style.display = 'none';
    }, 5000);
  }
}

/**
 * Extract profile automatically from LinkedIn URL
 */
async function extractProfileFromLinkedIn() {
  const extractBtn = document.getElementById('btn-extract-profile');
  const urlInput = document.getElementById('input-linkedin-url');
  const originalText = extractBtn.textContent;

  try {
    // Get URL from input
    const linkedinUrl = urlInput.value.trim();

    // Validate URL
    if (!linkedinUrl) {
      showProfileStatus('⚠️ Please enter your LinkedIn profile URL first', 'error');
      urlInput.focus();
      return;
    }

    // Validate it's a LinkedIn profile URL
    if (!linkedinUrl.includes('linkedin.com/in/')) {
      showProfileStatus('⚠️ Please enter a valid LinkedIn profile URL (must contain "linkedin.com/in/")', 'error');
      urlInput.focus();
      return;
    }

    // Normalize URL
    let normalizedUrl = linkedinUrl;
    if (!normalizedUrl.startsWith('http')) {
      normalizedUrl = 'https://' + normalizedUrl;
    }

    // Update button to show loading state
    extractBtn.disabled = true;
    extractBtn.textContent = '⏳ Extracting...';
    showProfileStatus('🔍 Opening LinkedIn profile...', 'success');

    // Check if tab already exists with this URL
    const existingTabs = await chrome.tabs.query({ url: normalizedUrl });

    let targetTab;
    let createdNewTab = false;

    if (existingTabs.length > 0) {
      // Use existing tab
      targetTab = existingTabs[0];
      // Activate the tab
      await chrome.tabs.update(targetTab.id, { active: true });
      // Reload to ensure fresh data
      await chrome.tabs.reload(targetTab.id);
      showProfileStatus('🔄 Refreshing profile page...', 'success');
    } else {
      // Create new tab
      targetTab = await chrome.tabs.create({ url: normalizedUrl, active: false });
      createdNewTab = true;
      showProfileStatus('📖 Loading profile page...', 'success');
    }

    // Wait for page to load (LinkedIn is slow)
    await waitForTabLoad(targetTab.id);

    // Give LinkedIn a bit more time to fully render
    await new Promise(resolve => setTimeout(resolve, 2000));

    showProfileStatus('⚙️ Extracting profile data...', 'success');

    // Send message to content script to extract profile
    const response = await chrome.tabs.sendMessage(targetTab.id, {
      action: 'extractMyProfile'
    });

    // Close the tab if we created it
    if (createdNewTab) {
      await chrome.tabs.remove(targetTab.id);
    }

    if (response.success) {
      const profile = response.profile;

      // Populate form fields
      document.getElementById('input-name').value = profile.name || '';
      document.getElementById('input-skills').value = (profile.skills || []).join(', ');
      document.getElementById('input-experience').value = profile.experienceYears || '';
      document.getElementById('input-connections').value = profile.connections || '';
      document.getElementById('input-industry').value = profile.industry || '';
      document.getElementById('input-seniority').value = profile.seniority || '';
      document.getElementById('input-location').value = profile.location || '';
      document.getElementById('input-headline').value = profile.headline || '';

      // Show success message
      showProfileStatus(
        `✅ Profile extracted successfully! Found ${profile.skills.length} skills, ${profile.experienceYears} years experience. Review and click "Save My Profile" below.`,
        'success'
      );

      // Scroll to save button
      document.getElementById('btn-save-profile').scrollIntoView({ behavior: 'smooth', block: 'center' });

    } else {
      // Show error from content script
      showProfileStatus(`❌ ${response.error}`, 'error');
    }

  } catch (error) {
    console.error('Extraction error:', error);

    // More helpful error messages
    if (error.message && error.message.includes('Could not establish connection')) {
      showProfileStatus(
        '❌ Could not connect to LinkedIn. The page might still be loading. Please try again in a few seconds.',
        'error'
      );
    } else if (error.message && error.message.includes('No tab with id')) {
      showProfileStatus(
        '❌ Tab was closed. Please try again.',
        'error'
      );
    } else {
      showProfileStatus(`❌ Extraction failed: ${error.message}`, 'error');
    }
  } finally {
    // Restore button
    extractBtn.disabled = false;
    extractBtn.textContent = originalText;
  }
}

/**
 * Wait for tab to finish loading
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
