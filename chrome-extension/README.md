# 🤝 LinkedIn Professional Match AI - Chrome Extension

Enterprise-grade Chrome extension that provides real-time AI-powered compatibility scoring for LinkedIn profiles.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Manifest](https://img.shields.io/badge/manifest-v3-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## ✨ Features

### Core Functionality
- **Real-time Compatibility Scoring** - Automatic analysis when viewing LinkedIn profiles
- **Beautiful Overlay UI** - Non-intrusive, gradient-styled score card
- **Smart Caching** - 24-hour cache to reduce API calls and improve performance
- **Batch Processing** - Analyze multiple profiles efficiently
- **Data Export** - Export compatibility data as JSON

### Enterprise Features
- **Analytics Dashboard** - Track scans, high matches, and usage patterns
- **Configurable Settings** - Customize scoring thresholds and behavior
- **API Health Monitoring** - Real-time API status checks every 5 minutes
- **Privacy-First** - All processing via your deployed API, no third-party tracking
- **Offline Support** - Works with cached data when offline

### User Interface
- **Popup Dashboard** - Quick access to stats and settings
- **Options Page** - Full settings control panel
- **Score Visualization** - Color-coded scores (Excellent/Good/Moderate/Low)
- **Loading States** - Smooth animations during analysis
- **Error Handling** - Clear error messages with retry options

## 📸 Screenshots

```
┌─────────────────────────────────┐
│  Compatibility Score            │
│  ────────────────────────────── │
│           61.4/100              │
│  Recommended - Good compatibility│
│  Strong skill complementarity | │
│  Valuable network connections   │
│  ────────────────────────────── │
│  🔄  📊  ✕                      │
└─────────────────────────────────┘
```

## 🚀 Installation

### Method 1: Load Unpacked (Development)

1. **Clone or download** this repository
2. **Open Chrome** and navigate to `chrome://extensions/`
3. **Enable Developer Mode** (toggle in top right)
4. Click **"Load unpacked"**
5. Select the `chrome-extension` folder
6. The extension icon will appear in your toolbar

### Method 2: Chrome Web Store (Coming Soon)

Once published, install directly from the Chrome Web Store.

## ⚙️ Configuration

### Initial Setup

1. Click the extension icon to open the popup
2. Click **"Settings"** to configure:
   - Enable/disable API integration
   - Toggle score overlay
   - Configure caching
   - Set minimum score threshold
3. Click **"Save Settings"**

### API Configuration

The extension connects to your deployed API:
```
https://linkedin-match-algorithm-4ce8d98dc007.herokuapp.com
```

To change the API endpoint, edit `scripts/background.js`:
```javascript
const API_BASE_URL = 'YOUR_API_URL_HERE';
```

## 📖 Usage

### Basic Usage

1. **Navigate to LinkedIn** profile page
2. **Wait 1-2 seconds** for analysis
3. **View compatibility score** in the overlay card
4. **Take action** based on the recommendation

### Interpreting Scores

| Score | Color | Recommendation |
|-------|-------|----------------|
| 80-100 | 🟢 Green | Excellent - Connect immediately |
| 60-79 | 🔵 Blue | Good - Worth considering |
| 40-59 | 🟡 Yellow | Moderate - Evaluate carefully |
| 0-39 | 🔴 Red | Low - Limited mutual benefit |

### Features Explained

#### Compatibility Score
- **0-100 scale** calculated by AI model
- Based on 18 features including:
  - Skill match & complementarity
  - Network value (bidirectional)
  - Career alignment
  - Experience gap
  - Industry match
  - Geographic proximity
  - Seniority match

#### Actions
- **🔄 Refresh** - Recalculate score (bypasses cache)
- **📊 Export** - Download JSON with full data
- **✕ Close** - Hide overlay (reopens on page refresh)

### Analytics Dashboard

View your usage statistics:
- **Total Scans** - Profiles analyzed
- **High Matches** - Scores ≥60
- **Cache Size** - Cached profiles
- **API Status** - Online/Offline indicator
- **Model Status** - Loaded/Not Loaded

## 🔧 Technical Details

### Architecture

```
LinkedIn Page
    ↓
Content Script (content.js)
    ↓ Extract Profile Data
Feature Calculation
    ↓
Background Service Worker (background.js)
    ↓ Check Cache
API Call (if not cached)
    ↓
Heroku API (Gradient Boosting Model)
    ↓
Score + Explanation
    ↓
Display Overlay (content.css)
```

### File Structure

```
chrome-extension/
├── manifest.json           # Extension config (Manifest V3)
├── popup.html              # Extension popup UI
├── options.html            # Settings page
├── scripts/
│   ├── background.js       # Service worker (API, cache, analytics)
│   ├── content.js          # LinkedIn page injection
│   ├── popup.js            # Popup interactions
│   └── options.js          # Settings interactions
├── styles/
│   └── content.css         # Overlay styling
├── icons/
│   ├── icon16.png
│   ├── icon48.png
│   └── icon128.png
└── README.md
```

### Permissions

- **storage** - Save settings and cache
- **activeTab** - Access LinkedIn pages
- **scripting** - Inject content scripts
- **host_permissions** - Connect to LinkedIn and API

### Caching Strategy

- **Duration**: 24 hours
- **Size Limit**: 100 profiles (LRU eviction)
- **Storage**: Chrome Local Storage
- **Bypass**: Refresh button clears individual cache

### API Integration

**Endpoints Used:**
- `GET /health` - API health check (every 5 minutes)
- `POST /api/v1/compatibility` - Score calculation

**Request Format:**
```json
{
  "skill_match_score": 75.0,
  "skill_complementarity_score": 80.0,
  "network_value_a_to_b": 70.0,
  "network_value_b_to_a": 75.0,
  "career_alignment_score": 85.0,
  "experience_gap": 5,
  "industry_match": 90.0,
  "geographic_score": 65.0,
  "seniority_match": 75.0
}
```

## 🐛 Troubleshooting

### Extension Not Working

1. **Check API Status** - Open popup, verify "API Status: Online"
2. **Reload Extension** - Go to `chrome://extensions/`, click reload
3. **Clear Cache** - In popup, click "Clear Cache"
4. **Check Console** - Open DevTools, look for errors

### Score Not Appearing

1. **Verify Settings** - Settings > "Show Score Overlay" is enabled
2. **Check Profile URL** - Must be `/in/` profile page
3. **Wait Longer** - Profile loading can take 2-5 seconds
4. **Refresh Page** - Hard reload (Cmd/Ctrl + Shift + R)

### API Errors

- **503 Error** - Model not loaded on server
- **500 Error** - Server processing error
- **Network Error** - Check internet connection or API status

## 🔐 Privacy & Security

- **No data collection** - All data stays local or goes to your API
- **No tracking** - Zero third-party analytics
- **Cache-only storage** - Profile data cached locally (24h max)
- **HTTPS only** - Encrypted API communication
- **Open source** - Full code transparency

## 🛠️ Development

### Prerequisites
- Chrome Browser (v88+)
- Access to deployed API
- Basic JavaScript knowledge

### Local Development

1. Make changes to extension files
2. Go to `chrome://extensions/`
3. Click **Reload** on the extension
4. Test on LinkedIn profile

### Building Icons

Icons are required in 3 sizes: 16x16, 48x48, 128x128
Place PNG files in `icons/` directory.

Quick icon generation:
```bash
# Using ImageMagick
convert logo.png -resize 16x16 icons/icon16.png
convert logo.png -resize 48x48 icons/icon48.png
convert logo.png -resize 128x128 icons/icon128.png
```

## 📝 Changelog

### v1.0.0 (2025-12-22)
- ✨ Initial release
- 🎯 Real-time compatibility scoring
- 💾 Smart caching system
- 📊 Analytics dashboard
- ⚙️ Full settings control
- 🎨 Beautiful gradient UI

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Built with Chrome Extension Manifest V3
- API powered by Heroku
- ML model: Scikit-learn Gradient Boosting
- UI inspired by modern design principles

## 📧 Support

- **Issues**: GitHub Issues
- **Email**: support@your-domain.com
- **Docs**: Full API documentation at `/docs`

---

**Made with ❤️ for better professional networking**
