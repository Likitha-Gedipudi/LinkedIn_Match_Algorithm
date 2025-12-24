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
async function calculateWithGroq(userProfile, targetProfile) {
    console.log('🤖 ========== GROQ API CALL START ==========');
    console.log('👤 User Profile:', userProfile);
    console.log('🎯 Target Profile:', targetProfile);

    const prompt = generateGroqPrompt(userProfile, targetProfile);
    console.log('📝 Groq Prompt Length:', prompt.length, 'characters');

    try {
        // Get API key from storage
        const settings = await chrome.storage.sync.get('groqApiKey');
        const apiKey = settings.groqApiKey;

        if (!apiKey) {
            throw new Error('Groq API key not configured');
        }

        const requestStartTime = Date.now();

        const response = await fetch(GROQ_API_URL, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: GROQ_MODEL,
                messages: [
                    {
                        role: 'system',
                        content: GROQ_SYSTEM_PROMPT
                    },
                    {
                        role: 'user',
                        content: prompt
                    }
                ],
                temperature: 0.3,
                max_tokens: 500,
                top_p: 1,
                response_format: { type: 'json_object' }
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Groq API error ${response.status}: ${errorText}`);
        }

        const data = await response.json();
        const requestDuration = Date.now() - requestStartTime;

        console.log(`⏱️ Groq Response Time: ${requestDuration}ms`);
        console.log('📥 Raw Groq Response:', data);

        let result = JSON.parse(data.choices[0].message.content);
        result = validateGroqResponse(result);

        console.log('✅ Validated Groq Result:', result);
        console.log('🎯 Score:', result.compatibility_score);
        console.log('💡 Recommendation:', result.recommendation);
        console.log('📋 Explanation:', result.explanation);
        console.log('✅ ========== GROQ API CALL SUCCESS ==========\n');

        return {
            success: true,
            data: result,
            timestamp: Date.now(),
            source: 'groq'
        };

    } catch (error) {
        console.error('❌ ========== GROQ API CALL FAILED ==========');
        console.error('Error:', error.message);
        console.error('Stack:', error.stack);
        console.error('❌ ==========================================\n');

        throw error;
    }
}
