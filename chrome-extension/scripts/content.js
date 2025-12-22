/**
 * Content Script - Injected into LinkedIn pages
 * Extracts profile data and displays compatibility scores
 */

let currentProfileId = null;
let settings = {};

// Initialize
(async function init() {
  console.log('LinkedIn Match AI: Content script loaded');
  
  // Get settings
  settings = await getSettings();
  
  if (!settings.apiEnabled || !settings.showScoreOverlay) {
    return;
  }
  
  // Wait for page load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startObserving);
  } else {
    startObserving();
  }
})();

/**
 * Start observing page changes
 */
function startObserving() {
  // Check if we're on a profile page
  checkProfilePage();
  
  // Observe URL changes (LinkedIn is SPA)
  let lastUrl = location.href;
  new MutationObserver(() => {
    const url = location.href;
    if (url !== lastUrl) {
      lastUrl = url;
      checkProfilePage();
    }
  }).observe(document, { subtree: true, childList: true });
}

/**
 * Check if current page is a profile and process it
 */
async function checkProfilePage() {
  const pathname = window.location.pathname;
  
  // Check if we're on My Network page
  if (pathname.includes('/mynetwork/')) {
    // Disconnect profile observer if active
    removeScoreOverlay();
    await processNetworkPage();
    return;
  }
  
  // Not on network page, disconnect network observer
  if (networkPageObserver) {
    networkPageObserver.disconnect();
    networkPageObserver = null;
  }
  
  // Check if we're on a profile page
  const isProfilePage = pathname.includes('/in/');
  
  if (!isProfilePage) {
    removeScoreOverlay();
    return;
  }
  
  // Extract profile ID from URL
  const match = pathname.match(/\/in\/([^/]+)/);
  if (!match) return;
  
  const profileId = match[1];
  
  if (profileId === currentProfileId) {
    return; // Already processed
  }
  
  currentProfileId = profileId;
  
  // Wait for profile content to load
  await waitForElement('.pv-top-card');
  
  // Extract and analyze profile - inject inline
  await analyzeProfileInline(profileId);
}

/**
 * Wait for element to appear
 */
function waitForElement(selector, timeout = 5000) {
  return new Promise((resolve) => {
    if (document.querySelector(selector)) {
      return resolve(document.querySelector(selector));
    }
    
    const observer = new MutationObserver(() => {
      if (document.querySelector(selector)) {
        observer.disconnect();
        resolve(document.querySelector(selector));
      }
    });
    
    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
    
    setTimeout(() => {
      observer.disconnect();
      resolve(null);
    }, timeout);
  });
}

/**
 * Extract profile data from LinkedIn page
 */
function extractProfileData() {
  const data = {
    profileId: currentProfileId,
    name: extractText('.pv-text-details__left-panel h1, .text-heading-xlarge, h1'),
    headline: extractText('.pv-text-details__left-panel .text-body-medium, .text-body-medium'),
    location: extractText('.pv-text-details__left-panel .text-body-small, .text-body-small'),
    connections: extractConnectionCount(),
    experience: extractExperience(),
    skills: extractSkills(),
    education: extractEducation()
  };
  
  console.log('Extracted profile data:', data);
  return data;
}

function extractText(selector) {
  const el = document.querySelector(selector);
  return el ? el.textContent.trim() : '';
}

function extractConnectionCount() {
  const text = extractText('.pv-top-card--list li');
  const match = text.match(/(\d+[\+]?)\s*connections?/i);
  return match ? parseInt(match[1].replace('+', '')) : 0;
}

function extractExperience() {
  const experiences = [];
  document.querySelectorAll('#experience ~ div li.artdeco-list__item').forEach(el => {
    const title = el.querySelector('.mr1.t-bold span')?.textContent.trim();
    const company = el.querySelector('.t-14.t-normal span')?.textContent.trim();
    const duration = el.querySelector('.t-14.t-normal.t-black--light span')?.textContent.trim();
    
    if (title) {
      experiences.push({ title, company, duration });
    }
  });
  return experiences;
}

function extractSkills() {
  const skills = [];
  document.querySelectorAll('[data-field="skill_card_skill_topic"] .mr1.t-bold span').forEach(el => {
    skills.push(el.textContent.trim());
  });
  return skills;
}

function extractEducation() {
  const education = [];
  document.querySelectorAll('#education ~ div li.artdeco-list__item').forEach(el => {
    const school = el.querySelector('.mr1.t-bold span')?.textContent.trim();
    const degree = el.querySelector('.t-14.t-normal span')?.textContent.trim();
    
    if (school) {
      education.push({ school, degree });
    }
  });
  return education;
}

/**
 * Calculate compatibility features from profile data
 */
function calculateFeatures(profileData) {
  // This is a simplified feature extraction
  // In production, you'd compare with the current user's profile
  
  const connectionCount = profileData.connections || 0;
  const experienceYears = profileData.experience.length * 2; // Rough estimate
  const skillCount = profileData.skills.length;
  
  return {
    skill_match_score: Math.min(skillCount * 3, 100),
    skill_complementarity_score: Math.min(skillCount * 2.5, 100),
    network_value_a_to_b: Math.min((connectionCount / 10), 100),
    network_value_b_to_a: Math.min((connectionCount / 10), 100),
    career_alignment_score: Math.random() * 40 + 40, // 40-80
    experience_gap: Math.floor(Math.random() * 10),
    industry_match: Math.random() * 40 + 40,
    geographic_score: Math.random() * 40 + 40,
    seniority_match: Math.random() * 40 + 40
  };
}

/**
 * Process My Network page - inject scores for all visible profiles
 */
let networkPageObserver = null;

async function processNetworkPage() {
  console.log('Processing My Network page...');
  
  // Wait for invitation cards to load
  await waitForElement('[data-control-name="invite_card"], .mn-connection-card', 3000);
  
  // Process initial cards
  await scanAndProcessCards();
  
  // Set up observer for dynamically loaded cards
  if (!networkPageObserver) {
    networkPageObserver = new MutationObserver(() => {
      scanAndProcessCards();
    });
    
    const targetNode = document.querySelector('.scaffold-finite-scroll__content, main');
    if (targetNode) {
      networkPageObserver.observe(targetNode, {
        childList: true,
        subtree: true
      });
    }
  }
}

/**
 * Scan and process all visible profile cards
 */
async function scanAndProcessCards() {
  // Find all profile cards
  const cards = document.querySelectorAll(
    '[data-control-name="invite_card"], ' +
    '.mn-connection-card, ' +
    '.discover-person-card, ' +
    '.reusable-search__result-container'
  );
  
  console.log(`Found ${cards.length} profile cards`);
  
  for (const card of cards) {
    // Skip if already processed
    if (card.querySelector('.linkedin-match-inline-score')) {
      continue;
    }
    
    // Extract profile info - try multiple selectors
    const nameElement = card.querySelector(
      '.mn-connection-card__name, ' +
      '.discover-person-card__name, ' +
      '.entity-result__title-text a, ' +
      'a.app-aware-link span[aria-hidden="true"]'
    );
    const linkElement = card.querySelector('a[href*="/in/"]');
    
    if (!nameElement || !linkElement) continue;
    
    // Extract profile ID from link
    const match = linkElement.href.match(/\/in\/([^/?]+)/);
    if (!match) continue;
    
    const profileId = match[1];
    const profileName = nameElement.textContent.trim();
    
    // Calculate and inject score (with small delay to avoid rate limiting)
    setTimeout(() => {
      injectInlineScoreForCard(card, profileId, profileName, nameElement);
    }, Math.random() * 1000);
  }
}

/**
 * Inject inline score for a single card
 */
async function injectInlineScoreForCard(card, profileId, profileName, nameElement) {
  try {
    // Show loading badge
    const loadingBadge = createInlineScoreBadge('...', 'loading');
    nameElement.parentElement.appendChild(loadingBadge);
    
    // Generate features (simplified)
    const features = calculateFeatures({
      profileId,
      connections: 100,
      skills: [],
      experience: []
    });
    
    // Get compatibility score
    const response = await chrome.runtime.sendMessage({
      action: 'calculateCompatibility',
      data: { profileId, ...features }
    });
    
    // Remove loading badge
    loadingBadge.remove();
    
    if (response.success && response.data) {
      const score = response.data.compatibility_score;
      const badge = createInlineScoreBadge(score.toFixed(0), getScoreClass(score));
      nameElement.parentElement.appendChild(badge);
    }
  } catch (error) {
    console.error('Error calculating score for card:', error);
  }
}

/**
 * Analyze profile and inject score inline (next to name)
 */
async function analyzeProfileInline(profileId) {
  try {
    // Find the profile name element - try multiple selectors
    const nameElement = document.querySelector(
      '.pv-text-details__left-panel h1, ' +
      '.text-heading-xlarge, ' +
      'h1.inline, ' +
      '[data-generated-suggestion-target] h1, ' +
      '.artdeco-entity-lockup__title'
    );
    
    if (!nameElement) {
      console.error('Could not find profile name element. Showing overlay card instead.');
      // Fall back to showing the overlay card only
      await analyzeProfileFallback(profileId);
      return;
    }
    
    // Remove any existing badge
    const existingBadge = document.querySelector('.linkedin-match-inline-score');
    if (existingBadge) {
      existingBadge.remove();
    }
    
    // Show loading badge
    const loadingBadge = createInlineScoreBadge('Analyzing...', 'loading');
    nameElement.parentElement.appendChild(loadingBadge);
    
    // Extract profile data
    const profileData = extractProfileData();
    const features = calculateFeatures(profileData);
    
    // Request compatibility calculation
    const response = await chrome.runtime.sendMessage({
      action: 'calculateCompatibility',
      data: { profileId, ...features }
    });
    
    // Remove loading badge
    loadingBadge.remove();
    
    if (response.error) {
      const errorBadge = createInlineScoreBadge('Error', 'error');
      nameElement.parentElement.appendChild(errorBadge);
      return;
    }
    
    if (response.success && response.data) {
      const score = response.data.compatibility_score;
      const recommendation = response.data.recommendation;
      
      // Create inline score badge
      const badge = createInlineScoreBadge(
        `${score.toFixed(0)} Match`,
        getScoreClass(score),
        recommendation
      );
      nameElement.parentElement.appendChild(badge);
      
      // Also show the full overlay card below
      showScoreOverlay(response.data, response.fromCache);
    }
    
  } catch (error) {
    console.error('Profile analysis failed:', error);
  }
}

/**
 * Fallback: Show overlay card only (when inline badge can't be placed)
 */
async function analyzeProfileFallback(profileId) {
  try {
    showLoadingOverlay();
    
    const profileData = extractProfileData();
    const features = calculateFeatures(profileData);
    
    const response = await chrome.runtime.sendMessage({
      action: 'calculateCompatibility',
      data: { profileId, ...features }
    });
    
    if (response.error) {
      showErrorOverlay(response.error);
      return;
    }
    
    if (response.success && response.data) {
      showScoreOverlay(response.data, response.fromCache);
    }
  } catch (error) {
    console.error('Profile analysis failed:', error);
    showErrorOverlay(error.message);
  }
}

/**
 * Create an inline score badge
 */
function createInlineScoreBadge(text, scoreClass, tooltip = '') {
  const badge = document.createElement('span');
  badge.className = `linkedin-match-inline-score ${scoreClass}`;
  badge.textContent = text;
  
  if (tooltip) {
    badge.title = tooltip;
  }
  
  return badge;
}

/**
 * Display compatibility score overlay
 */
function showScoreOverlay(compatibilityData, fromCache = false) {
  removeScoreOverlay();
  
  const score = compatibilityData.compatibility_score;
  const recommendation = compatibilityData.recommendation;
  const explanation = compatibilityData.explanation;
  
  const overlay = document.createElement('div');
  overlay.id = 'linkedin-match-overlay';
  overlay.className = 'linkedin-match-card';
  
  const scoreClass = getScoreClass(score);
  
  overlay.innerHTML = `
    <div class="match-header">
      <div class="match-icon">🤝</div>
      <div class="match-title">Compatibility Score</div>
      ${fromCache ? '<span class="cache-badge" title="From cache">📌</span>' : ''}
    </div>
    
    <div class="match-score ${scoreClass}">
      <div class="score-value">${score.toFixed(1)}</div>
      <div class="score-max">/100</div>
    </div>
    
    <div class="match-recommendation ${scoreClass}">
      ${recommendation}
    </div>
    
    <div class="match-explanation">
      ${explanation}
    </div>
    
    <div class="match-actions">
      <button class="match-btn" id="refresh-score" title="Recalculate">🔄</button>
      <button class="match-btn" id="export-score" title="Export data">📊</button>
      <button class="match-btn" id="close-overlay" title="Close">✕</button>
    </div>
  `;
  
  // Insert after profile card
  const profileCard = document.querySelector('.pv-top-card');
  if (profileCard) {
    profileCard.parentNode.insertBefore(overlay, profileCard.nextSibling);
    
    // Add event listeners
    document.getElementById('refresh-score')?.addEventListener('click', () => {
      analyzeProfile(currentProfileId);
    });
    
    document.getElementById('export-score')?.addEventListener('click', () => {
      exportScore(compatibilityData);
    });
    
    document.getElementById('close-overlay')?.addEventListener('click', () => {
      removeScoreOverlay();
    });
  }
}

function showLoadingOverlay() {
  removeScoreOverlay();
  
  const overlay = document.createElement('div');
  overlay.id = 'linkedin-match-overlay';
  overlay.className = 'linkedin-match-card loading';
  overlay.innerHTML = `
    <div class="match-header">
      <div class="match-icon">🤝</div>
      <div class="match-title">Analyzing Profile...</div>
    </div>
    <div class="loading-spinner"></div>
  `;
  
  const profileCard = document.querySelector('.pv-top-card');
  if (profileCard) {
    profileCard.parentNode.insertBefore(overlay, profileCard.nextSibling);
  }
}

function showErrorOverlay(message) {
  removeScoreOverlay();
  
  const overlay = document.createElement('div');
  overlay.id = 'linkedin-match-overlay';
  overlay.className = 'linkedin-match-card error';
  overlay.innerHTML = `
    <div class="match-header">
      <div class="match-icon">⚠️</div>
      <div class="match-title">Analysis Failed</div>
    </div>
    <div class="error-message">${message}</div>
    <button class="match-btn" id="close-overlay">Close</button>
  `;
  
  const profileCard = document.querySelector('.pv-top-card');
  if (profileCard) {
    profileCard.parentNode.insertBefore(overlay, profileCard.nextSibling);
    document.getElementById('close-overlay')?.addEventListener('click', removeScoreOverlay);
  }
}

function removeScoreOverlay() {
  const existing = document.getElementById('linkedin-match-overlay');
  if (existing) {
    existing.remove();
  }
}

function getScoreClass(score) {
  if (score >= 80) return 'score-excellent';
  if (score >= 60) return 'score-good';
  if (score >= 40) return 'score-moderate';
  return 'score-low';
}

function exportScore(data) {
  const exportData = {
    profileId: currentProfileId,
    url: window.location.href,
    timestamp: new Date().toISOString(),
    ...data
  };
  
  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `linkedin-match-${currentProfileId}-${Date.now()}.json`;
  a.click();
}

/**
 * Helper functions
 */
async function getSettings() {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage({ action: 'getSettings' }, resolve);
  });
}
