# 🚀 Quick Start Guide - LinkedIn Match AI Extension

## Prerequisites

- ✅ Chrome Browser installed
- ✅ API deployed to Heroku (https://linkedin-match-algorithm-4ce8d98dc007.herokuapp.com)
- ✅ API is healthy and model is loaded

## Installation Steps (5 minutes)

### Step 1: Generate Icons (1 minute)

**Quick Method - Create Simple Placeholders:**

```bash
cd /Users/likig/Desktop/linkedin_match/chrome-extension/icons

# Create simple colored placeholder icons (requires Python/PIL or ImageMagick)
# Or just use any 3 PNG files named icon16.png, icon48.png, icon128.png

# If you have Python with PIL:
python3 -c "from PIL import Image; Image.new('RGB', (16,16), '#667eea').save('icon16.png')"
python3 -c "from PIL import Image; Image.new('RGB', (48,48), '#667eea').save('icon48.png')"
python3 -c "from PIL import Image; Image.new('RGB', (128,128), '#667eea').save('icon128.png')"
```

**Or download any icon online** and resize to 16x16, 48x48, 128x128.

### Step 2: Load Extension (2 minutes)

1. Open Chrome
2. Navigate to: `chrome://extensions/`
3. Enable "Developer mode" (toggle in top-right)
4. Click "Load unpacked"
5. Select folder: `/Users/likig/Desktop/linkedin_match/chrome-extension`
6. Extension appears! 🎉

### Step 3: Verify Setup (1 minute)

1. Click the extension icon in Chrome toolbar
2. Check dashboard shows:
   - ✅ API Status: Online
   - ✅ Model Status: Loaded
3. If not online, wait 10 seconds and refresh

### Step 4: Test on LinkedIn (1 minute)

1. Go to any LinkedIn profile (e.g., linkedin.com/in/williamhgates)
2. Wait 2-3 seconds
3. You should see a purple gradient compatibility card appear!

## Troubleshooting

### Icons Not Showing?
- Any PNG files will work temporarily
- Extension will still function without proper icons

### "API Status: Offline"?
- Wait 30 seconds (health check runs every 5 min + on load)
- Check your API is deployed: `curl https://linkedin-match-algorithm-4ce8d98dc007.herokuapp.com/health`

### Score Not Appearing?
1. Open Chrome DevTools (F12)
2. Check Console tab for errors
3. Verify you're on a profile page (URL contains `/in/`)
4. Refresh the page

### "Model not loaded" Error?
- Check API health endpoint: `/health`
- Model should be loaded on Heroku
- May need to redeploy API

## Next Steps

✨ **Customize Settings:**
- Click extension icon
- Click "Settings"
- Adjust threshold, caching, etc.

📊 **View Analytics:**
- Click extension icon
- See total scans and high matches

🎨 **Create Better Icons:**
- See `icons/ICON_INSTRUCTIONS.md`
- Make professional-looking icons

## Need Help?

Check the full README.md for:
- Complete feature documentation
- Detailed troubleshooting guide
- API configuration options
- Development guidelines

---

**Enjoy smarter LinkedIn networking! 🤝**
