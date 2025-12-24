require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');

const app = express();
const PORT = process.env.PORT || 3000;

// Security middleware
app.use(helmet());
app.use(express.json());

// CORS configuration - only allow Chrome extension
const corsOptions = {
    origin: function (origin, callback) {
        // Allow requests with no origin (like mobile apps or curl requests) for testing
        // In production, you might want to be more restrictive
        if (!origin || origin.startsWith('chrome-extension://')) {
            callback(null, true);
        } else {
            callback(new Error('Not allowed by CORS'));
        }
    },
    methods: ['POST'],
    credentials: true
};
app.use(cors(corsOptions));

// Rate limiting - 20 requests per minute per IP
const limiter = rateLimit({
    windowMs: 60 * 1000, // 1 minute
    max: 20,
    message: { error: 'Too many requests, please try again later.' }
});
app.use('/api/', limiter);

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        groqConfigured: !!process.env.GROQ_API_KEY
    });
});

// Main proxy endpoint
app.post('/api/compatibility', async (req, res) => {
    console.log('📨 Compatibility request received');

    try {
        const { userProfile, targetProfile } = req.body;

        // Validate required fields
        if (!userProfile || !targetProfile) {
            return res.status(400).json({
                error: 'Missing required fields: userProfile and targetProfile'
            });
        }

        if (!process.env.GROQ_API_KEY) {
            console.error('❌ GROQ_API_KEY not configured');
            return res.status(500).json({ error: 'Server configuration error' });
        }

        console.log('🤖 Forwarding to Groq API...');
        const startTime = Date.now();

        // Forward request to Groq API
        const groqResponse = await fetch('https://api.groq.com/openai/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${process.env.GROQ_API_KEY}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: 'llama-3.3-70b-versatile',
                messages: [
                    {
                        role: 'system',
                        content: generateSystemPrompt()
                    },
                    {
                        role: 'user',
                        content: generateUserPrompt(userProfile, targetProfile)
                    }
                ],
                temperature: 0.3,
                max_tokens: 500,
                response_format: { type: 'json_object' }
            })
        });

        const duration = Date.now() - startTime;
        console.log(`⏱️ Groq responded in ${duration}ms`);

        if (!groqResponse.ok) {
            const errorText = await groqResponse.text();
            console.error('❌ Groq API error:', errorText);
            return res.status(groqResponse.status).json({
                error: `Groq API error: ${groqResponse.status}`
            });
        }

        const data = await groqResponse.json();
        const result = JSON.parse(data.choices[0].message.content);

        console.log('✅ Compatibility calculated:', result.compatibility_score);

        // Return result to extension
        res.json({
            success: true,
            data: result,
            timestamp: Date.now()
        });

    } catch (error) {
        console.error('❌ Proxy error:', error.message);
        res.status(500).json({
            error: 'Internal server error',
            message: error.message
        });
    }
});

// Helper: Generate system prompt
function generateSystemPrompt() {
    return `You are an expert LinkedIn professional networking compatibility analyzer with deep understanding of:
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
}

// Helper: Generate user prompt
function generateUserPrompt(userProfile, targetProfile) {
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

Return ONLY the JSON object. No other text.`;
}

// Start server
app.listen(PORT, () => {
    console.log(`🚀 Groq Proxy Server running on port ${PORT}`);
    console.log(`🔑 API Key configured: ${!!process.env.GROQ_API_KEY}`);
    console.log(`🌐 Health check: http://localhost:${PORT}/health`);
});
