/**
 * Debug Helper for LinkedIn Match AI Extension
 * Run in Chrome Console to diagnose issues
 */

console.log('🔍 LinkedIn Match AI Debug Helper Loaded\n');

// Test 1: Check if extension is loaded
console.log('1️⃣ Extension Status:');
console.log('  Content Script Loaded:', typeof analyzeProfile !== 'undefined' ? '✅' : '❌');
console.log('  Settings Available:', typeof settings !== 'undefined' ? '✅' : '❌');

// Test 2: Find profile name elements
console.log('\n2️⃣ Profile Name Elements:');
const nameSelectors = [
  '.pv-text-details__left-panel h1',
  '.text-heading-xlarge',
  'h1.inline',
  '[data-generated-suggestion-target] h1',
  '.artdeco-entity-lockup__title',
  'h1'
];

nameSelectors.forEach(selector => {
  const found = document.querySelector(selector);
  console.log(`  ${selector}:`, found ? '✅ Found' : '❌ Not found');
  if (found) {
    console.log(`    Text: "${found.textContent.trim()}"`);
  }
});

// Test 3: Find network page cards
console.log('\n3️⃣ Network Page Cards:');
const cardSelectors = [
  '[data-control-name="invite_card"]',
  '.mn-connection-card',
  '.discover-person-card',
  '.reusable-search__result-container'
];

cardSelectors.forEach(selector => {
  const found = document.querySelectorAll(selector);
  console.log(`  ${selector}: ${found.length} found`);
});

// Test 4: Check API connectivity
console.log('\n4️⃣ Testing API...');
fetch('https://linkedin-match-algorithm-4ce8d98dc007.herokuapp.com/health')
  .then(r => r.json())
  .then(data => {
    console.log('  API Health:', data.status === 'healthy' ? '✅' : '❌');
    console.log('  Model Loaded:', data.model_loaded ? '✅' : '❌');
  })
  .catch(err => {
    console.log('  API Health: ❌ Error:', err.message);
  });

// Test 5: Check current page
console.log('\n5️⃣ Current Page:');
console.log('  URL:', window.location.href);
console.log('  Is Profile Page:', window.location.pathname.includes('/in/') ? '✅' : '❌');
console.log('  Is Network Page:', window.location.pathname.includes('/mynetwork/') ? '✅' : '❌');

// Test 6: Storage check
console.log('\n6️⃣ Extension Storage:');
chrome.storage.sync.get(null, (settings) => {
  console.log('  Settings:', settings);
});

chrome.storage.local.get(['apiStatus', 'modelLoaded', 'totalScans'], (data) => {
  console.log('  API Status:', data.apiStatus);
  console.log('  Model Loaded:', data.modelLoaded);
  console.log('  Total Scans:', data.totalScans || 0);
});

console.log('\n✅ Debug complete! Check results above.');
console.log('💡 Tip: If name elements not found, LinkedIn changed their HTML structure.');
