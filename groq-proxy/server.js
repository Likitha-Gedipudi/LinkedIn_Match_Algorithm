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
                temperature: 0.5,
                max_tokens: 800,
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
    return `You are an expert LinkedIn professional networking compatibility analyzer. Your role is to provide DISCRIMINATING scores that meaningfully differentiate between connections.

CRITICAL: Scores must spread across 0-100 range. DO NOT cluster scores around 40-60. Be strict and honest.

═══════════════════════════════════════════════════
STRICT SCORING FRAMEWORK (Total: 100 points)
═══════════════════════════════════════════════════

1. SKILLS COMPATIBILITY (0-25 points) - EQUAL WEIGHT
   ⚠️ IMPORTANT: Focus on RELATED and COMPLEMENTARY skills, not just exact matches
   
   A. Direct Skill Overlap (0-15 points):
      Count skills as "matching" if they are:
      - Exact matches (Python = Python)
      - Related technologies (React & Angular, AWS & Azure)  
      - Same domain (Data Analysis & Machine Learning, Frontend & UI/UX)
      
      Scoring:
      - 0 related skills: 0 points
      - 1-2 related skills: 4 points (weak)
      - 3-5 related skills: 9 points (moderate)
      - 6-10 related skills: 13 points (strong)
      - 10+ related skills: 15 points (exceptional)
   
   B. Complementary Skills (0-10 points):
      Skills that create mutual learning opportunities (e.g., One knows Python, other knows R)
      - No complementary value: 0 points
      - Generic complementarity: 4 points
      - Strong complementarity (clear synergy): 7 points
      - Exceptional complementarity (perfect fit): 10 points
   
   PENALTY: If industries completely unrelated AND no skill overlap: -10 points

2. PROFESSIONAL ALIGNMENT (0-25 points) - EQUAL WEIGHT
   ⚠️ EXPERIENCE GAP PENALTIES:
   
   A. Experience Compatibility (0-12 points):
      - 0-2 years gap (peers): 12 points
      - 3-5 years gap (mentorship): 9 points
      - 6-10 years gap: 5 points
      - 11-15 years gap: 2 points
      - 15+ years gap: 0 points (too large)
   
   B. Career Stage Match (0-8 points):
      - Same seniority level: 8 points
      - 1 level difference: 5 points
      - 2 levels difference: 2 points
      - 3+ levels difference: 0 points
   
   C. Industry Relevance (0-5 points):
      - Same industry: 5 points
      - Related industry: 3 points
      - Different industry: 0 points

3. NETWORK VALUE (0-25 points) - EQUAL WEIGHT
   ⚠️ CONNECTION STRENGTH MATTERS:
   
   A. Network Size Analysis (0-18 points):
      User Network:
      - Under 100 connections: 3 points
      - 100-500 connections: 7 points
      - 500-1000 connections: 11 points
      - 1000+ connections: 14 points
      
      Target Network:
      - Under 100 connections: 2 points
      - 100-500 connections: 5 points
      - 500+ connections: 8 points
   
   B. Geographic Proximity (0-3 points) - MINIMAL WEIGHT:
      - Same city/region: 3 points
      - Same country: 2 points
      - Different country: 0 points
   
   C. Seniority Appropriateness (0-4 points):
      - Appropriate match: 4 points
      - Slight mismatch: 2 points
      - Large gap (intern vs C-level): -4 points

4. STRATEGIC VALUE (0-25 points) - EQUAL WEIGHT
   
   A. Mutual Benefit Potential (0-15 points):
      - High mutual benefit (both gain significantly): 15 points
      - Moderate benefit (clear value exchange): 10 points
      - One-sided benefit: 5 points
      - No clear benefit: 0 points
   
   B. Career Goals Alignment (0-10 points):
      - Aligned goals/trajectory: 10 points
      - Somewhat aligned: 5 points
      - Misaligned: 0 points

═══════════════════════════════════════════════════
SCORE DISTRIBUTION REQUIREMENTS
═══════════════════════════════════════════════════

You MUST use the full 0-100 range:

0-20:  INCOMPATIBLE - Completely different fields, no overlap
       Example: Junior graphic designer vs Senior chemical engineer

21-40: POOR MATCH - Minimal commonality, weak potential
       Example: Different industries, different locations, 1 shared skill

41-60: MODERATE - Some overlap but significant gaps
       Example: Same industry but different roles, 2-3 shared skills

61-80: GOOD MATCH - Strong compatibility, clear mutual benefit
       Example: Same field, 5+ shared skills, similar experience

81-95: EXCELLENT - Exceptional alignment, ideal connection
       Example: Same company, complementary roles, 10+ shared skills

96-100: PERFECT - Rare! Almost identical professional profiles
        Reserve ONLY for truly exceptional matches

═══════════════════════════════════════════════════
CRITICAL RULES
═══════════════════════════════════════════════════

1. **RELATED SKILLS COUNT**: Don't require exact matches - React & Vue.js are related, Python & R are related
2. **CALCULATE HOLISTICALLY**: Consider the overall compatibility across all categories
3. **USE FULL RANGE**: Scores of 15, 28, 73, 89 are all valid - don't cluster around 50
4. **JUSTIFY HIGH SCORES**: 70+ requires strong evidence across multiple categories
5. **PENALIZE MISMATCHES**: Apply all penalty criteria strictly
6. **NO DEFAULTS**: Analyze deeply rather than defaulting to middle scores

SCORING CALCULATION:
- Add up points from all 4 categories (Skills + Career + Network + Strategic)
- The sum naturally creates a 0-100 score
- Ensure balanced consideration of all three main areas (Skills, Career, Network)

OUTPUT FORMAT (JSON ONLY):
{
  "compatibility_score": <precise number 0-100>,
  "recommendation": "<recommendation>",
  "explanation": "<factor 1> | <factor 2> | <factor 3> | <factor 4>"
}

RECOMMENDATION FORMAT:
- 0-40: "SKIP - <specific reason>"
- 41-60: "CONSIDER - <specific reason>"
- 61-80: "CONNECT - <specific reason>"
- 81-100: "STRONGLY CONNECT - <specific reason>"

Return ONLY the JSON object. No markdown, no explanations.`;
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
