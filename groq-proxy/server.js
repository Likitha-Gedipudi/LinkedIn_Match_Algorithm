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

// ========== XGBOOST V3 SCORING (12 Factors) ==========
// Replicates the trained XGBoost model's scoring logic

const PRESTIGIOUS_COMPANIES = ['google', 'meta', 'facebook', 'amazon', 'apple', 'microsoft',
    'netflix', 'tesla', 'uber', 'airbnb', 'stripe', 'linkedin', 'nvidia', 'adobe', 'salesforce'];

const RELATED_ROLES = {
    'data_science': ['data_analytics', 'data_engineering', 'software_dev', 'product'],
    'data_analytics': ['data_science', 'data_engineering', 'product'],
    'software_dev': ['data_engineering', 'data_science', 'product'],
    'product': ['data_science', 'software_dev', 'design'],
    'other': []
};

// XGBoost v3 weights
const XGBOOST_WEIGHTS = {
    mentorship: 0.20,
    network: 0.16,
    skill_learning: 0.16,
    role_synergy: 0.12,
    goal_alignment: 0.05,
    alumni: 0.09,
    career: 0.09,
    industry: 0.07,
    geographic: 0.03,
    engagement: 0.02,
    rising_star: 0.01
};

function inferJobCategory(headline = '', about = '') {
    const text = `${headline} ${about}`.toLowerCase();
    const categories = {
        'data_science': ['data scientist', 'machine learning', 'ml engineer', 'ai', 'data science'],
        'data_analytics': ['data analyst', 'business intelligence', 'bi analyst', 'analytics'],
        'data_engineering': ['data engineer', 'etl', 'pipeline', 'spark'],
        'software_dev': ['software engineer', 'developer', 'sde', 'programmer', 'full stack'],
        'product': ['product manager', 'pm', 'product owner'],
        'design': ['designer', 'ux', 'ui'],
        'executive': ['ceo', 'cto', 'director', 'vp']
    };

    for (const [category, keywords] of Object.entries(categories)) {
        if (keywords.some(kw => text.includes(kw))) return category;
    }
    return 'other';
}

function inferSeniority(headline = '', yearsExp = 0) {
    const text = headline.toLowerCase();
    if (['ceo', 'cto', 'cfo', 'vp', 'director', 'head of'].some(w => text.includes(w))) return 'executive';
    if (['senior', 'lead', 'principal', 'staff'].some(w => text.includes(w))) return 'senior';
    if (['junior', 'associate', 'intern'].some(w => text.includes(w)) || yearsExp < 2) return 'entry';
    return 'mid';
}

function calculateXGBoostScore(userProfile, targetProfile) {
    console.log('🧮 Calculating XGBoost v3 score...');

    const scores = {};

    // 1. Mentorship (20%)
    const userExp = parseInt(userProfile.years_experience) || 0;
    const targetExp = parseInt(targetProfile.years_experience) || 0;
    const expGap = targetExp - userExp;

    if (expGap >= 3 && expGap <= 10) scores.mentorship = 100;
    else if (expGap > 10) scores.mentorship = 70;
    else if (expGap > 0) scores.mentorship = 60;
    else scores.mentorship = 20;

    // 2. Network (16%)
    const targetConn = parseInt(targetProfile.connections) || 0;
    if (targetConn >= 5000) scores.network = 100;
    else if (targetConn >= 2000) scores.network = 85;
    else if (targetConn >= 1000) scores.network = 70;
    else if (targetConn >= 500) scores.network = 55;
    else scores.network = 40;

    const company = (targetProfile.company || targetProfile.current_company || '').toLowerCase();
    if (PRESTIGIOUS_COMPANIES.some(p => company.includes(p))) {
        scores.network = Math.min(scores.network + 15, 100);
    }

    // 3. Skill Learning (16%)
    const userSkills = new Set((userProfile.skills || []).map(s => s.toLowerCase()));
    const targetSkills = new Set((targetProfile.skills || []).map(s => s.toLowerCase()));
    const newSkills = [...targetSkills].filter(s => !userSkills.has(s)).length;

    if (newSkills >= 5) scores.skill_learning = 70;
    else if (newSkills >= 3) scores.skill_learning = 50;
    else scores.skill_learning = 40;

    // 4. Role Synergy (12%)
    const userRole = userProfile.job_category || inferJobCategory(userProfile.headline, userProfile.about);
    const targetRole = targetProfile.job_category || inferJobCategory(targetProfile.headline, targetProfile.about);

    if (userRole === targetRole) scores.role_synergy = 100;
    else if ((RELATED_ROLES[userRole] || []).includes(targetRole)) scores.role_synergy = 70;
    else scores.role_synergy = 40;

    // 5. Goal Alignment (5%)
    const userNeeds = new Set((userProfile.needs || []).map(n => n.toLowerCase()));
    const targetOffers = new Set((targetProfile.can_offer || []).map(o => o.toLowerCase()));

    if (userNeeds.size > 0 && targetOffers.size > 0) {
        const overlap = [...userNeeds].filter(n => targetOffers.has(n)).length;
        scores.goal_alignment = Math.round((overlap / userNeeds.size) * 100) || 50;
    } else {
        scores.goal_alignment = 50;
    }

    // 6. Alumni (9%)
    const userUni = (userProfile.university || '').toLowerCase();
    const targetUni = (targetProfile.university || '').toLowerCase();
    scores.alumni = (userUni && targetUni && (userUni.includes(targetUni) || targetUni.includes(userUni))) ? 100 : 0;

    // 7. Career (9%)
    const targetSeniority = targetProfile.seniority_level || inferSeniority(targetProfile.headline, targetExp);
    const seniorityScores = { entry: 30, mid: 50, senior: 75, executive: 95 };
    scores.career = seniorityScores[targetSeniority] || 30;

    // 8. Industry (7%)
    const userInd = (userProfile.industry || '').toLowerCase();
    const targetInd = (targetProfile.industry || '').toLowerCase();
    scores.industry = (userInd && targetInd && userInd === targetInd) ? 100 : 30;

    // 9. Geographic (3%)
    const userLoc = (userProfile.location || '').split(',');
    const targetLoc = (targetProfile.location || '').split(',');

    if (userLoc.length >= 1 && targetLoc.length >= 1) {
        const userCity = (userLoc[0] || '').trim().toLowerCase();
        const targetCity = (targetLoc[0] || '').trim().toLowerCase();
        if (userCity && targetCity && userCity === targetCity) scores.geographic = 100;
        else if (userLoc.length > 1 && targetLoc.length > 1) {
            const userState = (userLoc[1] || '').trim().toLowerCase();
            const targetState = (targetLoc[1] || '').trim().toLowerCase();
            scores.geographic = (userState && targetState && userState === targetState) ? 70 : 40;
        } else scores.geographic = 40;
    } else scores.geographic = 50;

    // 10. Engagement (2%)
    scores.engagement = parseFloat(targetProfile.engagement_quality_score) || 50;

    // 11. Rising Star (1%)
    const rising = parseFloat(targetProfile.rising_star_score) || 30;
    const hidden = parseFloat(targetProfile.undervalued_score) || 30;
    scores.rising_star = (rising + hidden) / 2;

    // Calculate weighted total
    let total = 0;
    for (const [key, weight] of Object.entries(XGBOOST_WEIGHTS)) {
        total += (scores[key] || 0) * weight;
    }

    // Apply red flag penalty
    const redFlag = parseFloat(targetProfile.red_flag_score) || 0;
    let multiplier = 1.0;
    if (redFlag > 75) multiplier = 0.80;
    else if (redFlag > 50) multiplier = 0.90;
    else if (redFlag > 25) multiplier = 0.95;

    const finalScore = Math.round(total * multiplier * 10) / 10;

    console.log('🎯 XGBoost Score:', finalScore, '/ 100');

    return {
        score: finalScore,
        breakdown: scores,
        multiplier,
        model: 'xgboost_v3'
    };
}

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        groqConfigured: !!process.env.GROQ_API_KEY,
        xgboostEnabled: true
    });
});

// Main proxy endpoint - HYBRID: XGBoost score + Groq recommendations
app.post('/api/compatibility', async (req, res) => {
    console.log('📨 Compatibility request received (HYBRID MODE)');

    try {
        const { userProfile, targetProfile } = req.body;

        // Validate required fields
        if (!userProfile || !targetProfile) {
            return res.status(400).json({
                error: 'Missing required fields: userProfile and targetProfile'
            });
        }

        // STEP 1: Calculate XGBoost score first
        console.log('🧮 STEP 1: Calculating XGBoost v3 score...');
        const xgboostResult = calculateXGBoostScore(userProfile, targetProfile);
        console.log('✅ XGBoost Score:', xgboostResult.score);

        // STEP 2: Get recommendations from Groq
        if (!process.env.GROQ_API_KEY) {
            console.warn('⚠️ GROQ_API_KEY not configured - returning XGBoost only');
            return res.json({
                success: true,
                data: {
                    compatibility_score: xgboostResult.score,
                    score_breakdown: xgboostResult.breakdown,
                    model_source: 'xgboost_v3',
                    recommendations: ['Configure Groq API key for personalized recommendations'],
                    connection_tips: ['Based on XGBoost model scoring']
                },
                timestamp: Date.now()
            });
        }

        console.log('🤖 STEP 2: Getting Groq recommendations...');
        const startTime = Date.now();

        // Forward request to Groq API for recommendations (include XGBoost score for context)
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
                        content: generateHybridSystemPrompt()
                    },
                    {
                        role: 'user',
                        content: generateHybridUserPrompt(userProfile, targetProfile, xgboostResult)
                    }
                ],
                temperature: 0.5,
                max_tokens: 600,
                response_format: { type: 'json_object' }
            })
        });

        const duration = Date.now() - startTime;
        console.log(`⏱️ Groq responded in ${duration}ms`);

        if (!groqResponse.ok) {
            const errorText = await groqResponse.text();
            console.error('❌ Groq API error:', errorText);
            // Fall back to XGBoost only
            return res.json({
                success: true,
                data: {
                    compatibility_score: xgboostResult.score,
                    score_breakdown: xgboostResult.breakdown,
                    model_source: 'xgboost_v3',
                    recommendations: ['Unable to get AI recommendations at this time'],
                    connection_tips: ['Score calculated by XGBoost model']
                },
                timestamp: Date.now()
            });
        }

        const data = await groqResponse.json();
        const groqResult = JSON.parse(data.choices[0].message.content);

        console.log('✅ HYBRID result ready - XGBoost score:', xgboostResult.score);

        // COMBINE: XGBoost score + Groq recommendations
        res.json({
            success: true,
            data: {
                compatibility_score: xgboostResult.score,  // FROM XGBOOST
                score_breakdown: xgboostResult.breakdown,  // FROM XGBOOST
                model_source: 'hybrid_xgboost_groq',
                recommendations: groqResult.recommendations || [],  // FROM GROQ
                connection_tips: groqResult.connection_tips || [],  // FROM GROQ
                match_summary: groqResult.match_summary || '',  // FROM GROQ
                groq_score: groqResult.compatibility_score  // Optional: Groq's score for comparison
            },
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

// Helper: Generate user prompt - ENHANCED VERSION
function generateUserPrompt(userProfile, targetProfile) {
    // Extract keywords from About sections
    const userAboutKeywords = extractKeywordsFromAbout(userProfile.about || '');
    const targetAboutKeywords = extractKeywordsFromAbout(targetProfile.about || '');

    // Extract keywords from experience descriptions
    const userExpKeywords = extractKeywordsFromExperience(userProfile.experience || []);
    const targetExpKeywords = extractKeywordsFromExperience(targetProfile.experience || []);

    return `Analyze compatibility between these two LinkedIn professionals. Focus on HOW the target can help the user.

═══════════════════════════════════════════════════
USER PROFILE (Person seeking connections)
═══════════════════════════════════════════════════

BASIC INFO:
- Name: ${userProfile.name || 'Not specified'}
- Headline: ${userProfile.headline || 'Not specified'}
- Location: ${userProfile.location || 'Not specified'}
- Connections: ${userProfile.connections || 'Unknown'}
- Experience: ${userProfile.experienceYears || 'Unknown'} years
- Industry: ${userProfile.industry || 'Not specified'}
- Seniority: ${userProfile.seniority || 'Not specified'}

SKILLS (${userProfile.skills?.length || 0}):
${userProfile.skills?.slice(0, 15).join(', ') || 'None listed'}

ABOUT SECTION KEYWORDS:
${userAboutKeywords.join(', ') || 'None extracted'}

EXPERIENCE KEYWORDS:
${userExpKeywords.join(', ') || 'None extracted'}

═══════════════════════════════════════════════════
TARGET PROFILE (Person to evaluate for connection)
═══════════════════════════════════════════════════

BASIC INFO:
- Name: ${targetProfile.name || 'Not specified'}
- Headline: ${targetProfile.headline || 'Not specified'}  
- Location: ${targetProfile.location || 'Not specified'}
- Connections: ${targetProfile.connections || 'Unknown'}

ABOUT SECTION (Full Text):
${(targetProfile.about || 'Not available').substring(0, 800)}

SKILLS (${targetProfile.skills?.length || 0}):
${targetProfile.skills?.slice(0, 20).join(', ') || 'None listed'}

EXPERIENCE (${targetProfile.experience?.length || 0} positions):
${targetProfile.experience?.slice(0, 4).map((exp, i) => `
  ${i + 1}. ${exp.title || 'Unknown'} at ${exp.company || 'Unknown'} (${exp.duration || 'Unknown'})
     ${exp.description ? 'Description: ' + exp.description.substring(0, 200) + '...' : ''}
`).join('') || 'None available'}

PROJECTS (${targetProfile.projects?.length || 0}):
${targetProfile.projects?.slice(0, 3).map(p => `- ${p.name}: ${(p.description || '').substring(0, 100)}`).join('\n') || 'None listed'}

INTERESTS:
${targetProfile.interests?.slice(0, 10).join(', ') || 'None listed'}

RECENT POSTS/ACTIVITY:
${targetProfile.posts?.slice(0, 2).map(p => `- ${(p.content || '').substring(0, 150)}...`).join('\n') || 'No recent activity'}

ABOUT SECTION KEYWORDS:
${targetAboutKeywords.join(', ') || 'None extracted'}

EXPERIENCE KEYWORDS:
${targetExpKeywords.join(', ') || 'None extracted'}

═══════════════════════════════════════════════════
ANALYSIS REQUIREMENTS
═══════════════════════════════════════════════════

1. KEYWORD MATCHING (0-25 points):
   - Compare About section keywords
   - Compare skills overlap AND complementarity
   - Compare experience keywords
   - Match: same field? related technologies? synergistic domains?

2. HOW CAN TARGET HELP USER? (0-25 points):
   - Mentorship: Can target mentor user based on experience gap?
   - Skills: What skills can user learn from target?
   - Network: Can target provide referrals to their company/industry?
   - Projects: Are target's projects relevant to user's goals?

3. INTEREST & ACTIVITY ALIGNMENT (0-25 points):
   - Do their interests align for good conversation/connection?
   - Is target active (posts = engaged = more likely to respond)?
   - Shared professional interests = stronger connection

4. PROFESSIONAL FIT (0-25 points):
   - Same/related industry?
   - Geographic proximity for meetups?
   - Seniority appropriate for networking?
   - Career stage compatibility?

═══════════════════════════════════════════════════
OUTPUT FORMAT (JSON ONLY)
═══════════════════════════════════════════════════

{
  "compatibility_score": <0-100>,
  "recommendation": "<STRONGLY CONNECT/CONNECT/CONSIDER/SKIP> - <one-line reason>",
  "explanation": "<keyword match insight> | <how they can help you> | <shared interests> | <professional fit>",
  "actionable_benefits": [
    "Their experience in [X] can help you with [Y]",
    "They can teach you [skill] based on their [project/role]",
    "Connection to [company/industry] could lead to [opportunity]"
  ]
}

CRITICAL RULES:
- EXPLANATION must have 4 factors separated by " | "
- ACTIONABLE_BENEFITS must list 2-3 SPECIFIC ways target helps user
- Be specific: "Can teach you Kubernetes" not "Good skills"
- Reference actual data from their profile
- If no clear benefit, score should be <40

Return ONLY the JSON object. No markdown, no explanations.`;
}

// Helper: Extract keywords from About section
function extractKeywordsFromAbout(aboutText) {
    if (!aboutText) return [];

    const technicalKeywords = ['python', 'java', 'javascript', 'react', 'aws', 'docker', 'kubernetes',
        'machine learning', 'data science', 'sql', 'ai', 'cloud', 'devops', 'api', 'microservices',
        'tensorflow', 'pytorch', 'spark', 'hadoop', 'nlp', 'deep learning', 'llm', 'gpt'];

    const domainKeywords = ['fintech', 'healthcare', 'e-commerce', 'saas', 'b2b', 'startup',
        'enterprise', 'consulting', 'banking', 'insurance', 'retail', 'media'];

    const roleKeywords = ['engineer', 'developer', 'scientist', 'analyst', 'manager', 'lead',
        'architect', 'consultant', 'director', 'founder', 'cto', 'vp'];

    const lowerAbout = aboutText.toLowerCase();
    const found = [];

    [...technicalKeywords, ...domainKeywords, ...roleKeywords].forEach(kw => {
        if (lowerAbout.includes(kw)) found.push(kw);
    });

    return [...new Set(found)].slice(0, 15);
}

// Helper: Extract keywords from experience descriptions
function extractKeywordsFromExperience(experiences) {
    if (!experiences || experiences.length === 0) return [];

    const allText = experiences.map(e =>
        `${e.title || ''} ${e.company || ''} ${e.description || ''}`
    ).join(' ').toLowerCase();

    const actionKeywords = ['built', 'developed', 'led', 'managed', 'designed', 'implemented',
        'scaled', 'optimized', 'automated', 'increased', 'reduced', 'launched', 'created'];

    const techKeywords = ['python', 'java', 'aws', 'kubernetes', 'docker', 'sql', 'react',
        'node', 'api', 'microservices', 'machine learning', 'data pipeline', 'etl'];

    const found = [];

    [...actionKeywords, ...techKeywords].forEach(kw => {
        if (allText.includes(kw)) found.push(kw);
    });

    return [...new Set(found)].slice(0, 15);
}

// ========== HYBRID PROMPTS (For Groq Recommendations) ==========

function generateHybridSystemPrompt() {
    return `You are an expert LinkedIn networking advisor. The compatibility score has ALREADY been calculated by our XGBoost ML model. 

Your job is ONLY to provide:
1. Personalized recommendations on how to approach this connection
2. Specific connection tips based on profile analysis
3. A brief match summary

DO NOT calculate or suggest a different score - use the provided XGBoost score as truth.

Respond in JSON format:
{
    "recommendations": ["recommendation 1", "recommendation 2", "recommendation 3"],
    "connection_tips": ["tip 1", "tip 2"],
    "match_summary": "Brief 1-2 sentence summary of why this person is a good/bad connection"
}`;
}

function generateHybridUserPrompt(userProfile, targetProfile, xgboostResult) {
    return `Based on this XGBoost ML model analysis, provide personalized networking recommendations.

═══ XGBOOST MODEL RESULTS (Already Calculated) ═══
Compatibility Score: ${xgboostResult.score}/100
Score Breakdown:
- Mentorship Potential: ${xgboostResult.breakdown.mentorship || 0}/100
- Network Value: ${xgboostResult.breakdown.network || 0}/100
- Skill Learning: ${xgboostResult.breakdown.skill_learning || 0}/100
- Role Synergy: ${xgboostResult.breakdown.role_synergy || 0}/100
- Goal Alignment: ${xgboostResult.breakdown.goal_alignment || 0}/100
- Alumni Connection: ${xgboostResult.breakdown.alumni || 0}/100
- Career Advancement: ${xgboostResult.breakdown.career || 0}/100
- Industry Match: ${xgboostResult.breakdown.industry || 0}/100
- Geographic: ${xgboostResult.breakdown.geographic || 0}/100

═══ USER PROFILE ═══
Name: ${userProfile.name || 'User'}
Headline: ${userProfile.headline || 'Not specified'}
Skills: ${(userProfile.skills || []).slice(0, 10).join(', ')}
Industry: ${userProfile.industry || 'Not specified'}
Experience: ${userProfile.years_experience || userProfile.experienceYears || '?'} years

═══ TARGET PROFILE ═══
Name: ${targetProfile.name || 'Target'}
Headline: ${targetProfile.headline || 'Not specified'}
Company: ${targetProfile.company || targetProfile.current_company || 'Not specified'}
Skills: ${(targetProfile.skills || []).slice(0, 10).join(', ')}
Industry: ${targetProfile.industry || 'Not specified'}
Experience: ${targetProfile.years_experience || targetProfile.experienceYears || '?'} years
Location: ${targetProfile.location || 'Not specified'}

Based on this analysis, provide:
1. 3 specific recommendations for connecting with this person
2. 2 connection tips (conversation starters, common ground)
3. A brief match summary

Focus on ACTIONABLE advice. Reference specific profile data. Be concise.`;
}

// Start server
app.listen(PORT, () => {
    console.log(`🚀 Groq Proxy Server running on port ${PORT}`);
    console.log(`🧮 XGBoost v3 scoring: ENABLED`);
    console.log(`🔑 Groq API Key configured: ${!!process.env.GROQ_API_KEY}`);
    console.log(`🌐 Health check: http://localhost:${PORT}/health`);
});

