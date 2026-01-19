/**
 * Keyword Extractor for LinkedIn Profiles
 * Extracts and categorizes keywords from all profile sections
 */

// Technical skill keywords database
const TECHNICAL_KEYWORDS = {
    programming: ['python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust', 'scala', 'ruby', 'php', 'swift', 'kotlin', 'r', 'matlab'],
    data_tools: ['sql', 'spark', 'hadoop', 'airflow', 'kafka', 'pandas', 'numpy', 'dbt', 'snowflake', 'databricks', 'bigquery', 'redshift'],
    ml_ai: ['machine learning', 'deep learning', 'tensorflow', 'pytorch', 'scikit-learn', 'keras', 'nlp', 'computer vision', 'llm', 'transformers', 'neural network', 'ai', 'artificial intelligence', 'gpt', 'bert', 'langchain'],
    cloud: ['aws', 'azure', 'gcp', 'google cloud', 'cloud', 'ec2', 's3', 'lambda', 'kubernetes', 'docker', 'terraform', 'cloudformation'],
    web: ['react', 'angular', 'vue', 'node', 'nodejs', 'django', 'flask', 'fastapi', 'express', 'nextjs', 'graphql', 'rest api'],
    databases: ['mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch', 'cassandra', 'dynamodb', 'neo4j'],
    devops: ['ci/cd', 'jenkins', 'github actions', 'gitlab', 'ansible', 'prometheus', 'grafana', 'linux', 'bash'],
    mobile: ['ios', 'android', 'react native', 'flutter', 'swift', 'kotlin']
};

// Domain/Industry keywords
const DOMAIN_KEYWORDS = {
    fintech: ['fintech', 'banking', 'payments', 'blockchain', 'cryptocurrency', 'trading', 'investment', 'financial services', 'insurance', 'wealth management'],
    healthcare: ['healthcare', 'medical', 'biotech', 'pharma', 'clinical', 'health tech', 'telemedicine', 'patient', 'hospital', 'life sciences'],
    ecommerce: ['e-commerce', 'ecommerce', 'retail', 'marketplace', 'shopping', 'consumer', 'supply chain', 'logistics', 'inventory'],
    saas: ['saas', 'b2b', 'enterprise', 'platform', 'subscription', 'crm', 'erp', 'productivity'],
    media: ['media', 'entertainment', 'streaming', 'content', 'gaming', 'social media', 'advertising', 'marketing tech'],
    education: ['education', 'edtech', 'learning', 'training', 'curriculum', 'academic', 'university', 'school'],
    security: ['cybersecurity', 'security', 'infosec', 'privacy', 'compliance', 'authentication', 'encryption']
};

// Role/Position keywords
const ROLE_KEYWORDS = {
    data_science: ['data scientist', 'machine learning engineer', 'ml engineer', 'ai engineer', 'research scientist', 'applied scientist', 'data science'],
    data_engineering: ['data engineer', 'analytics engineer', 'etl', 'data platform', 'data infrastructure', 'big data'],
    data_analytics: ['data analyst', 'business analyst', 'analytics', 'business intelligence', 'bi developer', 'reporting'],
    software_engineering: ['software engineer', 'developer', 'sde', 'swe', 'backend', 'frontend', 'full stack', 'architect'],
    product: ['product manager', 'product owner', 'pm', 'product lead', 'product strategy'],
    design: ['ux designer', 'ui designer', 'product designer', 'ux researcher', 'design lead'],
    leadership: ['director', 'vp', 'cto', 'ceo', 'head of', 'manager', 'lead', 'principal', 'staff', 'senior staff']
};

// Interest/Topic keywords (from posts and activity)
const INTEREST_KEYWORDS = {
    career: ['career growth', 'job search', 'networking', 'interview', 'resume', 'career advice', 'mentorship'],
    tech_trends: ['generative ai', 'chatgpt', 'llm', 'ai trends', 'tech trends', 'innovation', 'startup', 'venture capital'],
    leadership_topics: ['leadership', 'management', 'team building', 'culture', 'hiring', 'diversity', 'inclusion'],
    learning: ['learning', 'certification', 'online course', 'bootcamp', 'upskilling', 'training']
};

/**
 * Extract keywords from text content
 */
function extractKeywordsFromText(text, keywordDatabase) {
    if (!text) return [];

    const lowerText = text.toLowerCase();
    const found = new Set();

    for (const [category, keywords] of Object.entries(keywordDatabase)) {
        for (const keyword of keywords) {
            if (lowerText.includes(keyword.toLowerCase())) {
                found.add(keyword);
            }
        }
    }

    return Array.from(found);
}

/**
 * Extract all keywords from a comprehensive profile
 */
function extractAllKeywords(profileData) {
    // Combine all text fields for analysis
    const allText = [
        profileData.name || '',
        profileData.headline || '',
        profileData.about || '',
        profileData.location || '',
        ...(profileData.skills || []),
        ...(profileData.experience || []).map(exp =>
            `${exp.title || ''} ${exp.company || ''} ${exp.description || ''}`
        ),
        ...(profileData.education || []).map(edu =>
            `${edu.school || ''} ${edu.degree || ''} ${edu.field || ''}`
        ),
        ...(profileData.projects || []).map(proj =>
            `${proj.name || ''} ${proj.description || ''}`
        ),
        ...(profileData.posts || []).map(post => post.content || ''),
        ...(profileData.interests || [])
    ].join(' ');

    return {
        technical: extractKeywordsFromText(allText, TECHNICAL_KEYWORDS),
        domain: extractKeywordsFromText(allText, DOMAIN_KEYWORDS),
        role: extractKeywordsFromText(allText, ROLE_KEYWORDS),
        interests: extractKeywordsFromText(allText, INTEREST_KEYWORDS),

        // Raw extracted data
        rawSkills: profileData.skills || [],
        rawAboutKeywords: extractKeywordsFromText(profileData.about || '', TECHNICAL_KEYWORDS),
        rawExperienceKeywords: extractKeywordsFromText(
            (profileData.experience || []).map(e => e.description || '').join(' '),
            TECHNICAL_KEYWORDS
        )
    };
}

/**
 * Compare keywords between two profiles
 */
function compareKeywords(userKeywords, targetKeywords) {
    const comparison = {
        // Technical overlap
        technicalOverlap: userKeywords.technical.filter(k =>
            targetKeywords.technical.includes(k)
        ),
        technicalUserOnly: userKeywords.technical.filter(k =>
            !targetKeywords.technical.includes(k)
        ),
        technicalTargetOnly: targetKeywords.technical.filter(k =>
            !userKeywords.technical.includes(k)
        ),

        // Domain overlap
        domainOverlap: userKeywords.domain.filter(k =>
            targetKeywords.domain.includes(k)
        ),
        domainUserOnly: userKeywords.domain.filter(k =>
            !targetKeywords.domain.includes(k)
        ),
        domainTargetOnly: targetKeywords.domain.filter(k =>
            !userKeywords.domain.includes(k)
        ),

        // Role similarity
        roleOverlap: userKeywords.role.filter(k =>
            targetKeywords.role.includes(k)
        ),

        // Interest alignment
        interestOverlap: userKeywords.interests.filter(k =>
            targetKeywords.interests.includes(k)
        )
    };

    // Calculate scores
    comparison.technicalScore = comparison.technicalOverlap.length > 0
        ? Math.min(100, comparison.technicalOverlap.length * 15)
        : 0;

    comparison.domainScore = comparison.domainOverlap.length > 0
        ? Math.min(100, comparison.domainOverlap.length * 20)
        : 0;

    comparison.roleScore = comparison.roleOverlap.length > 0
        ? Math.min(100, comparison.roleOverlap.length * 25)
        : 0;

    comparison.interestScore = comparison.interestOverlap.length > 0
        ? Math.min(100, comparison.interestOverlap.length * 20)
        : 0;

    // Value they can offer (skills they have that you don't)
    comparison.learningOpportunities = targetKeywords.technical.filter(k =>
        !userKeywords.technical.includes(k)
    );

    return comparison;
}

/**
 * Generate actionable description of how target can help user
 */
function generateActionableDescription(userProfile, targetProfile, keywordComparison) {
    const descriptions = [];

    // Technical learning opportunities
    if (keywordComparison.learningOpportunities.length > 0) {
        const topSkills = keywordComparison.learningOpportunities.slice(0, 3);
        descriptions.push(`Can help you learn: ${topSkills.join(', ')}`);
    }

    // Domain expertise
    if (keywordComparison.domainTargetOnly.length > 0) {
        const domains = keywordComparison.domainTargetOnly.slice(0, 2);
        descriptions.push(`Has expertise in: ${domains.join(', ')}`);
    }

    // Role synergy
    if (keywordComparison.roleOverlap.length > 0) {
        descriptions.push(`Same field: Great for peer networking and referrals`);
    }

    // Interest alignment
    if (keywordComparison.interestOverlap.length > 0) {
        const interests = keywordComparison.interestOverlap.slice(0, 2);
        descriptions.push(`Shared interests: ${interests.join(', ')}`);
    }

    // Technical overlap for collaboration
    if (keywordComparison.technicalOverlap.length >= 3) {
        descriptions.push(`Strong tech overlap: Good for project collaboration`);
    }

    return descriptions;
}

// Export functions for use in content.js
if (typeof window !== 'undefined') {
    window.KeywordExtractor = {
        extractAllKeywords,
        compareKeywords,
        generateActionableDescription,
        TECHNICAL_KEYWORDS,
        DOMAIN_KEYWORDS,
        ROLE_KEYWORDS,
        INTEREST_KEYWORDS
    };
}
