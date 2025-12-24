# Quick Start Guide: URL-Based Profile Extraction

## How to Use the Updated Feature

### Step 1: Reload Your Extension
1. Go to `chrome://extensions/`
2. Find "LinkedIn Professional Match AI"
3. Click the **Reload** button (🔄 icon)

### Step 2: Get Your LinkedIn Profile URL
1. Go to your LinkedIn profile
2. Copy the URL from the address bar
   - Should look like: `https://www.linkedin.com/in/your-name/`
   - Or just: `linkedin.com/in/your-name/`

### Step 3: Extract Your Profile
1. Right-click the extension icon → **Options**
2. In the "📝 My Profile" section, you'll see a blue "✨ Quick Setup" box
3. **Paste your LinkedIn URL** in the "Your LinkedIn Profile URL" field
4. Click **"📥 Extract from LinkedIn URL"**
5. Wait while the extension:
   - Opens/finds your profile page
   - Extracts all your data
   - Auto-fills the form

### Step 4: Review and Save
1. Your profile data will auto-fill all fields:
   - Name
   - Skills (comma-separated)
   - Years of Experience
   - Connections
   - Industry (auto-detected!)
   - Seniority Level (calculated!)
   - Location
   - Headline
2. Review the extracted data
3. Make any adjustments if needed
4. Click **💾 Save My Profile**

## What Happens?

The extension will:
- ✅ Check if you already have that profile open in a tab (uses existing tab)
- ✅ Or open a new tab in the background with your profile
- ✅ Wait for the page to fully load
- ✅ Extract all your profile information
- ✅ Close the tab if it was newly created
- ✅ Fill in all the form fields for you

## Advantages of URL Method

✅ **No manual navigation** - Just paste URL and click  
✅ **Works from anywhere** - Don't need to be on LinkedIn first  
✅ **Automatic tab management** - Opens/closes tabs as needed  
✅ **Reuses existing tabs** - If profile already open, uses that tab  

## Troubleshooting

### Error: "Please enter your LinkedIn profile URL first"
**Solution:** Paste your LinkedIn URL in the input field

### Error: "Please enter a valid LinkedIn profile URL"
**Solution:** Make sure your URL contains `linkedin.com/in/`

### Error: "Could not connect to LinkedIn"
**Solution:** Wait a few seconds and try again (LinkedIn might be slow)

### Extension asks for additional permissions
**Solution:** Accept the "tabs" permission - needed to open/manage tabs

---

## Example URLs That Work

✅ `https://www.linkedin.com/in/john-doe/`  
✅ `linkedin.com/in/john-doe/`  
✅ `www.linkedin.com/in/jane-smith-12345/`  

❌ `https://www.linkedin.com/` (missing `/in/`)  
❌ `https://www.linkedin.com/feed/` (not a profile)  

---

**Need help?** The extension shows helpful error messages if something goes wrong!
