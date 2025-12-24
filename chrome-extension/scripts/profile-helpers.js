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
 * Calculate geographic score (location proximity)
 */
function calculateGeographicScore(locationA, locationB) {
    // Exact location match
    if (locationA === locationB) {
        return 90 + Math.random() * 10;
    }

    // Same country regions
    const sameCountry = (loc1, loc2) => {
        const countries = ['United States', 'United Kingdom', 'Canada', 'India', 'Germany', 'France', 'Australia'];
        for (const country of countries) {
            if (loc1.includes(country) && loc2.includes(country)) {
                return true;
            }
        }
        return false;
    };

    if (sameCountry(locationA, locationB)) {
        return 65 + Math.random() * 15; // Same country
    }

    // Remote work era - geography less important
    return 40 + Math.random() * 20;
}

/**
 * Calculate seniority match
 */
function calculateSeniorityMatch(seniorityA, seniorityB) {
    const levels = { 'entry': 0, 'mid': 1, 'senior': 2, 'executive': 3 };
    const levelA = levels[seniorityA] || 1;
    const levelB = levels[seniorityB] || 1;

    const diff = Math.abs(levelA - levelB);

    // Same level - peer networking
    if (diff === 0) {
        return 85 + Math.random() * 15;
    }

    // One level apart - mentorship potential
    if (diff === 1) {
        return 75 + Math.random() * 15;
    }

    // Two levels apart - still valuable
    if (diff === 2) {
        return 55 + Math.random() * 15;
    }

    // Three levels apart
    return 35 + Math.random() * 15;
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
