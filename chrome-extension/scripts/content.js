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
 * Extract profile data from LinkedIn page - ENHANCED VERSION
 * Now extracts: About, Experience (with descriptions), Projects, Posts, Interests
 */
function extractProfileData() {
  console.log('🔍 Starting ENHANCED profile extraction...');

  const data = {
    profileId: currentProfileId,
    name: extractText('.pv-text-details__left-panel h1, .text-heading-xlarge, h1'),
    headline: extractText('.pv-text-details__left-panel .text-body-medium, .text-body-medium'),
    location: extractText('.pv-text-details__left-panel .text-body-small, .text-body-small'),
    connections: extractConnectionCount(),

    // ENHANCED: Full About section
    about: extractAboutSection(),

    // ENHANCED: Experience with descriptions
    experience: extractExperienceEnhanced(),

    // Skills
    skills: extractSkills(),

    // Education
    education: extractEducation(),

    // ENHANCED: Projects section
    projects: extractProjects(),

    // ENHANCED: Recent posts/activity
    posts: extractRecentPosts(),

    // ENHANCED: Interests (followed topics)
    interests: extractInterests(),

    // ENHANCED: Featured section
    featured: extractFeatured()
  };

  console.log('✅ ENHANCED profile data extracted:', {
    name: data.name,
    headline: data.headline,
    aboutLength: data.about?.length || 0,
    experienceCount: data.experience?.length || 0,
    skillCount: data.skills?.length || 0,
    projectCount: data.projects?.length || 0,
    postCount: data.posts?.length || 0,
    interestCount: data.interests?.length || 0
  });

  return data;
}

function extractText(selector) {
  const el = document.querySelector(selector);
  return el ? el.textContent.trim() : '';
}

function extractConnectionCount() {
  // Try multiple selectors for connection count
  const selectors = [
    '.pv-top-card--list li span.t-bold',
    'a[href*="connections"] span.t-bold',
    '.pv-top-card--list-bullet li:first-child span'
  ];

  for (const selector of selectors) {
    const el = document.querySelector(selector);
    if (el) {
      const text = el.textContent.trim();
      const match = text.match(/(\d+[\+,]*\d*)/);
      if (match) {
        return parseInt(match[1].replace(/[+,]/g, '')) || 0;
      }
    }
  }

  // Fallback: search in list items
  const text = extractText('.pv-top-card--list li');
  const match = text.match(/(\d+[\+]?)\s*connections?/i);
  return match ? parseInt(match[1].replace('+', '')) : 0;
}

/**
 * ENHANCED: Extract About section with full text
 */
function extractAboutSection() {
  const aboutSelectors = [
    '#about ~ div .inline-show-more-text span[aria-hidden="true"]',
    '#about ~ div .pv-shared-text-with-see-more span[aria-hidden="true"]',
    '#about + div + div span[aria-hidden="true"]',
    'section.pv-about-section div.inline-show-more-text',
    '.pv-shared-text-with-see-more .visually-hidden',
    '#about ~ div .full-width span'
  ];

  for (const selector of aboutSelectors) {
    const el = document.querySelector(selector);
    if (el && el.textContent.trim().length > 20) {
      console.log('📝 Found About section with selector:', selector);
      return el.textContent.trim();
    }
  }

  // Fallback: try to find any text container after #about
  const aboutSection = document.querySelector('#about');
  if (aboutSection) {
    const container = aboutSection.closest('section');
    if (container) {
      const textEl = container.querySelector('.inline-show-more-text, .pv-shared-text-with-see-more');
      if (textEl) {
        return textEl.textContent.trim();
      }
    }
  }

  return '';
}

/**
 * ENHANCED: Extract experience with full descriptions
 */
function extractExperienceEnhanced() {
  const experiences = [];

  // Try multiple selector patterns for experience items
  const experienceSelectors = [
    '#experience ~ div li.artdeco-list__item',
    'section[id*="experience"] li.artdeco-list__item',
    '.experience-section li'
  ];

  let experienceItems = [];
  for (const selector of experienceSelectors) {
    experienceItems = document.querySelectorAll(selector);
    if (experienceItems.length > 0) break;
  }

  experienceItems.forEach(el => {
    const title = el.querySelector('.mr1.t-bold span, .t-bold span[aria-hidden="true"]')?.textContent.trim();
    const company = el.querySelector('.t-14.t-normal span, .pv-entity__secondary-title')?.textContent.trim();
    const duration = el.querySelector('.t-14.t-normal.t-black--light span, .pv-entity__date-range span:nth-child(2)')?.textContent.trim();

    // ENHANCED: Get experience description
    const descriptionEl = el.querySelector('.inline-show-more-text span[aria-hidden="true"], .pv-shared-text-with-see-more span');
    const description = descriptionEl ? descriptionEl.textContent.trim() : '';

    // ENHANCED: Get location
    const locationEl = el.querySelector('.t-14.t-normal.t-black--light span:last-child');
    const location = locationEl ? locationEl.textContent.trim() : '';

    if (title) {
      experiences.push({
        title,
        company,
        duration,
        description,
        location
      });
    }
  });

  console.log(`📋 Extracted ${experiences.length} experience entries`);
  return experiences;
}

function extractSkills() {
  const skills = [];

  // Try multiple selectors for skills
  const skillSelectors = [
    '[data-field="skill_card_skill_topic"] .mr1.t-bold span',
    '#skills ~ div .mr1.hoverable-link-text span[aria-hidden="true"]',
    'section[data-section="skills"] .skill-categories-card span',
    '.pv-skill-categories-section li span'
  ];

  for (const selector of skillSelectors) {
    document.querySelectorAll(selector).forEach(el => {
      const skill = el.textContent.trim();
      if (skill && !skills.includes(skill)) {
        skills.push(skill);
      }
    });
    if (skills.length > 0) break;
  }

  console.log(`🎯 Extracted ${skills.length} skills`);
  return skills;
}

function extractEducation() {
  const education = [];

  const educationSelectors = [
    '#education ~ div li.artdeco-list__item',
    'section[id*="education"] li.artdeco-list__item'
  ];

  let educationItems = [];
  for (const selector of educationSelectors) {
    educationItems = document.querySelectorAll(selector);
    if (educationItems.length > 0) break;
  }

  educationItems.forEach(el => {
    const school = el.querySelector('.mr1.t-bold span, .pv-entity__school-name')?.textContent.trim();
    const degree = el.querySelector('.t-14.t-normal span, .pv-entity__degree-name span:nth-child(2)')?.textContent.trim();
    const field = el.querySelector('.pv-entity__fos span:nth-child(2)')?.textContent.trim();

    if (school) {
      education.push({ school, degree, field });
    }
  });

  return education;
}

/**
 * NEW: Extract projects section
 */
function extractProjects() {
  const projects = [];

  const projectSelectors = [
    '#projects ~ div li.artdeco-list__item',
    'section[id*="projects"] li.artdeco-list__item'
  ];

  let projectItems = [];
  for (const selector of projectSelectors) {
    projectItems = document.querySelectorAll(selector);
    if (projectItems.length > 0) break;
  }

  projectItems.forEach(el => {
    const name = el.querySelector('.mr1.t-bold span')?.textContent.trim();
    const descriptionEl = el.querySelector('.inline-show-more-text span[aria-hidden="true"], .pv-shared-text-with-see-more span');
    const description = descriptionEl ? descriptionEl.textContent.trim() : '';
    const dateRange = el.querySelector('.t-14.t-normal.t-black--light span')?.textContent.trim();

    if (name) {
      projects.push({ name, description, dateRange });
    }
  });

  console.log(`🚀 Extracted ${projects.length} projects`);
  return projects;
}

/**
 * NEW: Extract recent posts/activity
 */
function extractRecentPosts() {
  const posts = [];

  // Activity section selectors
  const postSelectors = [
    '.pv-recent-activity-section .feed-shared-update-v2',
    '[data-test-id="feed-share"] .feed-shared-text',
    '.profile-creator-shared-feed-update__mini-update'
  ];

  for (const selector of postSelectors) {
    document.querySelectorAll(selector).forEach(el => {
      const content = el.textContent.trim();
      if (content && content.length > 20) {
        posts.push({ content: content.substring(0, 500) });
      }
    });
    if (posts.length > 0) break;
  }

  // Also check for activity indicators
  const activitySection = document.querySelector('#content_collections, .pv-recent-activity-section');
  if (activitySection && posts.length === 0) {
    const activityText = activitySection.textContent.trim();
    if (activityText.length > 50) {
      posts.push({ content: activityText.substring(0, 500) });
    }
  }

  console.log(`📰 Extracted ${posts.length} recent posts`);
  return posts;
}

/**
 * NEW: Extract interests (followed topics, influencers)
 */
function extractInterests() {
  const interests = [];

  const interestSelectors = [
    '#interests ~ div .pv-entity__summary-title-text',
    '#interests ~ div .t-bold span',
    'section[id*="interests"] .pv-interest-entity-link span',
    '.pv-interests-section .pv-entity__summary-title'
  ];

  for (const selector of interestSelectors) {
    document.querySelectorAll(selector).forEach(el => {
      const interest = el.textContent.trim();
      if (interest && !interests.includes(interest)) {
        interests.push(interest);
      }
    });
    if (interests.length > 0) break;
  }

  console.log(`💡 Extracted ${interests.length} interests`);
  return interests;
}

/**
 * NEW: Extract featured section
 */
function extractFeatured() {
  const featured = [];

  const featuredSelectors = [
    '#featured ~ div li',
    'section[id*="featured"] li.artdeco-carousel__item'
  ];

  for (const selector of featuredSelectors) {
    document.querySelectorAll(selector).forEach(el => {
      const title = el.querySelector('.t-bold span, .pv-featured-item__title')?.textContent.trim();
      const description = el.querySelector('.t-normal span, .pv-featured-item__subtitle')?.textContent.trim();

      if (title) {
        featured.push({ title, description });
      }
    });
    if (featured.length > 0) break;
  }

  console.log(`⭐ Extracted ${featured.length} featured items`);
  return featured;
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

  // NEW: Role Family Affinity - bonus for related career fields
  const roleAffinity = calculateRoleFamilyAffinity(
    userProfile.headline || '',
    profileData.headline || ''
  );
  const role_family_bonus = roleAffinity.bonus || 0;
  const role_family_reason = roleAffinity.reason || null;

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
    career_x_industry,
    // NEW: Role family affinity
    role_family_bonus,
    role_family_reason
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
  // FIXED: More reliable way to find invitation cards
  // Look for Accept buttons and traverse up to find the card container
  const acceptButtons = document.querySelectorAll('button[aria-label*="Accept"]');

  console.log(`🔍 Found ${acceptButtons.length} Accept buttons on Network page`);

  // Get unique cards from Accept buttons
  const cards = [];
  const processedCards = new Set();

  acceptButtons.forEach(btn => {
    // Find the card container by traversing up
    let card = btn.closest('li') || btn.closest('div.artdeco-list__item') || btn.closest('[class*="invitation"]');
    if (!card) {
      // Try to find 3-4 levels up from button
      card = btn.parentElement?.parentElement?.parentElement?.parentElement;
    }

    if (card && !processedCards.has(card)) {
      processedCards.add(card);
      cards.push(card);
    }
  });

  console.log(`📋 Processing ${cards.length} unique invitation cards (with rate limit delays)`);

  // Process ONE AT A TIME with delays to avoid Groq API rate limits (429)
  for (let i = 0; i < cards.length; i++) {
    const card = cards[i];

    // Skip if already processed
    if (card.querySelector('.linkedin-match-badge-container')) {
      continue;
    }

    // Find profile link
    const linkElement = card.querySelector('a[href*="/in/"]');
    if (!linkElement) {
      console.log('⚠️ No profile link found in card');
      continue;
    }

    // Extract profile ID
    const match = linkElement.href.match(/\/in\/([^/?]+)/);
    if (!match) continue;

    const profileId = match[1];

    // Find name
    const nameElement = linkElement.querySelector('span[aria-hidden="true"]') ||
      linkElement.querySelector('span') ||
      card.querySelector('strong');
    const profileName = nameElement ? nameElement.textContent.trim().split('\n')[0] : 'Unknown';

    // Find headline
    const headlineElement = card.querySelector('[class*="subtitle"], [class*="occupation"], .text-body-small');
    const headline = headlineElement ? headlineElement.textContent.trim() : '';

    console.log(`📊 [${i + 1}/${cards.length}] Processing: ${profileName}`);

    // Calculate and inject score
    await injectInlineScoreForCard(card, profileId, profileName, nameElement, headline);

    // RATE LIMIT DELAY: Wait 2 seconds between each API call to avoid 429 errors
    if (i < cards.length - 1) {
      console.log(`⏳ Waiting 2s before next profile (rate limit protection)...`);
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }

  console.log(`✅ Finished processing ${cards.length} invitation cards`);
}


/**
 * Inject inline score for a single card - ENHANCED VERSION
 * Now extracts more data from card preview and sends to Groq
 */
async function injectInlineScoreForCard(card, profileId, profileName, nameElement, headline = '') {
  try {
    // Remove any existing badges
    const oldBadges = card.querySelectorAll('.linkedin-match-badge-container, .linkedin-match-inline-score');
    oldBadges.forEach(badge => badge.remove());

    // Find the Ignore button to place badge before it
    const ignoreButton = card.querySelector('button[aria-label*="Ignore"]');
    const acceptButton = card.querySelector('button[aria-label*="Accept"]');

    // Create badge container
    const badgeContainer = document.createElement('span');
    badgeContainer.className = 'linkedin-match-badge-container';
    badgeContainer.style.cssText = `
      display: inline-flex;
      align-items: center;
      margin-right: 12px;
    `;

    // Insert BEFORE the Ignore button
    if (ignoreButton && ignoreButton.parentNode) {
      ignoreButton.parentNode.insertBefore(badgeContainer, ignoreButton);
    } else if (acceptButton && acceptButton.parentNode) {
      acceptButton.parentNode.insertBefore(badgeContainer, acceptButton);
    } else {
      // Fallback: append to card
      card.appendChild(badgeContainer);
    }

    // Show loading badge
    const loadingBadge = createInlineScoreBadge('...', 'loading');
    badgeContainer.appendChild(loadingBadge);

    // ENHANCED: Extract more data from card preview
    const aboutSnippet = card.querySelector('.invitation-card__custom-message, .mn-connection-card__occupation')?.textContent.trim() || '';
    const mutualConnections = card.querySelector('.member-insights__count, .mutual-connections')?.textContent.trim() || '';

    // Extract skills from headline (common pattern: "Role | Skill1 | Skill2 | Skill3")
    const skillsFromHeadline = extractSkillsFromHeadline(headline);

    // Build a minimal but useful target profile for Groq
    const targetProfile = {
      name: profileName,
      headline: headline,
      about: aboutSnippet,  // May be connection message or occupation
      skills: skillsFromHeadline,
      experience: parseExperienceFromHeadline(headline),
      connections: mutualConnections.includes('mutual') ? 500 : 100,  // Estimate
      location: extractLocationFromHeadline(headline),
      projects: [],
      posts: [],
      interests: []
    };

    // Get user profile
    const userProfile = await getUserProfile();

    console.log('📊 Card-based scoring for:', profileName);

    // RETRY LOGIC: Try up to 3 times with 10-second wait on 429 errors
    let response = null;
    let retryCount = 0;
    const maxRetries = 3;

    while (retryCount < maxRetries) {
      try {
        // Send to Groq via background script
        response = await chrome.runtime.sendMessage({
          action: 'calculateCompatibility',
          data: {
            profileId,
            userProfile: userProfile,
            targetProfile: targetProfile,
            skill_match_score: calculateQuickSkillMatch(skillsFromHeadline, userProfile.skills || []),
            skill_complementarity_score: 50,
            network_value_a_to_b: 60,
            network_value_b_to_a: 60,
            career_alignment_score: 60,
            experience_gap: 3,
            industry_match: headline.toLowerCase().includes('data') ? 80 : 50,
            geographic_score: 50,
            seniority_match: 60
          }
        });

        // Check if it's a rate limit error
        if (response?.error?.includes('429') || response?.error?.includes('rate')) {
          retryCount++;
          console.log(`⚠️ Rate limited (429) for ${profileName}. Retry ${retryCount}/${maxRetries} in 10s...`);
          await new Promise(resolve => setTimeout(resolve, 10000));
          continue;
        }

        // Success or other error - break out of retry loop
        break;

      } catch (error) {
        retryCount++;
        if (retryCount < maxRetries) {
          console.log(`⚠️ Error for ${profileName}. Retry ${retryCount}/${maxRetries} in 10s...`);
          await new Promise(resolve => setTimeout(resolve, 10000));
        } else {
          throw error;
        }
      }
    }

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
        actionable_benefits: response.data.actionable_benefits || [],
        fromCache: response.fromCache,
        targetProfile: targetProfile,
        userProfile: {
          name: userProfile.name,
          skills: userProfile.skills,
          headline: userProfile.headline
        }
      };

      // Create clickable badge in the container
      const badge = createClickableScoreBadge(matchData);
      badgeContainer.appendChild(badge);
    } else {
      // Show error badge if API failed
      console.warn(`⚠️ API failed for ${profileName}:`, response?.error || 'Unknown error');
      const errorBadge = document.createElement('span');
      errorBadge.textContent = '?';
      errorBadge.title = 'Score unavailable';
      errorBadge.style.cssText = `
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 24px;
        height: 24px;
        padding: 2px 6px;
        background: #9ca3af;
        color: white;
        border-radius: 12px;
        font-size: 12px;
        cursor: help;
      `;
      badgeContainer.appendChild(errorBadge);
    }
  } catch (error) {
    console.error('Error calculating score for card:', profileName, error);
    // Show error indicator
    const errorBadge = document.createElement('span');
    errorBadge.textContent = '!';
    errorBadge.title = 'Error: ' + error.message;
    errorBadge.style.cssText = `
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 24px;
      height: 24px;
      background: #dc2626;
      color: white;
      border-radius: 12px;
      font-size: 12px;
      cursor: help;
    `;
    badgeContainer.appendChild(errorBadge);
  }
}

/**
 * Extract skills from headline (e.g., "Senior Data Engineer | AWS | Spark | Python")
 */
function extractSkillsFromHeadline(headline) {
  if (!headline) return [];

  // Common skill keywords to look for
  const skillKeywords = [
    'python', 'java', 'javascript', 'sql', 'aws', 'azure', 'gcp', 'docker', 'kubernetes',
    'spark', 'hadoop', 'airflow', 'kafka', 'tensorflow', 'pytorch', 'react', 'angular',
    'node', 'django', 'flask', 'machine learning', 'ml', 'ai', 'data science', 'etl',
    'databricks', 'snowflake', 'tableau', 'power bi', 'excel', 'r', 'scala', 'go',
    'mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch', 'dbt', 'pyspark'
  ];

  const lowerHeadline = headline.toLowerCase();
  const foundSkills = [];

  // Check for keywords
  skillKeywords.forEach(skill => {
    if (lowerHeadline.includes(skill)) {
      foundSkills.push(skill.charAt(0).toUpperCase() + skill.slice(1));
    }
  });

  // Also split by | and extract tech-looking terms
  const parts = headline.split(/[|•·,]/);
  parts.forEach(part => {
    const trimmed = part.trim();
    // If it looks like a skill (short, no common words)
    if (trimmed.length > 1 && trimmed.length < 25 &&
      !trimmed.toLowerCase().includes('at ') &&
      !trimmed.toLowerCase().includes('engineer') &&
      !trimmed.toLowerCase().includes('manager') &&
      (trimmed.includes('x ') || /^[A-Z0-9]+$/.test(trimmed) || skillKeywords.some(s => trimmed.toLowerCase().includes(s)))) {
      if (!foundSkills.includes(trimmed)) {
        foundSkills.push(trimmed);
      }
    }
  });

  return foundSkills.slice(0, 10);
}

/**
 * Parse experience info from headline
 */
function parseExperienceFromHeadline(headline) {
  if (!headline) return [];

  const experiences = [];

  // Look for company names (after @ or "at")
  const atMatch = headline.match(/@\s*([A-Za-z0-9\s]+)/i) || headline.match(/at\s+([A-Za-z0-9\s]+)/i);
  if (atMatch) {
    const company = atMatch[1].trim().split(/[|•·]/)[0].trim();
    // Extract role from before @
    const roleMatch = headline.match(/^([^@|•·]+)/);
    const role = roleMatch ? roleMatch[1].trim() : 'Professional';

    experiences.push({
      title: role,
      company: company,
      duration: '',
      description: ''
    });
  }

  return experiences;
}

/**
 * Extract location from headline if present
 */
function extractLocationFromHeadline(headline) {
  if (!headline) return '';

  const locationPatterns = [
    /(?:based in|located in|from)\s+([A-Za-z\s,]+)/i,
    /([A-Za-z]+,\s*[A-Z]{2})/,  // City, STATE format
    /(India|USA|UK|Canada|Germany|Australia|Singapore)/i
  ];

  for (const pattern of locationPatterns) {
    const match = headline.match(pattern);
    if (match) return match[1].trim();
  }

  return '';
}

/**
 * Quick skill match calculation for card-based scoring
 */
function calculateQuickSkillMatch(targetSkills, userSkills) {
  if (!targetSkills || !userSkills || targetSkills.length === 0 || userSkills.length === 0) {
    return 40;
  }

  const targetLower = targetSkills.map(s => s.toLowerCase());
  const userLower = userSkills.map(s => s.toLowerCase());

  let matches = 0;
  targetLower.forEach(skill => {
    if (userLower.some(us => us.includes(skill) || skill.includes(us))) {
      matches++;
    }
  });

  return Math.min(100, 30 + (matches * 15));
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

    // Find the headline element to place badge below it
    const headlineElement = document.querySelector('.text-body-medium.break-words');

    // Create badge container - positioned below headline for visibility
    const badgeContainer = document.createElement('div');
    badgeContainer.className = 'linkedin-match-profile-badge';
    badgeContainer.style.cssText = `
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: 12px;
      margin-bottom: 8px;
      padding: 8px 16px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border-radius: 20px;
      box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
      width: fit-content;
    `;

    // Insert badge BELOW the headline (or after More button as fallback)
    if (headlineElement && headlineElement.parentNode) {
      headlineElement.parentNode.insertBefore(badgeContainer, headlineElement.nextSibling);
    } else {
      // Fallback: insert after More button
      moreButton.parentNode.insertBefore(badgeContainer, moreButton.nextSibling);
    }

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
    // Use Groq API score
    if (response.success && response.data) {
      const score = response.data.compatibility_score;

      console.log('🎯 COMPATIBILITY RESULT (GROQ API):');
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

  // Determine colors based on score
  let bgColor;
  if (matchData.score >= 70) {
    bgColor = '#10a37f';  // Green
  } else if (matchData.score >= 50) {
    bgColor = '#f59e0b';  // Amber
  } else {
    bgColor = '#ef4444';  // Red
  }

  badge.className = `linkedin-match-inline-score ${scoreClass} clickable`;
  badge.textContent = matchData.score.toFixed(0);  // Just the number
  badge.title = `${matchData.score.toFixed(0)} Match - Click for details`;
  badge.style.cssText = `
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 28px;
    height: 24px;
    padding: 2px 8px;
    background: ${bgColor};
    color: white;
    border-radius: 12px;
    cursor: pointer;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 13px;
    font-weight: 600;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  `;

  // Hover effect
  badge.onmouseenter = () => {
    badge.style.transform = 'scale(1.1)';
  };
  badge.onmouseleave = () => {
    badge.style.transform = 'scale(1)';
  };

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
        <h3>🎯 Score Breakdown & Reasoning</h3>
        <div class="linkedin-match-explanation">
          ${factorsHTML}
        </div>
      </div>
      
      <div class="linkedin-match-modal-body" style="margin-top: 16px;">
        <h3>🎯 Should You Connect?</h3>
        <div class="linkedin-match-verdict" style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 16px; border-radius: 12px; border-left: 4px solid ${matchData.score >= 70 ? '#10a37f' : matchData.score >= 50 ? '#f59e0b' : '#ef4444'};">
          <p style="margin: 0; line-height: 1.6; font-size: 14px; color: #333;">
            ${generateConnectionVerdict(matchData)}
          </p>
        </div>
      </div>
      
      <div class="linkedin-match-modal-body" style="margin-top: 16px; text-align: center;">
        <h3>🤝 Would you connect with this person?</h3>
        <p style="color: #666; font-size: 12px; margin: 8px 0;">Your decision helps train the matching algorithm</p>
        <div class="linkedin-match-feedback-buttons" style="display: flex; gap: 16px; justify-content: center; margin-top: 12px;">
          <button class="modal-btn linkedin-match-btn-success" id="modal-feedback-yes" style="padding: 12px 24px; font-size: 16px;">
            👍 Yes, Connect!
          </button>
          <button class="modal-btn linkedin-match-btn-danger" id="modal-feedback-no" style="padding: 12px 24px; font-size: 16px;">
            👎 No, Skip
          </button>
        </div>
        <div id="feedback-thank-you" style="display: none; color: #10a37f; font-weight: bold; margin-top: 12px;">
          ✅ Got it! Thanks for training the model.
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

  // FEEDBACK BUTTON HANDLERS
  modal.querySelector('#modal-feedback-yes').addEventListener('click', async () => {
    await saveFeedback(matchData, true);
    showFeedbackThankYou(modal);
  });

  modal.querySelector('#modal-feedback-no').addEventListener('click', async () => {
    await saveFeedback(matchData, false);
    showFeedbackThankYou(modal);
  });

  // Animate in
  setTimeout(() => modal.classList.add('show'), 10);
}

/**
 * Save user feedback for model validation
 */
async function saveFeedback(matchData, wasUseful) {
  const feedback = {
    profileId: matchData.profileId,
    profileName: matchData.profileName,
    headline: matchData.headline,
    score: matchData.score,
    wasUseful: wasUseful,
    timestamp: new Date().toISOString(),
    url: window.location.href
  };

  console.log('📝 Saving feedback:', feedback);

  try {
    // Send to background script for storage
    await chrome.runtime.sendMessage({
      action: 'saveFeedback',
      data: feedback
    });
    console.log('✅ Feedback saved successfully');
  } catch (error) {
    console.error('❌ Error saving feedback:', error);
    // Fallback: save to local storage directly
    const existing = JSON.parse(localStorage.getItem('linkedin_match_feedback') || '[]');
    existing.push(feedback);
    localStorage.setItem('linkedin_match_feedback', JSON.stringify(existing));
  }
}

/**
 * Show thank you message after feedback
 */
function showFeedbackThankYou(modal) {
  const buttons = modal.querySelector('.linkedin-match-feedback-buttons');
  const thankYou = modal.querySelector('#feedback-thank-you');

  if (buttons) buttons.style.display = 'none';
  if (thankYou) thankYou.style.display = 'block';
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
 * Generate a PERSONALIZED paragraph explaining why to connect (or not)
 * Uses actual extracted profile data for specific recommendations
 * NOW USES ROLE FAMILY DETECTION for smarter verdicts
 */
function generateConnectionVerdict(matchData) {
  const score = matchData.score || 0;
  const name = (matchData.profileName || 'This person').split(' ')[0]; // First name only
  const headline = matchData.headline || '';
  const features = matchData.features || {};
  const targetProfile = matchData.targetProfile || {};
  const userProfile = matchData.userProfile || {};

  // Extract actual data points
  const targetSkills = targetProfile.skills || [];
  const userSkills = userProfile.skills || [];
  const targetLocation = targetProfile.location || '';
  const userLocation = userProfile.location || '';

  // NEW: Detect Role Family for smarter matching
  const roleAffinity = features.role_family_bonus || 0;
  const roleReason = features.role_family_reason || null;

  // Check if target has data-related skills (even if not exact match)
  const dataKeywords = ['data', 'analytics', 'analysis', 'ml', 'machine learning', 'ai',
    'statistics', 'sql', 'python', 'tableau', 'power bi', 'excel',
    'forecasting', 'modeling', 'quantitative', 'research'];
  const targetHasDataSkills = targetSkills.some(s =>
    dataKeywords.some(k => s.toLowerCase().includes(k))
  );
  const userWantsData = (userProfile.headline || '').toLowerCase().includes('data') ||
    userSkills.some(s => dataKeywords.some(k => s.toLowerCase().includes(k)));

  // Find specific overlapping and complementary skills
  const sharedSkills = targetSkills.filter(s =>
    userSkills.some(us => us.toLowerCase().includes(s.toLowerCase()) || s.toLowerCase().includes(us.toLowerCase()))
  ).slice(0, 3);

  const uniqueTargetSkills = targetSkills.filter(s =>
    !userSkills.some(us => us.toLowerCase().includes(s.toLowerCase()) || s.toLowerCase().includes(us.toLowerCase()))
  ).slice(0, 3);

  // Extract role and company from headline
  const company = extractCompanyFromHeadline(headline);

  // Check for key indicators
  const isRecruiter = headline.toLowerCase().includes('recruiter') || headline.toLowerCase().includes('hiring') || headline.toLowerCase().includes('talent');
  const isManager = headline.toLowerCase().includes('manager') || headline.toLowerCase().includes('director') || headline.toLowerCase().includes('lead');
  const isSenior = headline.toLowerCase().includes('senior') || headline.toLowerCase().includes('staff') || headline.toLowerCase().includes('principal');
  const sameLocation = targetLocation && userLocation && (targetLocation.toLowerCase().includes(userLocation.toLowerCase().split(',')[0]) || userLocation.toLowerCase().includes(targetLocation.toLowerCase().split(',')[0]));

  // Build personalized verdict
  let action = '';
  let parts = [];

  // OVERRIDE: If same role family, upgrade verdict regardless of score
  const sameFamily = roleAffinity >= 25;  // 25+ means same or adjacent family
  const adjacentFamily = roleAffinity >= 15 && roleAffinity < 25;

  // HIGH SCORE (70+) OR Same Role Family
  if (score >= 70 || (score >= 40 && sameFamily)) {
    action = `<strong style="color: #10a37f;">✅ YES, CONNECT with ${name}!</strong>`;

    // Role family reason first
    if (roleReason) {
      parts.push(`<b>${roleReason}</b> — great for referrals and industry insights`);
    }

    // Skill-based reason
    if (sharedSkills.length > 0) {
      parts.push(`You both work with <b>${sharedSkills.join(', ')}</b>`);
    }

    // What they can teach you
    if (uniqueTargetSkills.length > 0 && targetHasDataSkills) {
      parts.push(`${name} can help you learn <b>${uniqueTargetSkills.join(', ')}</b>`);
    }

    // Company referral
    if (company) {
      parts.push(`Their position at <b>${company}</b> could open doors for referrals`);
    }

    // Mentorship
    if (isSenior || isManager) {
      parts.push(`As a ${isManager ? 'manager' : 'senior professional'}, ${name} could provide valuable career mentorship`);
    }

    if (parts.length === 0) {
      parts.push(`Strong professional alignment across skills, career stage, and industry`);
    }

    // MEDIUM SCORE (50-69) OR Adjacent Family with lower score
  } else if (score >= 50 || (score >= 30 && adjacentFamily)) {
    action = `<strong style="color: #f59e0b;">⚠️ CONSIDER connecting with ${name}</strong>`;

    if (roleReason) {
      parts.push(`<b>${roleReason}</b> — could be useful for cross-functional networking`);
    } else if (targetHasDataSkills && userWantsData) {
      parts.push(`${name} has <b>data-related skills</b> that could be valuable`);
    } else if (sharedSkills.length > 0) {
      parts.push(`You share some skills (<b>${sharedSkills.join(', ')}</b>), useful for industry insights`);
    } else if (uniqueTargetSkills.length > 0) {
      parts.push(`${name} works with <b>${uniqueTargetSkills.slice(0, 2).join(', ')}</b> which could complement your skillset`);
    }

    if (company) {
      parts.push(`Connect if you're interested in <b>${company}</b> or their industry`);
    } else {
      parts.push(`Consider connecting if you're actively expanding your professional network`);
    }

    // LOW SCORE (below 50) - BUT check for exceptions
  } else {
    // EXCEPTION 1: Recruiter
    if (isRecruiter) {
      action = `<strong style="color: #f59e0b;">⚠️ EXCEPTION — ${name} is a recruiter!</strong>`;
      parts = [`Despite low compatibility, <b>${name} appears to be a recruiter</b>. Connect if you're job searching — they can help regardless of skill match!`];
    }
    // EXCEPTION 2: Has data skills but score is low
    else if (targetHasDataSkills && userWantsData) {
      action = `<strong style="color: #f59e0b;">⚠️ CONSIDER — ${name} works with data!</strong>`;
      parts = [`Despite low overall score, ${name} has <b>data-related skills</b> (${targetSkills.filter(s => dataKeywords.some(k => s.toLowerCase().includes(k))).slice(0, 2).join(', ')}). Could be worth connecting for industry insights.`];
    }
    // DEFAULT: Skip
    else {
      action = `<strong style="color: #ef4444;">❌ SKIP ${name} for now</strong>`;

      if (sharedSkills.length === 0 && uniqueTargetSkills.length > 0) {
        parts.push(`Limited overlap — ${name} works with <b>${uniqueTargetSkills.slice(0, 2).join(', ')}</b> which don't align with your current focus`);
      } else {
        parts.push(`Your professional paths don't align closely enough for meaningful networking`);
      }

      parts.push(`Your time is better spent on connections closer to your career goals`);
    }
  }

  return `${action} — ${parts.join('. ')}.`;
}


/**
 * Extract role from headline
 */
function extractRoleFromHeadline(headline) {
  if (!headline) return '';
  // Get text before "at" or "@" or "|"
  const roleMatch = headline.match(/^([^@|•]+)/);
  if (roleMatch) return roleMatch[1].trim();
  return headline.split('|')[0].trim();
}

/**
 * Extract company from headline helper
 */
function extractCompanyFromHeadline(headline) {
  if (!headline) return '';
  const atMatch = headline.match(/(?:at|@)\s+([A-Za-z0-9\s&]+)/i);
  if (atMatch) return atMatch[1].trim().split(/[|•·]/)[0].trim();
  return '';
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
