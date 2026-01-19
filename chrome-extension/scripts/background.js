/**
 * Background Service Worker
 * Handles API communication, caching, and analytics
 */

// ========== GROQ API CONFIGURATION (via Proxy) ==========
const GROQ_PROXY_URL = 'https://linkedin-match-groq-proxy-4ddeee207bcb.herokuapp.com'; // Production
const USE_GROQ_API = true; // Toggle: true = Groq (via proxy), false = Model API

// System prompt for Groq
const GROQ_SYSTEM_PROMPT = `You are an expert LinkedIn professional networking compatibility analyzer with deep understanding of:
- Professional skill synergies and complementarity
- Career trajectory alignment and mentorship opportunities  
- Network value and mutual benefit assessment
- Geographic and industry collaboration potential

Your task is to analyze two LinkedIn profiles and return a detailed compatibility assessment.

ANALYSIS FRAMEWORK:
1. Skills Analysis (40 points)
   - Direct skill overlap for collaboration (0-20 points)
   - Complementary skills for mutual learning (0-20 points)

2. Career Alignment (25 points)
   - Similar career stage for peer support (0-10 points)
   - Experience gap for mentorship (0-10 points)
   - Industry relevance (0-5 points)

3. Network Value (20 points)
   - Connection strength (both sides) (0-10 points)
   - Geographic proximity for meetups (0-5 points)
   - Seniority match for appropriate networking (0-5 points)

4. Professional Context (15 points)
   - Industry alignment (0-8 points)
   - Location benefits (0-4 points)
   - Career goals compatibility (0-3 points)

SCORING TIERS:
- 80-100: Exceptional Match (Strong connect recommendation)
- 60-79: Good Match (Recommended to connect)
- 40-59: Moderate Match (Consider connecting)
- 0-39: Weak Match (Skip for now)

RETURN FORMAT:
You MUST return ONLY a valid JSON object with this EXACT structure:
{
  "compatibility_score": <float 0-100>,
  "recommendation": "<string>",
  "explanation": "<string with exactly 4 factors separated by ' | '>"
}

CRITICAL RULES:
- NO markdown formatting
- NO code blocks
- NO explanatory text
- ONLY the raw JSON object
- Score must be a number between 0-100
- Explanation must have exactly 4 factors separated by " | "`;

// ========== EXISTING MODEL API CONFIGURATION ==========
const API_BASE_URL = 'https://linkedin-match-algorithm-4ce8d98dc007.herokuapp.com';
const CACHE_DURATION = 24 * 60 * 60 * 1000; // 24 hours

// Initialize extension
chrome.runtime.onInstalled.addListener(() => {
  console.log('LinkedIn Match AI Extension Installed');

  // Set default settings
  chrome.storage.sync.set({
    apiEnabled: true,
    showScoreOverlay: true,
    cacheEnabled: true,
    analyticsEnabled: true,
    minScoreThreshold: 40
  });

  // Initialize analytics
  chrome.storage.local.set({
    totalScans: 0,
    highMatches: 0,
    lastScanTime: null
  });
});

// Message handler from content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'calculateCompatibility') {
    handleCompatibilityRequest(request.data)
      .then(sendResponse)
      .catch(error => sendResponse({ error: error.message }));
    return true; // Async response
  }

  if (request.action === 'getSettings') {
    chrome.storage.sync.get(null, sendResponse);
    return true;
  }

  if (request.action === 'updateAnalytics') {
    updateAnalytics(request.data);
    sendResponse({ success: true });
  }

  if (request.action === 'clearCache') {
    chrome.storage.local.remove('profileCache', () => {
      sendResponse({ success: true });
    });
    return true;
  }

  // NEW: Save user feedback for model validation
  if (request.action === 'saveFeedback') {
    saveFeedback(request.data)
      .then(() => sendResponse({ success: true }))
      .catch(error => sendResponse({ error: error.message }));
    return true;
  }

  // NEW: Get all collected feedback
  if (request.action === 'getFeedback') {
    getFeedbackData()
      .then(data => sendResponse({ success: true, data }))
      .catch(error => sendResponse({ error: error.message }));
    return true;
  }

  // NEW: Export feedback as CSV
  if (request.action === 'exportFeedback') {
    exportFeedbackAsCSV()
      .then(csv => sendResponse({ success: true, csv }))
      .catch(error => sendResponse({ error: error.message }));
    return true;
  }

  // NEW: Clear feedback data
  if (request.action === 'clearFeedback') {
    chrome.storage.local.remove('userFeedback', () => {
      sendResponse({ success: true });
    });
    return true;
  }
});

/**
 * Handle compatibility calculation with caching
 */
async function handleCompatibilityRequest(profileData) {
  try {
    // Check settings
    const settings = await chrome.storage.sync.get(['apiEnabled', 'cacheEnabled']);

    if (!settings.apiEnabled) {
      return { error: 'API is disabled in settings' };
    }

    // Check cache
    if (settings.cacheEnabled) {
      const cached = await getCachedScore(profileData.profileId);
      if (cached) {
        console.log('Using cached score for:', profileData.profileId);
        return { ...cached, fromCache: true };
      }
    }

    // Calculate compatibility - route based on toggle
    let result;
    if (USE_GROQ_API) {
      console.log('🤖 Using Groq API (via proxy server)');
      result = await calculateWithGroq(profileData.userProfile, profileData.targetProfile);
    } else {
      console.log('🔢 Using Model API (fallback)');
      result = await calculateCompatibility(profileData);
    }

    // Cache result
    if (settings.cacheEnabled && result.success) {
      await cacheScore(profileData.profileId, result);
    }

    // Update analytics
    await updateAnalytics({
      scan: true,
      highMatch: result.data?.compatibility_score >= 60
    });

    return result;

  } catch (error) {
    console.error('Compatibility calculation error:', error);
    return { error: error.message, success: false };
  }
}

/**
 * Call API to calculate compatibility
 */
async function calculateCompatibility(profileData) {
  console.log('🌐 ========== API CALL START ==========');
  console.log('📤 API Endpoint:', `${API_BASE_URL}/api/v1/compatibility`);
  console.log('📊 Request Payload:', {
    skill_match_score: profileData.skill_match_score || 50,
    skill_complementarity_score: profileData.skill_complementarity_score || 50,
    network_value_a_to_b: profileData.network_value_a_to_b || 50,
    network_value_b_to_a: profileData.network_value_b_to_a || 50,
    career_alignment_score: profileData.career_alignment_score || 50,
    experience_gap: profileData.experience_gap || 5,
    industry_match: profileData.industry_match || 50,
    geographic_score: profileData.geographic_score || 50,
    seniority_match: profileData.seniority_match || 50
  });

  const requestStartTime = Date.now();

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/compatibility`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        skill_match_score: profileData.skill_match_score || 50,
        skill_complementarity_score: profileData.skill_complementarity_score || 50,
        network_value_a_to_b: profileData.network_value_a_to_b || 50,
        network_value_b_to_a: profileData.network_value_b_to_a || 50,
        career_alignment_score: profileData.career_alignment_score || 50,
        experience_gap: profileData.experience_gap || 5,
        industry_match: profileData.industry_match || 50,
        geographic_score: profileData.geographic_score || 50,
        seniority_match: profileData.seniority_match || 50
      })
    });

    const requestDuration = Date.now() - requestStartTime;
    console.log(`⏱️ API Response Time: ${requestDuration}ms`);
    console.log('📡 HTTP Status:', response.status, response.statusText);

    if (!response.ok) {
      console.error('❌ API Error - Non-OK status:', response.status);
      throw new Error(`API Error: ${response.status}`);
    }

    const data = await response.json();

    console.log('✅ API Response Data:', data);
    console.log('🎯 Calculated Score:', data.compatibility_score);
    console.log('📋 Recommendation:', data.recommendation);
    console.log('💡 Explanation:', data.explanation);
    console.log('✅ ========== API CALL SUCCESS ==========\n');

    return {
      success: true,
      data: data,
      timestamp: Date.now()
    };

  } catch (error) {
    const requestDuration = Date.now() - requestStartTime;
    console.error('❌ ========== API CALL FAILED ==========');
    console.error('⏱️ Failed after:', requestDuration + 'ms');
    console.error('❌ Error:', error.message);
    console.error('📚 Stack:', error.stack);
    console.error('❌ ========================================\n');

    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * Cache management
 */
async function getCachedScore(profileId) {
  return new Promise((resolve) => {
    chrome.storage.local.get('profileCache', (result) => {
      const cache = result.profileCache || {};
      const cached = cache[profileId];

      if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
        resolve(cached);
      } else {
        resolve(null);
      }
    });
  });
}

async function cacheScore(profileId, result) {
  return new Promise((resolve) => {
    chrome.storage.local.get('profileCache', (data) => {
      const cache = data.profileCache || {};
      cache[profileId] = result;

      // Limit cache size to 100 profiles
      const keys = Object.keys(cache);
      if (keys.length > 100) {
        // Remove oldest entries
        keys.sort((a, b) => cache[a].timestamp - cache[b].timestamp);
        keys.slice(0, keys.length - 100).forEach(key => delete cache[key]);
      }

      chrome.storage.local.set({ profileCache: cache }, resolve);
    });
  });
}

/**
 * Analytics tracking
 */
async function updateAnalytics(data) {
  chrome.storage.local.get(['totalScans', 'highMatches'], (result) => {
    const updates = {
      lastScanTime: Date.now()
    };

    if (data.scan) {
      updates.totalScans = (result.totalScans || 0) + 1;
    }

    if (data.highMatch) {
      updates.highMatches = (result.highMatches || 0) + 1;
    }

    chrome.storage.local.set(updates);
  });
}

/**
 * Health check on startup
 */
async function checkAPIHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    const data = await response.json();

    chrome.storage.local.set({
      apiStatus: data.status,
      modelLoaded: data.model_loaded,
      lastHealthCheck: Date.now()
    });

    return data;
  } catch (error) {
    console.error('Health check failed:', error);
    chrome.storage.local.set({
      apiStatus: 'error',
      lastHealthCheck: Date.now()
    });
  }
}

// Run health check every 5 minutes
setInterval(checkAPIHealth, 5 * 60 * 1000);
checkAPIHealth(); // Initial check
// ========== GROQ HELPER FUNCTIONS & IMPLEMENTATION ==========

/**
 * Helper: Categorize skills by type
 */
function categorizeSkills(skills, category) {
  if (!skills || skills.length === 0) return 'None';

  const categories = {
    technical: ['python', 'javascript', 'java', 'react', 'sql', 'aws', 'docker',
      'kubernetes', 'machine learning', 'data science', 'ai', 'nodejs',
      'typescript', 'angular', 'vue', 'mongodb', 'postgresql', 'git',
      'linux', 'tensorflow', 'pytorch', 'spark', 'hadoop'],
    business: ['product management', 'strategy', 'marketing', 'sales', 'seo',
      'business development', 'consulting', 'finance', 'analytics',
      'project management', 'agile', 'scrum', 'operations', 'planning'],
    soft: ['leadership', 'communication', 'teamwork', 'problem solving',
      'critical thinking', 'creativity', 'adaptability', 'time management',
      'presentation', 'negotiation']
  };

  const categoryKeywords = categories[category] || [];
  const matchedSkills = skills.filter(skill =>
    categoryKeywords.some(keyword =>
      skill.toLowerCase().includes(keyword) || keyword.includes(skill.toLowerCase())
    )
  );

  return matchedSkills.length > 0
    ? matchedSkills.slice(0, 5).join(', ')
    : 'None';
}

/**
 * Helper: Estimate experience years from experience array
 */
function estimateExperienceYears(experiences) {
  if (!experiences || experiences.length === 0) return 0;

  let totalYears = 0;
  experiences.forEach(exp => {
    if (exp.duration) {
      const yearMatch = exp.duration.match(/(\d+)\s*yrs?/);
      const monthMatch = exp.duration.match(/(\d+)\s*mos?/);

      if (yearMatch) totalYears += parseInt(yearMatch[1]);
      if (monthMatch) totalYears += parseInt(monthMatch[1]) / 12;
    }
  });

  return totalYears > 0 ? Math.round(totalYears) : experiences.length * 2;
}

/**
 * Generate comprehensive prompt for Groq
 */
function generateGroqPrompt(userProfile, targetProfile) {
  const estimatedYears = estimateExperienceYears(targetProfile.experience);

  return `Analyze compatibility between these two LinkedIn professionals in detail:

═══════════════════════════════════════════════════
USER PROFILE (Your Profile)
═══════════════════════════════════════════════════

BASIC INFORMATION:
- Full Name: ${userProfile.name || 'Not specified'}
- Professional Headline: ${userProfile.headline || 'Not specified'}
- Location: ${userProfile.location || 'Not specified'}
- Connection Count: ${userProfile.connections || 'Unknown'}

PROFESSIONAL BACKGROUND:
- Total Years of Experience: ${userProfile.experienceYears || 'Not specified'}
- Industry: ${userProfile.industry || 'Not specified'}
- Career Seniority Level: ${userProfile.seniority || 'Not specified'}

SKILLS (${userProfile.skills?.length || 0} total):
${userProfile.skills?.length > 0
      ? userProfile.skills.map((skill, i) => `  ${i + 1}. ${skill}`).join('\n')
      : '  No skills listed'}

SKILL CATEGORIES:
- Technical Skills: ${categorizeSkills(userProfile.skills, 'technical')}
- Business Skills: ${categorizeSkills(userProfile.skills, 'business')}
- Soft Skills: ${categorizeSkills(userProfile.skills, 'soft')}

═══════════════════════════════════════════════════
TARGET PROFILE (Person to Analyze)
═══════════════════════════════════════════════════

BASIC INFORMATION:
- Full Name: ${targetProfile.name || 'Not specified'}
- Professional Headline: ${targetProfile.headline || 'Not specified'}
- Location: ${targetProfile.location || 'Not specified'}
- Connection Count: ${targetProfile.connections || 'Unknown'}

PROFESSIONAL BACKGROUND:
- Total Work Positions: ${targetProfile.experience?.length || 0}
- Estimated Years of Experience: ${estimatedYears || 'Unknown'}
- Education Background: ${targetProfile.education?.length || 0} degrees/certifications

SKILLS (${targetProfile.skills?.length || 0} total):
${targetProfile.skills?.length > 0
      ? targetProfile.skills.map((skill, i) => `  ${i + 1}. ${skill}`).join('\n')
      : '  No skills listed'}

EXPERIENCE DETAILS:
${targetProfile.experience?.length > 0
      ? targetProfile.experience.slice(0, 5).map((exp, i) => `
  Position ${i + 1}:
  - Title: ${exp.title || 'Not specified'}
  - Company: ${exp.company || 'Not specified'}
  - Duration: ${exp.duration || 'Not specified'}
  `).join('\n')
      : '  No experience details available'}

EDUCATION:
${targetProfile.education?.length > 0
      ? targetProfile.education.map((edu, i) => `
  ${i + 1}. ${edu.degree || edu.school || 'Not specified'}${edu.field ? ` in ${edu.field}` : ''}
  `).join('\n')
      : '  No education details available'}

═══════════════════════════════════════════════════
ANALYSIS REQUIREMENTS
═══════════════════════════════════════════════════

1. SKILLS COMPATIBILITY:
   - Identify overlapping skills for immediate collaboration
   - Find complementary skills for mutual learning opportunities
   - Assess if target's skills fill gaps in user's expertise
   - Consider if skills align with each other's career needs

2. CAREER ALIGNMENT:
   - Compare experience levels (peer vs mentorship potential)
   - Evaluate if career trajectories align
   - Check if industries are compatible or complementary
   - Assess seniority match for networking appropriateness

3. NETWORK VALUE:
   - Evaluate mutual networking benefit
   - Consider geographic proximity for in-person collaboration
   - Assess connection strength on both sides
   - Identify potential for introductions/referrals

4. PROFESSIONAL CONTEXT:
   - Industry synergies or cross-pollination opportunities
   - Location benefits (same city = meetups, different = remote collab)
   - Headline alignment with user's goals
   - Overall professional compatibility

SCORING INSTRUCTIONS:
- Be realistic and nuanced
- Consider both similarities AND differences (both have value)
- Weight skills heavily (40% of score)
- Consider mentorship gaps positively if appropriate
- Geographic proximity is a bonus, not requirement
- Give specific, actionable reasoning

OUTPUT FORMAT (JSON ONLY):
{
  "compatibility_score": <precise number 0-100, can be decimal>,
  "recommendation": "CONNECT - <specific reason>" | "CONSIDER - <specific reason>" | "SKIP - <specific reason>",
  "explanation": "<factor 1> | <factor 2> | <factor 3> | <factor 4>"
}

EXPLANATION GUIDELINES:
Each factor should be specific and data-driven. Examples:
✅ GOOD: "15+ overlapping skills including Python, React, and AWS"
✅ GOOD: "Complementary expertise: User in ML, target in data engineering"  
✅ GOOD: "3-year experience gap ideal for mentorship relationship"
✅ GOOD: "Both in San Francisco tech industry with 500+ connections"

❌ BAD: "Good skills"
❌ BAD: "Nice profile"
❌ BAD: "Compatible"

Return ONLY the JSON object. No other text.`;
}

/**
 * Validate Groq response format
 */
function validateGroqResponse(response) {
  if (!response.compatibility_score) {
    throw new Error('Missing compatibility_score');
  }

  if (!response.recommendation) {
    throw new Error('Missing recommendation');
  }

  if (!response.explanation) {
    throw new Error('Missing explanation');
  }

  if (response.compatibility_score < 0 || response.compatibility_score > 100) {
    throw new Error('Invalid score range');
  }

  const factors = response.explanation.split(' | ');
  if (factors.length < 3) {
    console.warn('⚠️ Explanation has fewer than 4 factors');
  }

  response.compatibility_score = parseFloat(response.compatibility_score);

  return response;
}

/**
 * Calculate compatibility using Groq API
 */
/**
 * Calculate compatibility using Groq API via Proxy Server
 */
async function calculateWithGroq(userProfile, targetProfile) {
  console.log('🤖 ========== GROQ PROXY CALL START ==========');
  console.log('👤 User Profile:', userProfile);
  console.log('🎯 Target Profile:', targetProfile);

  try {
    const requestStartTime = Date.now();

    // Call our secure proxy server (API key is on server)
    const response = await fetch(`${GROQ_PROXY_URL}/api/compatibility`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        userProfile: userProfile,
        targetProfile: targetProfile
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Proxy server error ${response.status}: ${errorText}`);
    }

    const result = await response.json();
    const requestDuration = Date.now() - requestStartTime;

    console.log(`⏱️ Proxy Response Time: ${requestDuration}ms`);
    console.log('📥 Proxy Response:', result);
    console.log('🎯 Score:', result.data.compatibility_score);
    console.log('💡 Recommendation:', result.data.recommendation);
    console.log('📋 Explanation:', result.data.explanation);
    console.log('✅ ========== GROQ PROXY CALL SUCCESS ==========\n');

    return result;

  } catch (error) {
    console.error('❌ ========== GROQ PROXY CALL FAILED ==========');
    console.error('Error:', error.message);
    console.error('Stack:', error.stack);
    console.error('❌ ==========================================\n');

    throw error;
  }
}

// ========== FEEDBACK COLLECTION FOR MODEL VALIDATION ==========

/**
 * Save user feedback for model validation
 */
async function saveFeedback(feedbackData) {
  return new Promise((resolve, reject) => {
    chrome.storage.local.get('userFeedback', (result) => {
      const feedback = result.userFeedback || [];
      feedback.push(feedbackData);

      chrome.storage.local.set({ userFeedback: feedback }, () => {
        if (chrome.runtime.lastError) {
          reject(chrome.runtime.lastError);
        } else {
          console.log(`📊 Feedback saved. Total: ${feedback.length} samples`);
          resolve();
        }
      });
    });
  });
}

/**
 * Get all collected feedback data
 */
async function getFeedbackData() {
  return new Promise((resolve) => {
    chrome.storage.local.get('userFeedback', (result) => {
      const feedback = result.userFeedback || [];

      // Calculate statistics
      const total = feedback.length;
      const useful = feedback.filter(f => f.wasUseful).length;
      const notUseful = total - useful;
      const accuracy = total > 0 ? (useful / total * 100).toFixed(1) : 0;

      resolve({
        feedback,
        stats: {
          total,
          useful,
          notUseful,
          accuracy: `${accuracy}%`
        }
      });
    });
  });
}

/**
 * Export feedback as CSV for model training
 */
async function exportFeedbackAsCSV() {
  return new Promise((resolve) => {
    chrome.storage.local.get('userFeedback', (result) => {
      const feedback = result.userFeedback || [];

      if (feedback.length === 0) {
        resolve('No feedback data collected yet.');
        return;
      }

      // CSV header
      const headers = ['profileId', 'profileName', 'headline', 'score', 'wasUseful', 'timestamp', 'url'];
      const csvRows = [headers.join(',')];

      // CSV data rows
      feedback.forEach(f => {
        const row = [
          f.profileId || '',
          `"${(f.profileName || '').replace(/"/g, '""')}"`,
          `"${(f.headline || '').replace(/"/g, '""')}"`,
          f.score || 0,
          f.wasUseful ? 1 : 0,
          f.timestamp || '',
          f.url || ''
        ];
        csvRows.push(row.join(','));
      });

      resolve(csvRows.join('\n'));
    });
  });
}

