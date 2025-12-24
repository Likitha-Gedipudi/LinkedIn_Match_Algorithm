# Groq API Proxy Server

Secure backend proxy to hide Groq API keys from Chrome extension users.

## Quick Start

### 1. Install Dependencies
```bash
npm install
``

`

### 2. Configure API Key
```bash
cp .env.example .env
# Edit .env and add your Groq API key
```

### 3. Run Locally
```bash
npm start
# or for development with auto-reload:
npm run dev
```

Server will start on `http://localhost:3000`

## Endpoints

### Health Check
```
GET /health
```

Returns server status and whether API key is configured.

### Compatibility Analysis
```
POST /api/compatibility
Content-Type: application/json

{
  "userProfile": {
    "name": "...",
    "skills": [...],
    ...
  },
  "targetProfile": {
    "name": "...",
    "skills": [...],
    ...
  }
}
```

Returns compatibility score and analysis.

## Deploy to Heroku

### 1. Install Heroku CLI
```bash
brew tap heroku/brew && brew install heroku
```

### 2. Login and Create App
```bash
heroku login
heroku create your-app-name
```

### 3. Set Environment Variable
```bash
heroku config:set GROQ_API_KEY=your_api_key_here
```

### 4. Deploy
```bash
git init
git add .
git commit -m "Initial commit"
git push heroku main
```

### 5. Verify
```bash
heroku open /health
```

## Deploy to Vercel (Alternative)

### 1. Install Vercel CLI
```bash
npm i -g vercel
```

### 2. Deploy
```bash
vercel
```

### 3. Add Environment Variable
Go to Vercel dashboard → Your Project → Settings → Environment Variables
Add: `GROQ_API_KEY=your_key_here`

## Security Features

- ✅ API key stored as environment variable
- ✅ CORS restricted to chrome-extension://
- ✅ Rate limiting (20 req/min per IP)
- ✅ Request validation
- ✅ Helmet.js security headers
- ✅ Error messages don't leak sensitive info

## Update Chrome Extension

After deploying, update `background.js`:

```javascript
// Change this URL to your deployed server
const GROQ_PROXY_URL = 'https://your-app.herokuapp.com';

// In calculateWithGroq function, change:
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
```

## Testing

Test locally:
```bash
curl http://localhost:3000/health
```

Test compatibility endpoint:
```bash
curl -X POST http://localhost:3000/api/compatibility \
  -H "Content-Type: application/json" \
  -d '{
    "userProfile": {"name": "Test", "skills": ["Python"]},
    "targetProfile": {"name": "Test2", "skills": ["Java"]}
  }'
```

## Monitoring

Check Heroku logs:
```bash
heroku logs --tail
```

## Cost

- Heroku: Free tier (550 hours/month)
- Vercel: Free tier (100GB bandwidth)
- Groq API: Pay per use

Your API key is safe on the server! 🔒
