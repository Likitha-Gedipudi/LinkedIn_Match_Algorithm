/**
 * Background Service Worker
 * Handles API communication, caching, and analytics
 */

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
    
    // Calculate compatibility
    const result = await calculateCompatibility(profileData);
    
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
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    const data = await response.json();
    
    return {
      success: true,
      data: data,
      timestamp: Date.now()
    };
    
  } catch (error) {
    console.error('API call failed:', error);
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
