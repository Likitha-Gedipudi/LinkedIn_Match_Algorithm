/**
 * Content Script - Injected into LinkedIn pages
 * Extracts profile data and displays compatibility scores
 */

let currentProfileId = null;
let settings = {};

// Console helper for debugging
window.linkedInMatchDebug = function () {
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
 * Now uses stored user profile for accurate comparisons
 */
async function calculateFeatures(profileData) {
  // Get stored user profile for comparison
  const userProfile = await getUserProfile();

  // Show notification if user profile not initialized
  if (!userProfile.initialized) {
    console.warn('⚠️ User profile not set. Using default values. Go to extension options to set your profile.');
  }

  const connectionCount = profileData.connections || 100;
  const experienceYears = estimateExperienceYears(profileData.experience || []);

  // Extract additional profile attributes
  const industry = extractIndustry(profileData);
  const location = extractLocation(profileData);
  const seniority = estimateSeniority(experienceYears);

  // Base features (9 features) - now using real calculations
  const skill_match_score = calculateSkillMatch(profileData.skills || [], userProfile.skills || []);
  const skill_complementarity_score = calculateSkillComplementarity(
    profileData.skills || [],
    userProfile.skills || [],
    profileData.headline || '',  // Pass job title/headline for relevance matching
    userProfile.headline || ''
  );
  const network_value_a_to_b = Math.min((connectionCount / 50) * 100, 100);
  const network_value_b_to_a = Math.min((userProfile.connections / 50) * 100, 100);
  const career_alignment_score = calculateCareerAlignment(experienceYears, userProfile.experienceYears || 5);
  const experience_gap = Math.abs(experienceYears - (userProfile.experienceYears || 5));
  const industry_match = calculateIndustryMatch(industry, userProfile.industry || 'Other');
  const geographic_score = calculateGeographicScore(location, userProfile.location || 'Unknown');
  const seniority_match = calculateSeniorityMatch(seniority, userProfile.seniority || 'mid');

  // Derived features (9 features)
  const network_value_avg = (network_value_a_to_b + network_value_b_to_a) / 2;
  const network_value_diff = Math.abs(network_value_a_to_b - network_value_b_to_a);
  const skill_total = skill_match_score + skill_complementarity_score;
  const skill_balance = (skill_match_score * skill_complementarity_score) / 100;
  const exp_gap_squared = experience_gap * experience_gap;
  const is_mentorship_gap = (experience_gap >= 3 && experience_gap <= 7) ? 1 : 0;
  const is_peer = (experience_gap <= 2) ? 1 : 0;
  const skill_x_network = (skill_complementarity_score * network_value_avg) / 100;
  const career_x_industry = (career_alignment_score * industry_match) / 100;

  return {
    skill_match_score,
    skill_complementarity_score,
    network_value_a_to_b,
    network_value_b_to_a,
    career_alignment_score,
    experience_gap,
    industry_match,
    geographic_score,
    seniority_match,
    network_value_avg,
    network_value_diff,
    skill_total,
    skill_balance,
    exp_gap_squared,
    is_mentorship_gap,
    is_peer,
    skill_x_network,
    career_x_industry
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
    const features = await calculateFeatures({
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
        fromCache: response.fromCache,
        features: features  // Include features for detailed breakdown
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
    console.log('🔍 ========== PROFILE ANALYSIS START ==========');
    console.log('📍 Profile ID:', profileId);
    console.log('🌐 URL:', window.location.href);

    // Find the More button (3-dot menu)
    const moreButton = document.querySelector(
      'button[aria-label*="More actions"], ' +
      'button[aria-label*="More"], ' +
      '.artdeco-dropdown__trigger[aria-label*="More"]'
    );

    if (!moreButton) {
      console.log('⚠️ Could not find More button on profile page');
      return;
    }

    console.log('✅ Found More button:', moreButton);

    // Remove any existing badge
    const existingBadges = document.querySelectorAll('.linkedin-match-profile-badge');
    existingBadges.forEach(badge => badge.remove());

    // Create badge container to appear next to More button
    const badgeContainer = document.createElement('div');
    badgeContainer.className = 'linkedin-match-profile-badge';
    badgeContainer.style.cssText = `
      display: inline-flex;
      align-items: center;
      margin-left: 8px;
      vertical-align: middle;
    `;

    // Insert badge AFTER the More button
    moreButton.parentNode.insertBefore(badgeContainer, moreButton.nextSibling);

    // Show loading badge
    const loadingBadge = createInlineScoreBadge('Analyzing...', 'loading');
    badgeContainer.appendChild(loadingBadge);

    console.log('⏳ Extracting profile data...');

    // Extract profile data
    const profileData = extractProfileData();
    console.log('📊 Extracted Target Profile Data:', {
      profileId: profileData.profileId,
      name: profileData.name,
      headline: profileData.headline,
      location: profileData.location,
      connections: profileData.connections,
      skillCount: profileData.skills?.length || 0,
      skills: profileData.skills,
      experienceCount: profileData.experience?.length || 0,
      educationCount: profileData.education?.length || 0
    });

    console.log('⚙️ Calculating features...');
    const features = await calculateFeatures(profileData);

    console.log('📈 Calculated Features:', features);

    // Get user profile for comparison logging
    const userProfile = await getUserProfile();
    console.log('👤 Your Profile Data:', {
      name: userProfile.name,
      headline: userProfile.headline,
      skillCount: userProfile.skills?.length || 0,
      skills: userProfile.skills,
      experienceYears: userProfile.experienceYears,
      connections: userProfile.connections,
      industry: userProfile.industry,
      seniority: userProfile.seniority,
      location: userProfile.location,
      initialized: userProfile.initialized
    });

    console.log('🔄 Sending API request to calculate compatibility...');
    console.log('📤 API Request Data:', { profileId, features });

    // Request compatibility calculation with error handling
    let response;
    const apiStartTime = Date.now();

    try {
      response = await chrome.runtime.sendMessage({
        action: 'calculateCompatibility',
        data: {
          profileId,
          userProfile: userProfile,      // NEW: Full user profile for Groq
          targetProfile: profileData,     // NEW: Full target profile for Groq
          ...features                     // KEEP: Features for Model API fallback
        }
      });

      const apiDuration = Date.now() - apiStartTime;
      console.log(`✅ API Response received (${apiDuration}ms):`, response);

      if (response.fromCache) {
        console.log('📌 Result from cache');
      } else {
        console.log('🌐 Fresh API call');
      }

    } catch (err) {
      console.error('❌ API call failed:', err);
      // Extension context invalidated - remove badge and stop
      console.log('Extension context invalidated. Please reload the page.');
      badgeContainer.remove();
      return;
    }

    // Remove loading badge
    loadingBadge.remove();

    if (!response || response.error) {
      console.error('❌ API returned error:', response?.error);
      const errorBadge = createInlineScoreBadge('Error', 'error');
      badgeContainer.appendChild(errorBadge);
      return;
    }

    if (response.success && response.data) {
      const score = response.data.compatibility_score;

      console.log('🎯 COMPATIBILITY RESULT:');
      console.log('  Score:', score);
      console.log('  Recommendation:', response.data.recommendation);
      console.log('  Explanation:', response.data.explanation);

      const matchData = {
        profileId,
        profileName: document.querySelector('h1')?.textContent.trim() || 'Profile',
        headline: document.querySelector('.text-body-medium')?.textContent.trim() || '',
        score,
        recommendation: response.data.recommendation,
        explanation: response.data.explanation,
        fromCache: response.fromCache,
        features: features,  // Include features for detailed breakdown
        // Add comparison data for UI
        targetProfile: {
          name: profileData.name,
          headline: profileData.headline,
          skills: profileData.skills || [],
          experience: profileData.experience || [],
          connections: profileData.connections,
          location: profileData.location
        },
        userProfile: {
          name: userProfile.name,
          headline: userProfile.headline,
          skills: userProfile.skills || [],
          experienceYears: userProfile.experienceYears,
          connections: userProfile.connections,
          location: userProfile.location,
          industry: userProfile.industry,
          seniority: userProfile.seniority
        }
      };

      console.log('✅ ========== PROFILE ANALYSIS COMPLETE ==========\n');

      // Create clickable badge
      const badge = createClickableScoreBadge(matchData);
      badgeContainer.appendChild(badge);
    }
  } catch (error) {
    // Silently handle errors - don't show to user
    if (error.message && !error.message.includes('Extension context invalidated')) {
      console.error('❌ Profile analysis failed:', error);
      console.error('Stack trace:', error.stack);
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
 * Show match details modal with detailed reasoning
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

  // Generate detailed factor breakdown HTML
  const factorsHTML = generateFactorBreakdown(matchData);

  // Generate profile comparison HTML
  const comparisonHTML = generateProfileComparison(matchData);

  modal.innerHTML = `
    <div class="linkedin-match-modal-content">
      <button class="linkedin-match-modal-close" aria-label="Close">✕</button>
      
      <div class="linkedin-match-modal-header">
        <h2>${scoreEmoji} Compatibility Analysis</h2>
        <div class="linkedin-match-modal-subtitle">
          <div class="linkedin-match-modal-title">${matchData.profileName}</div>
          ${matchData.headline ? `<div class="linkedin-match-modal-subtitle">${matchData.headline}</div>` : ''}
        </div>
      </div>
      
      <div class="linkedin-match-modal-body">
        <div class="linkedin-match-score-circle ${scoreClass}">
          <div class="linkedin-match-score-value">${matchData.score.toFixed(1)}</div>
          <div class="linkedin-match-score-max">/ 100</div>
        </div>
        <div class="linkedin-match-recommendation ${scoreClass}">
          ${matchData.recommendation}
        </div>
      </div>
      
      <div class="linkedin-match-modal-body">
        <h3>🔍 Profile Comparison</h3>
        <div class="linkedin-match-comparison">
          ${comparisonHTML}
        </div>
      </div>
      
      <div class="linkedin-match-modal-body">
        <h3>🎯 Score Breakdown & Reasoning</h3>
        <div class="linkedin-match-explanation">
          ${factorsHTML}
        </div>
      </div>
      
      <div class="linkedin-match-modal-body" style="margin-top: 16px;">
        <h3>📋 Summary</h3>
        <div class="linkedin-match-explanation">
          ${matchData.explanation.split(' | ').map(factor => `
            <div class="linkedin-match-explanation-item">
              <span class="linkedin-match-explanation-icon">•</span>
              <span class="linkedin-match-explanation-text">${factor}</span>
            </div>
          `).join('')}
        </div>
      </div>
      
      <div class="linkedin-match-modal-footer">
        <button class="modal-btn linkedin-match-btn-secondary" id="modal-export">📊 Export Data</button>
        <button class="modal-btn linkedin-match-btn-primary" id="modal-view-profile">👤 View Profile</button>
      </div>
      
      ${matchData.fromCache ? '<div class="linkedin-match-cache-badge">📌 From cache</div>' : ''}
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
 * Generate profile comparison HTML
 */
function generateProfileComparison(matchData) {
  const target = matchData.targetProfile || {};
  const user = matchData.userProfile || {};

  return `
    <table class="linkedin-match-comparison-table">
      <thead>
        <tr>
          <th></th>
          <th>👤 You</th>
          <th>🎯 ${matchData.profileName}</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td class="linkedin-match-comparison-label">Name</td>
          <td>${user.name || '-'}</td>
          <td>${target.name || '-'}</td>
        </tr>
        
        <tr>
          <td class="linkedin-match-comparison-label">Headline</td>
          <td>${user.headline || '-'}</td>
          <td>${target.headline || '-'}</td>
        </tr>
        
        <tr>
          <td class="linkedin-match-comparison-label">Skills</td>
          <td>
            <div class="skill-pills">
              ${(user.skills || []).slice(0, 5).map(skill => `<span class="skill-pill">${skill}</span>`).join('')}
              ${(user.skills?.length || 0) > 5 ? `<span class="skill-more">+${user.skills.length - 5} more</span>` : ''}
            </div>
          </td>
          <td>
            <div class="skill-pills">
              ${(target.skills || []).slice(0, 5).map(skill => `<span class="skill-pill">${skill}</span>`).join('')}
              ${(target.skills?.length || 0) > 5 ? `<span class="skill-more">+${target.skills.length - 5} more</span>` : ''}
            </div>
          </td>
        </tr>
        
        <tr>
          <td class="linkedin-match-comparison-label">Experience</td>
          <td>${user.experienceYears || '-'} years</td>
          <td>${target.experience?.length || '-'} positions</td>
        </tr>
        
        <tr>
          <td class="linkedin-match-comparison-label">Connections</td>
          <td>${user.connections || '-'}</td>
          <td>${target.connections || '-'}</td>
        </tr>
        
        <tr>
          <td class="linkedin-match-comparison-label">Location</td>
          <td>${user.location || '-'}</td>
          <td>${target.location || '-'}</td>
        </tr>
        
        <tr>
          <td class="linkedin-match-comparison-label">Industry</td>
          <td>${user.industry || '-'}</td>
          <td>-</td>
        </tr>
        
        <tr>
          <td class="linkedin-match-comparison-label">Seniority</td>
          <td>${user.seniority || '-'}</td>
          <td>-</td>
        </tr>
      </tbody>
    </table>
  `;
}

/**
 * Generate detailed factor breakdown HTML
 */
function generateFactorBreakdown(matchData) {
  // Extract features if available
  const features = matchData.features || {};

  // Define factor categories with their components
  const factorCategories = [
    {
      icon: '🤝',
      name: 'Skills Compatibility',
      factors: [
        {
          label: 'Skill Overlap',
          value: features.skill_match_score || 50,
          description: 'How many skills you have in common'
        },
        {
          label: 'Complementary Skills',
          value: features.skill_complementarity_score || 40,
          description: 'Unique skills that complement each other'
        }
      ]
    },
    {
      icon: '💼',
      name: 'Professional Alignment',
      factors: [
        {
          label: 'Career Stage Match',
          value: features.career_alignment_score || 60,
          description: 'Alignment in career trajectory and goals'
        },
        {
          label: 'Industry Match',
          value: features.industry_match || 50,
          description: 'Work in same or related industries'
        },
        {
          label: 'Seniority Alignment',
          value: features.seniority_match || 70,
          description: 'Similar or complementary experience levels'
        }
      ]
    },
    {
      icon: '🌐',
      name: 'Network Value',
      factors: [
        {
          label: 'Network Strength',
          value: features.network_value_avg || 60,
          description: 'Combined networking potential'
        },
        {
          label: 'Geographic Proximity',
          value: features.geographic_score || 50,
          description: 'Location-based networking opportunities'
        }
      ]
    }
  ];

  // Generate HTML for each category
  return factorCategories.map(category => `
    <div class="factor-category">
      <div class="factor-category-header">
        <span class="factor-category-icon">${category.icon}</span>
        <span class="factor-category-name">${category.name}</span>
      </div>
      ${category.factors.map(factor => `
        <div class="factor-item">
          <div class="factor-item-header">
            <span class="factor-label">${factor.label}</span>
            <span class="factor-score ${getScoreClass(factor.value)}">${Math.round(factor.value)}%</span>
          </div>
          <div class="factor-progress-bar">
            <div class="factor-progress-fill ${getScoreClass(factor.value)}" style="width: ${factor.value}%"></div>
          </div>
          <div class="factor-description">${factor.description}</div>
        </div>
      `).join('')}
    </div>
  `).join('');
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

/**
 * Message listener for profile extraction requests from options page
 */
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'extractMyProfile') {
    handleProfileExtraction(sendResponse);
    return true; // Keep channel open for async response
  }
});

/**
 * Extract current profile and send back to options page
 */
async function handleProfileExtraction(sendResponse) {
  try {
    // Check if we're on a LinkedIn profile page
    const pathname = window.location.pathname;
    const isProfilePage = pathname.includes('/in/');

    if (!isProfilePage) {
      sendResponse({
        success: false,
        error: 'Please navigate to your LinkedIn profile page first. (URL should contain /in/your-name)'
      });
      return;
    }

    // Wait for profile content to load
    await waitForElement('.pv-top-card', 3000);

    // Extract profile data using existing functions
    const profileData = extractProfileData();

    // Validate extracted data
    if (!profileData.name) {
      sendResponse({
        success: false,
        error: 'Could not extract profile name. Please make sure you are on a LinkedIn profile page.'
      });
      return;
    }

    // Extract additional metadata
    const experienceYears = estimateExperienceYears(profileData.experience || []);
    const industry = extractIndustry(profileData);
    const location = extractLocation(profileData);
    const seniority = estimateSeniority(experienceYears);

    // Build complete profile
    const completeProfile = {
      name: profileData.name,
      skills: profileData.skills || [],
      experienceYears: experienceYears,
      connections: profileData.connections || 0,
      industry: industry,
      seniority: seniority,
      location: location,
      headline: profileData.headline || ''
    };

    sendResponse({
      success: true,
      profile: completeProfile
    });

  } catch (error) {
    console.error('Profile extraction error:', error);
    sendResponse({
      success: false,
      error: 'Failed to extract profile data: ' + error.message
    });
  }
}
