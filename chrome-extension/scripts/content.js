/**
 * Content Script - Injected into LinkedIn pages
 * Extracts profile data and displays compatibility scores
 */

let currentProfileId = null;
let settings = {};

// Console helper for debugging
window.linkedInMatchDebug = function() {
  console.log('🔍 LinkedIn Match AI Debug');
  console.log('\n1️⃣ Looking for profile name elements...');
  
  const selectors = [
    '.pv-text-details__left-panel h1',
    '.text-heading-xlarge',
    'h1.inline',
    'main h1',
    '.ph5 h1',
    'h1'
  ];
  
  selectors.forEach(sel => {
    const el = document.querySelector(sel);
    console.log(`${sel}:`, el ? `✅ "${el.textContent.trim().substring(0, 50)}"` : '❌');
  });
  
  console.log('\n2️⃣ All h1 elements on page:');
  document.querySelectorAll('h1').forEach((h1, i) => {
    console.log(`  ${i + 1}. "${h1.textContent.trim().substring(0, 50)}"`);
  });
  
  console.log('\n3️⃣ Current URL:', window.location.pathname);
  console.log('\n💡 Run this anytime to debug selector issues!');
};

// Initialize
(async function init() {
  console.log('LinkedIn Match AI: Content script loaded');
  console.log('💡 Type linkedInMatchDebug() in console to debug selector issues');
  
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
  // Find all profile cards - including invitation cards
  const cards = document.querySelectorAll(
    '[data-control-name="invite_card"], ' +
    '.mn-connection-card, ' +
    '.discover-person-card, ' +
    '.reusable-search__result-container, ' +
    '.invitation-card, ' +
    'li.mn-invitation-list__card'
  );
  
  console.log(`Found ${cards.length} profile cards`);
  
  // Process in batches for better performance
  const batchSize = 5;
  for (let i = 0; i < cards.length; i += batchSize) {
    const batch = Array.from(cards).slice(i, i + batchSize);
    
    await Promise.all(batch.map(async (card) => {
      // Skip if already processed
      if (card.querySelector('.linkedin-match-inline-score')) {
        return;
      }
      
      // Extract profile info - try multiple selectors for invitation cards
      const nameElement = card.querySelector(
        '.mn-connection-card__name, ' +
        '.discover-person-card__name, ' +
        '.entity-result__title-text a, ' +
        'a.app-aware-link span[aria-hidden="true"], ' +
        '[data-control-name="actor_container"] span[dir="ltr"] span[aria-hidden="true"], ' +
        '.invitation-card__title'
      );
      
      const linkElement = card.querySelector('a[href*="/in/"]');
      
      if (!nameElement || !linkElement) return;
      
      // Extract profile ID from link
      const match = linkElement.href.match(/\/in\/([^/?]+)/);
      if (!match) return;
      
      const profileId = match[1];
      const profileName = nameElement.textContent.trim();
      
      // Extract additional info for better matching
      const headlineElement = card.querySelector('.invitation-card__subtitle, [data-control-name="subtitle"]');
      const headline = headlineElement ? headlineElement.textContent.trim() : '';
      
      // Calculate and inject score
      await injectInlineScoreForCard(card, profileId, profileName, nameElement, headline);
    }));
    
    // Small delay between batches
    if (i + batchSize < cards.length) {
      await new Promise(resolve => setTimeout(resolve, 500));
    }
  }
}

/**
 * Inject inline score for a single card
 */
async function injectInlineScoreForCard(card, profileId, profileName, nameElement, headline = '') {
  try {
    // Remove any existing badges
    const oldBadges = card.querySelectorAll('.linkedin-match-badge-container, .linkedin-match-inline-score');
    oldBadges.forEach(badge => badge.remove());
    
    // Find the button container (Accept/Ignore buttons)
    const buttonContainer = card.querySelector(
      '.invitation-card__action-container, ' +
      '[data-control-name="invite_card_actions"], ' +
      '.mn-connection-card__action-container, ' +
      'footer'
    );
    
    // Create badge container
    const badgeContainer = document.createElement('div');
    badgeContainer.className = 'linkedin-match-badge-container';
    
    // Insert BEFORE the button container
    if (buttonContainer) {
      buttonContainer.parentNode.insertBefore(badgeContainer, buttonContainer);
    } else {
      // Fallback: append to card
      card.appendChild(badgeContainer);
    }
    
    // Show loading badge
    const loadingBadge = createInlineScoreBadge('...', 'loading');
    badgeContainer.appendChild(loadingBadge);
    
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
      const matchData = {
        profileId,
        profileName,
        headline,
        score,
        recommendation: response.data.recommendation,
        explanation: response.data.explanation,
        fromCache: response.fromCache
      };
      
      // Create clickable badge in the container
      const badge = createClickableScoreBadge(matchData);
      badgeContainer.appendChild(badge);
    }
  } catch (error) {
    console.error('Error calculating score for card:', error);
  }
}

/**
 * Analyze profile page - inject badge above Message button
 */
async function analyzeProfileInline(profileId) {
  try {
    // Find the action container (Message/More buttons area)
    // Try multiple strategies to find the button container
    let actionContainer = null;
    
    // Strategy 1: Find parent of Message button
    const messageButton = document.querySelector('button[aria-label*="Message"]');
    if (messageButton) {
      // Go up to find the container with all action buttons
      actionContainer = messageButton.parentElement?.parentElement;
    }
    
    // Strategy 2: Find parent of Follow/Connect button
    if (!actionContainer) {
      const followButton = document.querySelector('button[aria-label*="Follow"], button[aria-label*="Connect"]');
      if (followButton) {
        actionContainer = followButton.parentElement;
      }
    }
    
    if (!actionContainer) {
      console.log('⚠️ Could not find action container on profile page');
      return;
    }
    
    console.log('✅ Found action container:', actionContainer);
    
    // Remove any existing badge
    const existingBadges = document.querySelectorAll('.linkedin-match-profile-badge');
    existingBadges.forEach(badge => badge.remove());
    
    // Create dedicated badge container above action buttons
    const badgeContainer = document.createElement('div');
    badgeContainer.className = 'linkedin-match-profile-badge';
    badgeContainer.style.cssText = `
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 12px 0;
      margin-bottom: 12px;
      z-index: 10;
    `;
    
    // Insert BEFORE action buttons
    actionContainer.parentNode.insertBefore(badgeContainer, actionContainer);
    
    // Show loading badge
    const loadingBadge = createInlineScoreBadge('Analyzing...', 'loading');
    badgeContainer.appendChild(loadingBadge);
    
    // Extract profile data
    const profileData = extractProfileData();
    const features = calculateFeatures(profileData);
    
    // Request compatibility calculation with error handling
    let response;
    try {
      response = await chrome.runtime.sendMessage({
        action: 'calculateCompatibility',
        data: { profileId, ...features }
      });
    } catch (err) {
      // Extension context invalidated - remove badge and stop
      console.log('Extension context invalidated. Please reload the page.');
      badgeContainer.remove();
      return;
    }
    
    // Remove loading badge
    loadingBadge.remove();
    
    if (!response || response.error) {
      const errorBadge = createInlineScoreBadge('Error', 'error');
      badgeContainer.appendChild(errorBadge);
      return;
    }
    
    if (response.success && response.data) {
      const score = response.data.compatibility_score;
      const matchData = {
        profileId,
        profileName: document.querySelector('h1')?.textContent.trim() || 'Profile',
        headline: document.querySelector('.text-body-medium')?.textContent.trim() || '',
        score,
        recommendation: response.data.recommendation,
        explanation: response.data.explanation,
        fromCache: response.fromCache
      };
      
      // Create clickable badge
      const badge = createClickableScoreBadge(matchData);
      badgeContainer.appendChild(badge);
    }
  } catch (error) {
    // Silently handle errors - don't show to user
    if (error.message && !error.message.includes('Extension context invalidated')) {
      console.error('Profile analysis failed:', error);
    }
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
 * Create a clickable inline score badge that opens a modal
 */
function createClickableScoreBadge(matchData) {
  const badge = document.createElement('div');
  const scoreClass = getScoreClass(matchData.score);
  badge.className = `linkedin-match-inline-score ${scoreClass} clickable`;
  badge.textContent = `${matchData.score.toFixed(0)} Match`;
  badge.title = 'Click for details';
  badge.style.cursor = 'pointer';
  
  // Store match data
  badge.dataset.matchData = JSON.stringify(matchData);
  
  // Add multiple event handlers to stop propagation
  const handleClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    e.stopImmediatePropagation();
    showMatchModal(matchData);
    return false;
  };
  
  badge.addEventListener('click', handleClick, true); // Capture phase
  badge.addEventListener('mousedown', (e) => {
    e.stopPropagation();
    e.stopImmediatePropagation();
  }, true);
  badge.addEventListener('mouseup', (e) => {
    e.stopPropagation();
    e.stopImmediatePropagation();
  }, true);
  
  return badge;
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
 * Show match details modal
 */
function showMatchModal(matchData) {
  // Remove any existing modal
  const existingModal = document.getElementById('linkedin-match-modal');
  if (existingModal) {
    existingModal.remove();
  }
  
  // Create modal overlay
  const modal = document.createElement('div');
  modal.id = 'linkedin-match-modal';
  modal.className = 'linkedin-match-modal-overlay';
  
  const scoreClass = getScoreClass(matchData.score);
  const scoreEmoji = matchData.score >= 80 ? '🎯' : matchData.score >= 60 ? '✅' : matchData.score >= 40 ? '⚠️' : '❌';
  
  modal.innerHTML = `
    <div class="linkedin-match-modal-content">
      <button class="linkedin-match-modal-close" aria-label="Close">✕</button>
      
      <div class="modal-header">
        <h2>${scoreEmoji} Compatibility Analysis</h2>
        <div class="modal-profile-info">
          <div class="modal-profile-name">${matchData.profileName}</div>
          ${matchData.headline ? `<div class="modal-profile-headline">${matchData.headline}</div>` : ''}
        </div>
      </div>
      
      <div class="modal-score-section">
        <div class="modal-score-circle ${scoreClass}">
          <div class="modal-score-value">${matchData.score.toFixed(1)}</div>
          <div class="modal-score-label">/ 100</div>
        </div>
        <div class="modal-recommendation ${scoreClass}">
          ${matchData.recommendation}
        </div>
      </div>
      
      <div class="modal-details-section">
        <h3>Match Factors</h3>
        <div class="modal-explanation">
          ${matchData.explanation.split(' | ').map(factor => `
            <div class="modal-factor">
              <span class="factor-icon">•</span>
              <span class="factor-text">${factor}</span>
            </div>
          `).join('')}
        </div>
      </div>
      
      <div class="modal-actions">
        <button class="modal-btn modal-btn-secondary" id="modal-export">📊 Export Data</button>
        <button class="modal-btn modal-btn-primary" id="modal-view-profile">👤 View Profile</button>
      </div>
      
      ${matchData.fromCache ? '<div class="modal-cache-badge">📌 From cache</div>' : ''}
    </div>
  `;
  
  document.body.appendChild(modal);
  
  // Add event listeners
  modal.querySelector('.linkedin-match-modal-close').addEventListener('click', () => modal.remove());
  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.remove();
  });
  
  modal.querySelector('#modal-export').addEventListener('click', () => {
    exportMatchData(matchData);
  });
  
  modal.querySelector('#modal-view-profile').addEventListener('click', () => {
    window.open(`https://www.linkedin.com/in/${matchData.profileId}/`, '_blank');
    modal.remove();
  });
  
  // Animate in
  setTimeout(() => modal.classList.add('show'), 10);
}

/**
 * Export match data as JSON
 */
function exportMatchData(matchData) {
  const exportData = {
    ...matchData,
    timestamp: new Date().toISOString(),
    url: window.location.href
  };
  
  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `linkedin-match-${matchData.profileId}-${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
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
