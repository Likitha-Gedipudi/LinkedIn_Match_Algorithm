/**
 * Profile Helper Functions
 * Intelligent calculations for compatibility features
 */

/**
 * Get or initialize user profile from storage
 */
async function getUserProfile() {
    return new Promise((resolve) => {
        chrome.storage.local.get('userProfile', (result) => {
            if (result.userProfile) {
                resolve(result.userProfile);
            } else {
                // Return default profile - will be replaced once user sets it
                resolve({
                    profileId: null,
                    name: 'Your Profile',
                    skills: [],
                    connections: 500,
                    experienceYears: 5,
                    industry: 'Technology',
                    location: 'United States',
                    seniority: 'mid',
                    headline: '',
                    initialized: false
                });
            }
        });
    });
}

/**
 * Save user profile to storage
 */
async function saveUserProfile(profile) {
    return new Promise((resolve) => {
        profile.initialized = true;
        profile.lastUpdated = Date.now();
        chrome.storage.local.set({ userProfile: profile }, resolve);
    });
}

/**
 * Auto-detect and save current user's profile when on their own LinkedIn page
 */
async function autoDetectUserProfile(profileData) {
    const userProfile = await getUserProfile();

    // Only auto-detect if not already initialized
    if (!userProfile.initialized) {
        const profile = {
            profileId: profileData.profileId,
            name: profileData.name,
            skills: profileData.skills || [],
            connections: profileData.connections || 500,
            experienceYears: estimateExperienceYears(profileData.experience || []),
            industry: extractIndustry(profileData),
            location: extractLocation(profileData),
            seniority: estimateSeniority(estimateExperienceYears(profileData.experience || [])),
            headline: profileData.headline || ''
        };

        await saveUserProfile(profile);
        console.log('✅ Auto-detected user profile:', profile);
        return profile;
    }

    return userProfile;
}

/**
 * Estimate years of experience from experience array
 */
function estimateExperienceYears(experiences) {
    if (!experiences || experiences.length === 0) return 3;

    let totalYears = 0;

    for (const exp of experiences) {
        if (exp.duration) {
            // Parse duration like "2 yrs 3 mos" or "1 yr" or "8 mos"
            const yearMatch = exp.duration.match(/(\d+)\s*yrs?/);
            const monthMatch = exp.duration.match(/(\d+)\s*mos?/);

            if (yearMatch) totalYears += parseInt(yearMatch[1]);
            if (monthMatch) totalYears += parseInt(monthMatch[1]) / 12;
        }
    }

    // If no duration found, estimate 2 years per position
    if (totalYears === 0) {
        totalYears = experiences.length * 2;
    }

    return Math.max(1, Math.round(totalYears));
}

/**
 * Extract industry from profile data
 */
function extractIndustry(profileData) {
    // Try to extract from headline
    const headline = profileData.headline || '';

    // Common industry keywords
    const industries = {
        'Technology': ['software', 'engineer', 'developer', 'tech', 'ai', 'ml', 'data science', 'cloud', 'devops'],
        'Finance': ['finance', 'banking', 'investment', 'trading', 'fintech', 'accountant'],
        'Healthcare': ['healthcare', 'medical', 'doctor', 'nurse', 'pharma', 'hospital'],
        'Marketing': ['marketing', 'brand', 'social media', 'seo', 'content', 'digital marketing'],
        'Sales': ['sales', 'business development', 'account executive', 'revenue'],
        'Design': ['designer', 'ux', 'ui', 'graphics', 'creative', 'product design'],
        'Education': ['teacher', 'professor', 'education', 'instructor', 'academic'],
        'Consulting': ['consultant', 'consulting', 'advisory', 'strategy'],
        'Legal': ['lawyer', 'legal', 'attorney', 'law'],
        'HR': ['human resources', 'recruiter', 'talent', 'hr']
    };

    const lowerHeadline = headline.toLowerCase();

    for (const [industry, keywords] of Object.entries(industries)) {
        if (keywords.some(keyword => lowerHeadline.includes(keyword))) {
            return industry;
        }
    }

    // Default
    return 'Other';
}

/**
 * Extract location from profile data
 */
function extractLocation(profileData) {
    const location = profileData.location || '';

    // Extract country/region
    if (location.includes('United States') || location.includes('USA')) return 'United States';
    if (location.includes('United Kingdom') || location.includes('UK')) return 'United Kingdom';
    if (location.includes('Canada')) return 'Canada';
    if (location.includes('India')) return 'India';
    if (location.includes('Germany')) return 'Germany';
    if (location.includes('France')) return 'France';
    if (location.includes('Australia')) return 'Australia';

    return location || 'Unknown';
}

/**
 * Estimate seniority level from experience years
 */
function estimateSeniority(experienceYears) {
    if (experienceYears <= 2) return 'entry';
    if (experienceYears <= 5) return 'mid';
    if (experienceYears <= 10) return 'senior';
    return 'executive';
}

// ========== ROLE FAMILY AFFINITY SYSTEM ==========
// Gives bonus points when target is in a related career field

/**
 * Define role families - roles that share career paths and can help each other
 */
const ROLE_FAMILIES = {
    'DATA': {
        name: 'Data & Analytics',
        keywords: ['data scientist', 'data analyst', 'data engineer', 'ml engineer', 'machine learning',
            'analytics', 'business intelligence', 'bi developer', 'statistician', 'research scientist',
            'ai engineer', 'nlp', 'deep learning', 'data architect', 'analytics engineer', 'mlops'],
        seniorKeywords: ['lead', 'senior', 'staff', 'principal', 'head of', 'director', 'vp', 'chief data'],
        adjacentFamilies: ['SOFTWARE', 'PRODUCT']  // Related families that also get a small bonus
    },
    'SOFTWARE': {
        name: 'Software Engineering',
        keywords: ['software engineer', 'developer', 'frontend', 'backend', 'fullstack', 'full stack',
            'devops', 'sre', 'site reliability', 'platform engineer', 'cloud engineer', 'ios developer',
            'android developer', 'mobile developer', 'web developer', 'systems engineer', 'infrastructure'],
        seniorKeywords: ['lead', 'senior', 'staff', 'principal', 'architect', 'director', 'vp', 'cto'],
        adjacentFamilies: ['DATA', 'PRODUCT', 'DEVOPS']
    },
    'PRODUCT': {
        name: 'Product & Strategy',
        keywords: ['product manager', 'product owner', 'program manager', 'technical pm', 'tpm',
            'product lead', 'product director', 'strategy', 'growth', 'product analyst'],
        seniorKeywords: ['senior', 'lead', 'director', 'vp', 'head of', 'chief product'],
        adjacentFamilies: ['DATA', 'SOFTWARE', 'DESIGN']
    },
    'DESIGN': {
        name: 'Design & UX',
        keywords: ['ux designer', 'ui designer', 'product designer', 'ux researcher', 'user research',
            'visual designer', 'interaction designer', 'design lead', 'creative director'],
        seniorKeywords: ['senior', 'lead', 'principal', 'director', 'head of design'],
        adjacentFamilies: ['PRODUCT', 'SOFTWARE']
    },
    'MARKETING': {
        name: 'Marketing & Growth',
        keywords: ['marketing', 'growth', 'seo', 'content', 'brand', 'digital marketing', 'social media',
            'performance marketing', 'demand gen', 'marketing analyst', 'marketing manager'],
        seniorKeywords: ['senior', 'lead', 'director', 'vp', 'cmo', 'head of'],
        adjacentFamilies: ['PRODUCT', 'SALES', 'DATA']
    },
    'FINANCE': {
        name: 'Finance & Analytics',
        keywords: ['financial analyst', 'finance', 'investment', 'risk', 'quant', 'quantitative',
            'portfolio', 'trading', 'fintech', 'banking', 'cfa', 'actuary', 'compliance'],
        seniorKeywords: ['senior', 'lead', 'director', 'vp', 'cfo', 'manager'],
        adjacentFamilies: ['DATA', 'CONSULTING']
    },
    'CONSULTING': {
        name: 'Consulting & Strategy',
        keywords: ['consultant', 'consulting', 'strategy', 'advisory', 'management consultant',
            'business analyst', 'transformation', 'implementation'],
        seniorKeywords: ['senior', 'manager', 'principal', 'partner', 'director'],
        adjacentFamilies: ['PRODUCT', 'FINANCE', 'DATA']
    },
    'OPERATIONS': {
        name: 'Operations & Supply Chain',
        keywords: ['operations', 'supply chain', 'logistics', 'process', 'ops', 'project manager',
            'program manager', 'scrum master', 'agile coach', 'delivery manager'],
        seniorKeywords: ['senior', 'lead', 'director', 'vp', 'coo', 'head of'],
        adjacentFamilies: ['PRODUCT', 'SOFTWARE']
    },
    'HR_RECRUITING': {
        name: 'HR & Talent',
        keywords: ['recruiter', 'talent', 'hr', 'human resources', 'people operations', 'hiring',
            'talent acquisition', 'sourcer', 'employer brand'],
        seniorKeywords: ['senior', 'lead', 'director', 'vp', 'head of'],
        adjacentFamilies: []  // HR is useful for everyone but doesn't have adjacent families
    }
};

/**
 * Detect which role family a headline belongs to
 */
function detectRoleFamily(headline) {
    if (!headline) return null;

    const lowerHeadline = headline.toLowerCase();

    for (const [familyKey, family] of Object.entries(ROLE_FAMILIES)) {
        if (family.keywords.some(keyword => lowerHeadline.includes(keyword))) {
            // Check if senior
            const isSenior = family.seniorKeywords.some(k => lowerHeadline.includes(k));
            return {
                family: familyKey,
                name: family.name,
                isSenior: isSenior,
                adjacentFamilies: family.adjacentFamilies
            };
        }
    }

    return null;
}

/**
 * Calculate Role Family Affinity bonus
 * Returns a bonus score (0-40) based on how related the roles are
 */
function calculateRoleFamilyAffinity(userHeadline, targetHeadline) {
    const userRole = detectRoleFamily(userHeadline);
    const targetRole = detectRoleFamily(targetHeadline);

    // If we can't detect either role, no bonus
    if (!userRole || !targetRole) {
        return { bonus: 0, reason: null };
    }

    let bonus = 0;
    let reason = '';

    // SAME FAMILY - Highest bonus
    if (userRole.family === targetRole.family) {
        bonus = 30;
        reason = `Same field (${targetRole.name})`;

        // Extra bonus if target is senior (mentorship potential)
        if (targetRole.isSenior && !userRole.isSenior) {
            bonus += 10;
            reason += ' + Senior (can mentor you)';
        }
        // Slight bonus for same level peers
        else if (targetRole.isSenior === userRole.isSenior) {
            bonus += 5;
            reason += ' + Peer (referrals & tips)';
        }
    }
    // ADJACENT FAMILY - Medium bonus
    else if (userRole.adjacentFamilies.includes(targetRole.family)) {
        bonus = 20;
        reason = `Related field (${targetRole.name})`;

        // Bonus if target is senior in adjacent field
        if (targetRole.isSenior) {
            bonus += 5;
            reason += ' + Senior';
        }
    }
    // HR/RECRUITING - Special case: always useful for job seekers
    else if (targetRole.family === 'HR_RECRUITING') {
        // Check if recruiter is in tech/data
        const targetLower = targetHeadline.toLowerCase();
        const recruitsForTech = ['tech', 'software', 'data', 'engineering', 'ml', 'ai'].some(k => targetLower.includes(k));

        if (recruitsForTech) {
            bonus = 25;
            reason = 'Tech Recruiter (can help you get hired!)';
        } else {
            bonus = 10;
            reason = 'Recruiter (may know opportunities)';
        }
    }

    return { bonus, reason };
}

/**
 * Get detailed role affinity breakdown for display
 */
function getRoleFamilyBreakdown(userHeadline, targetHeadline) {
    const userRole = detectRoleFamily(userHeadline);
    const targetRole = detectRoleFamily(targetHeadline);
    const affinity = calculateRoleFamilyAffinity(userHeadline, targetHeadline);

    return {
        userFamily: userRole ? userRole.name : 'Unknown',
        targetFamily: targetRole ? targetRole.name : 'Unknown',
        userIsSenior: userRole ? userRole.isSenior : false,
        targetIsSenior: targetRole ? targetRole.isSenior : false,
        bonus: affinity.bonus,
        reason: affinity.reason
    };
}

// Export for use in other scripts
if (typeof window !== 'undefined') {
    window.calculateRoleFamilyAffinity = calculateRoleFamilyAffinity;
    window.detectRoleFamily = detectRoleFamily;
    window.getRoleFamilyBreakdown = getRoleFamilyBreakdown;
    window.ROLE_FAMILIES = ROLE_FAMILIES;
}


/**
 * Calculate skill match score (overlap)
 */
function calculateSkillMatch(skillsA, skillsB) {
    if (!skillsA || !skillsB || skillsA.length === 0 || skillsB.length === 0) {
        return 50; // Default moderate match
    }

    // Normalize skills to lowercase for comparison
    const skillsANorm = skillsA.map(s => s.toLowerCase().trim());
    const skillsBNorm = skillsB.map(s => s.toLowerCase().trim());

    // Count exact matches
    const matches = skillsANorm.filter(skill => skillsBNorm.includes(skill));

    // Calculate Jaccard similarity
    const union = new Set([...skillsANorm, ...skillsBNorm]);
    const matchScore = (matches.length / union.size) * 100;

    return Math.min(100, Math.round(matchScore));
}

/**
 * Calculate skill complementarity (how unique skills complement)
 * Now considers if missing skills align with job roles
 */
function calculateSkillComplementarity(skillsA, skillsB, jobTitleA = '', jobTitleB = '') {
    if (!skillsA || !skillsB || skillsA.length === 0 || skillsB.length === 0) {
        return 40; // Low complementarity if no skills
    }

    const skillsANorm = skillsA.map(s => s.toLowerCase().trim());
    const skillsBNorm = skillsB.map(s => s.toLowerCase().trim());

    // Find unique skills each person has
    const uniqueA = skillsANorm.filter(skill => !skillsBNorm.includes(skill));
    const uniqueB = skillsBNorm.filter(skill => !skillsANorm.includes(skill));

    // Base complementarity: balance between overlap and uniqueness
    const totalSkills = skillsANorm.length + skillsBNorm.length;
    const uniqueSkills = uniqueA.length + uniqueB.length;
    let complementarityScore = (uniqueSkills / totalSkills) * 100;

    // Boost if there's a small overlap (good foundation)
    const overlap = calculateSkillMatch(skillsA, skillsB);
    const foundationBoost = overlap > 10 && overlap < 40 ? 10 : 0;
    complementarityScore += foundationBoost;

    // NEW: Job-skill relevance boost
    // Check if unique skills of B are relevant to A's job (and vice versa)
    const jobSkillBoost = calculateJobSkillRelevance(
        uniqueB, jobTitleA,  // B's skills → A's job
        uniqueA, jobTitleB   // A's skills → B's job
    );

    complementarityScore += jobSkillBoost;

    return Math.min(100, Math.round(complementarityScore));
}

/**
 * Calculate boost when one person's skills are relevant to the other's job role
 */
function calculateJobSkillRelevance(skillsB, jobTitleA, skillsA, jobTitleB) {
    // Define job role → relevant skill mappings
    const jobSkillMap = {
        // Technical Roles
        'software engineer': ['python', 'java', 'javascript', 'react', 'nodejs', 'aws', 'docker', 'kubernetes', 'git', 'sql', 'mongodb'],
        'data scientist': ['python', 'machine learning', 'tensorflow', 'pytorch', 'sql', 'statistics', 'r', 'data analysis', 'pandas', 'numpy'],
        'devops engineer': ['aws', 'docker', 'kubernetes', 'jenkins', 'terraform', 'ansible', 'linux', 'ci/cd', 'monitoring'],
        'frontend developer': ['javascript', 'react', 'vue', 'angular', 'html', 'css', 'typescript', 'webpack', 'sass'],
        'backend developer': ['python', 'java', 'nodejs', 'sql', 'mongodb', 'postgresql', 'redis', 'microservices', 'api design'],
        'mobile developer': ['swift', 'kotlin', 'react native', 'flutter', 'ios', 'android', 'mobile development'],

        // Business Roles
        'product manager': ['product strategy', 'roadmap', 'user research', 'data analysis', 'sql', 'jira', 'agile', 'stakeholder management'],
        'marketing manager': ['seo', 'sem', 'google analytics', 'content marketing', 'social media', 'email marketing', 'copywriting', 'brand strategy'],
        'sales manager': ['salesforce', 'crm', 'negotiation', 'business development', 'lead generation', 'sales strategy', 'pipeline management'],
        'project manager': ['agile', 'scrum', 'pmp', 'jira', 'project planning', 'risk management', 'budgeting', 'stakeholder management'],

        // Design Roles
        'ux designer': ['figma', 'sketch', 'user research', 'wireframing', 'prototyping', 'user testing', 'design systems'],
        'ui designer': ['figma', 'sketch', 'photoshop', 'illustrator', 'design systems', 'prototyping', 'visual design'],
        'graphic designer': ['photoshop', 'illustrator', 'indesign', 'branding', 'typography', 'logo design', 'creative direction'],

        // Other Roles
        'data analyst': ['sql', 'excel', 'tableau', 'power bi', 'python', 'data visualization', 'statistics'],
        'business analyst': ['sql', 'excel', 'requirements gathering', 'process mapping', 'stakeholder management', 'data analysis'],
        'consultant': ['strategy', 'business analysis', 'stakeholder management', 'presentation skills', 'excel', 'powerpoint']
    };

    let boost = 0;

    // Check if B's skills are relevant to A's job
    if (jobTitleA) {
        const jobA = jobTitleA.toLowerCase();
        for (const [role, relevantSkills] of Object.entries(jobSkillMap)) {
            if (jobA.includes(role)) {
                // Count how many of B's skills are relevant to A's job
                const relevantCount = skillsB.filter(skill =>
                    relevantSkills.some(relevantSkill => skill.includes(relevantSkill) || relevantSkill.includes(skill))
                ).length;

                if (relevantCount > 0) {
                    // Boost: 5 points per relevant skill, max 20 points from this direction
                    boost += Math.min(20, relevantCount * 5);
                }
                break;
            }
        }
    }

    // Check if A's skills are relevant to B's job
    if (jobTitleB) {
        const jobB = jobTitleB.toLowerCase();
        for (const [role, relevantSkills] of Object.entries(jobSkillMap)) {
            if (jobB.includes(role)) {
                const relevantCount = skillsA.filter(skill =>
                    relevantSkills.some(relevantSkill => skill.includes(relevantSkill) || relevantSkill.includes(skill))
                ).length;

                if (relevantCount > 0) {
                    boost += Math.min(20, relevantCount * 5);
                }
                break;
            }
        }
    }

    // Total boost capped at 30 points
    return Math.min(30, boost);
}

/**
 * Calculate career alignment (mentorship/learning potential)
 */
function calculateCareerAlignment(experienceYearsA, experienceYearsB) {
    const gap = Math.abs(experienceYearsA - experienceYearsB);

    // Perfect mentorship gap: 3-7 years
    if (gap >= 3 && gap <= 7) {
        return 90 + Math.random() * 10; // High alignment for mentorship
    }

    // Peer learning: 0-2 years
    if (gap <= 2) {
        return 75 + Math.random() * 15; // Good alignment for peers
    }

    // Large gap: still some value but less
    if (gap <= 10) {
        return 50 + Math.random() * 20;
    }

    // Very large gap
    return 30 + Math.random() * 15;
}

/**
 * Calculate industry match
 */
function calculateIndustryMatch(industryA, industryB) {
    // Exact match
    if (industryA === industryB) {
        return 90 + Math.random() * 10;
    }

    // Related industries
    const relatedIndustries = {
        'Technology': ['Finance', 'Marketing', 'Design'],
        'Finance': ['Technology', 'Consulting'],
        'Healthcare': ['Technology', 'Consulting'],
        'Marketing': ['Technology', 'Design', 'Sales'],
        'Sales': ['Marketing', 'Consulting'],
        'Design': ['Technology', 'Marketing'],
        'Consulting': ['Finance', 'Technology', 'Sales']
    };

    const related = relatedIndustries[industryA] || [];
    if (related.includes(industryB)) {
        return 60 + Math.random() * 20; // Related industry
    }

    // Different industries - still some cross-industry value
    return 30 + Math.random() * 20;
}

/**
 * Calculate geographic score (location proximity) - ENHANCED
 * Now considers remote work viability and timezone alignment
 */
function calculateGeographicScore(locationA, locationB) {
    if (!locationA || !locationB) return 50;

    const locA = locationA.toLowerCase();
    const locB = locationB.toLowerCase();

    // Exact city/region match
    if (locA === locB) {
        return 95; // Can meet in person for coffee chats
    }

    // Same metro area detection
    const metroAreas = {
        'san francisco': ['bay area', 'san jose', 'palo alto', 'mountain view', 'oakland'],
        'new york': ['nyc', 'manhattan', 'brooklyn', 'jersey city', 'hoboken'],
        'seattle': ['bellevue', 'redmond', 'kirkland'],
        'los angeles': ['la', 'santa monica', 'pasadena', 'burbank'],
        'boston': ['cambridge', 'somerville'],
        'chicago': ['evanston', 'oak park'],
        'bangalore': ['bengaluru', 'electronic city'],
        'hyderabad': ['hitec city', 'gachibowli'],
        'delhi': ['gurgaon', 'gurugram', 'noida', 'ncr']
    };

    for (const [metro, areas] of Object.entries(metroAreas)) {
        const inSameMetro = (locA.includes(metro) || areas.some(a => locA.includes(a))) &&
            (locB.includes(metro) || areas.some(a => locB.includes(a)));
        if (inSameMetro) {
            return 88; // Same metro = easy meetups
        }
    }

    // Same country detection
    const countries = {
        'united states': ['usa', 'u.s.', 'america'],
        'india': ['in'],
        'united kingdom': ['uk', 'england', 'london'],
        'canada': ['toronto', 'vancouver', 'montreal'],
        'germany': ['berlin', 'munich', 'frankfurt'],
        'australia': ['sydney', 'melbourne']
    };

    for (const [country, aliases] of Object.entries(countries)) {
        const inSameCountry = (locA.includes(country) || aliases.some(a => locA.includes(a))) &&
            (locB.includes(country) || aliases.some(a => locB.includes(a)));
        if (inSameCountry) {
            return 70; // Same country = same timezone, legal work auth
        }
    }

    // Tech hubs get bonus for remote work culture
    const techHubs = ['san francisco', 'new york', 'seattle', 'austin', 'boston',
        'bangalore', 'hyderabad', 'london', 'berlin', 'toronto'];
    const bothInTechHubs = techHubs.some(h => locA.includes(h)) &&
        techHubs.some(h => locB.includes(h));
    if (bothInTechHubs) {
        return 60; // Both in tech hubs = remote-friendly culture
    }

    // Different countries but remote possible
    return 45;
}

/**
 * Calculate seniority match - ENHANCED
 * Now considers mentorship value and peer networking benefits
 */
function calculateSeniorityMatch(seniorityA, seniorityB) {
    const levels = { 'entry': 0, 'mid': 1, 'senior': 2, 'executive': 3 };
    const levelA = levels[seniorityA] || 1;
    const levelB = levels[seniorityB] || 1;

    const diff = levelB - levelA; // Positive = target is more senior

    // Same level - peer networking (job referrals, interview tips)
    if (diff === 0) {
        return 85;
    }

    // Target is 1 level above - ideal mentorship
    if (diff === 1) {
        return 90; // They can mentor you AND refer you
    }

    // Target is 2 levels above - stretch networking
    if (diff === 2) {
        return 70; // Valuable but less likely to engage
    }

    // You are more senior than target
    if (diff === -1) {
        return 65; // You can mentor them (reverse value)
    }

    if (diff === -2) {
        return 50;
    }

    // 3+ levels apart
    return 40;
}

/**
 * NEW: Calculate comprehensive network value with scenarios
 * Returns score and detailed reasons for each component
 */
function calculateNetworkValueEnhanced(userProfile, targetProfile) {
    let totalScore = 0;
    const reasons = [];
    const breakdown = {};

    // ========== SCENARIO 1: REFERRAL POTENTIAL (0-30 points) ==========
    let referralScore = 0;

    // Check if target works at desirable company
    const headline = (targetProfile.headline || '').toLowerCase();
    const company = extractCompanyFromHeadline(targetProfile.headline || '');

    const topCompanies = {
        'faang': ['google', 'meta', 'amazon', 'apple', 'netflix', 'microsoft'],
        'unicorns': ['stripe', 'databricks', 'snowflake', 'openai', 'anthropic', 'figma'],
        'consulting': ['mckinsey', 'bain', 'bcg', 'deloitte', 'accenture', 'ey', 'pwc', 'kpmg'],
        'finance': ['goldman', 'jpmorgan', 'morgan stanley', 'citadel', 'two sigma']
    };

    for (const [tier, companies] of Object.entries(topCompanies)) {
        if (companies.some(c => headline.includes(c) || company.toLowerCase().includes(c))) {
            referralScore = 30;
            reasons.push(`Works at ${company} - high referral value!`);
            break;
        }
    }

    // Hiring manager or recruiter
    if (referralScore === 0) {
        if (headline.includes('hiring') || headline.includes('recruiter') ||
            headline.includes('talent acquisition') || headline.includes('hr ')) {
            referralScore = 25;
            reasons.push('Is a recruiter/hiring manager - direct access');
        } else if (headline.includes('manager') || headline.includes('director') ||
            headline.includes('lead')) {
            referralScore = 20;
            reasons.push('Is a manager - can refer and advocate');
        } else if (headline.includes('senior') || headline.includes('staff')) {
            referralScore = 15;
            reasons.push('Senior role - credible referral source');
        } else {
            referralScore = 10;
            reasons.push('Individual contributor - peer referral');
        }
    }

    totalScore += referralScore;
    breakdown.referral = referralScore;

    // ========== SCENARIO 2: MUTUAL CONNECTIONS (0-25 points) ==========
    let mutualScore = 0;

    // Note: Mutual connections are hard to extract from DOM
    // Using connection count as proxy for network overlap likelihood
    const targetConnections = targetProfile.connections || 100;
    const userConnections = userProfile.connections || 100;

    // Higher connections = higher chance of mutual overlap
    if (targetConnections >= 1000 && userConnections >= 500) {
        mutualScore = 20;
        reasons.push(`Large networks (${targetConnections}+ connections) - likely mutual overlap`);
    } else if (targetConnections >= 500) {
        mutualScore = 15;
        reasons.push(`Good network size (${targetConnections} connections)`);
    } else if (targetConnections >= 200) {
        mutualScore = 10;
        reasons.push('Moderate network size');
    } else {
        mutualScore = 5;
        reasons.push('Smaller network');
    }

    // Bonus if target follows user (from profile data if available)
    if (targetProfile.followsYou) {
        mutualScore += 5;
        reasons.push('Already follows you - warm connection');
    }

    totalScore += mutualScore;
    breakdown.networkSize = mutualScore;

    // ========== SCENARIO 3: INDUSTRY NETWORK ACCESS (0-25 points) ==========
    let industryNetworkScore = 0;

    const userIndustry = userProfile.industry || extractIndustry(userProfile);
    const targetIndustry = extractIndustry(targetProfile);

    // Same industry = access to relevant network
    if (userIndustry === targetIndustry) {
        industryNetworkScore = 25;
        reasons.push(`Same industry (${targetIndustry}) - relevant network access`);
    } else {
        // Related industries
        const relatedMap = {
            'Technology': ['Finance', 'Consulting', 'Marketing'],
            'Finance': ['Technology', 'Consulting'],
            'Consulting': ['Technology', 'Finance'],
            'Marketing': ['Technology', 'Design'],
            'Design': ['Technology', 'Marketing']
        };

        const related = relatedMap[userIndustry] || [];
        if (related.includes(targetIndustry)) {
            industryNetworkScore = 15;
            reasons.push(`Related industry (${targetIndustry}) - cross-industry opportunities`);
        } else {
            industryNetworkScore = 5;
            reasons.push('Different industry - limited network overlap');
        }
    }

    totalScore += industryNetworkScore;
    breakdown.industryAccess = industryNetworkScore;

    // ========== SCENARIO 4: ACTIVITY & ENGAGEMENT (0-20 points) ==========
    let engagementScore = 0;

    // Check if target has posts/activity
    const hasPosts = targetProfile.posts && targetProfile.posts.length > 0;
    const hasAbout = targetProfile.about && targetProfile.about.length > 100;
    const hasFeatured = targetProfile.featured && targetProfile.featured.length > 0;

    if (hasPosts) {
        engagementScore += 10;
        reasons.push('Active on LinkedIn - more likely to respond');
    }

    if (hasAbout) {
        engagementScore += 5;
        reasons.push('Detailed profile - engaged professional');
    }

    if (hasFeatured) {
        engagementScore += 5;
        reasons.push('Has featured content - thought leader');
    }

    if (engagementScore === 0) {
        engagementScore = 5;
        reasons.push('Basic profile activity');
    }

    totalScore += engagementScore;
    breakdown.engagement = engagementScore;

    return {
        score: Math.min(100, totalScore),
        breakdown,
        reasons,
        summary: generateNetworkSummary(breakdown, totalScore)
    };
}

/**
 * Extract company name from headline
 */
function extractCompanyFromHeadline(headline) {
    if (!headline) return '';

    // Pattern: "Role at Company" or "Role @ Company"
    const atMatch = headline.match(/(?:at|@)\s+([A-Za-z0-9\s&]+)/i);
    if (atMatch) {
        return atMatch[1].trim().split(/[|•·]/)[0].trim();
    }

    // Pattern: "Role, Company"
    const commaMatch = headline.match(/,\s+([A-Za-z0-9\s&]+)/);
    if (commaMatch) {
        return commaMatch[1].trim().split(/[|•·]/)[0].trim();
    }

    return '';
}

/**
 * Generate human-readable network summary
 */
function generateNetworkSummary(breakdown, totalScore) {
    if (totalScore >= 80) {
        return 'Excellent networking opportunity! Strong referral potential.';
    } else if (totalScore >= 60) {
        return 'Good connection - valuable for industry networking.';
    } else if (totalScore >= 40) {
        return 'Moderate value - consider for peer networking.';
    } else {
        return 'Limited direct networking value.';
    }
}

/**
 * Extract additional profile metadata for better matching
 */
function extractProfileMetadata(profileData) {
    return {
        industry: extractIndustry(profileData),
        location: extractLocation(profileData),
        experienceYears: estimateExperienceYears(profileData.experience || []),
        seniority: estimateSeniority(estimateExperienceYears(profileData.experience || []))
    };
}

// Export the new function for use in content.js
if (typeof window !== 'undefined') {
    window.calculateNetworkValueEnhanced = calculateNetworkValueEnhanced;
}
