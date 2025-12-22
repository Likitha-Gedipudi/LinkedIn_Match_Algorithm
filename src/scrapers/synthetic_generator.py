"""
Synthetic professional profile generator.
Creates realistic fake profiles for dataset augmentation and testing.
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List

from faker import Faker

from ..utils import generate_id, get_logger

logger = get_logger()


class SyntheticProfileGenerator:
    """
    Generate synthetic professional profiles with realistic data.
    
    Uses Faker library + domain-specific logic to create believable profiles.
    """
    
    def __init__(self, seed: int = 42, quality_level: str = "high"):
        """
        Initialize generator.
        
        Args:
            seed: Random seed for reproducibility
            quality_level: Quality of generated data (low, medium, high)
        """
        self.seed = seed
        self.quality_level = quality_level
        self.fake = Faker()
        Faker.seed(seed)
        random.seed(seed)
        
        self._load_professional_data()
    
    def _load_professional_data(self):
        """Load realistic professional data for generation."""
        # Tech skills by category
        self.tech_skills = {
            "programming": [
                "Python", "JavaScript", "Java", "C++", "Go", "Rust", "TypeScript",
                "Ruby", "PHP", "Swift", "Kotlin", "C#", "Scala", "R"
            ],
            "web": [
                "React", "Vue.js", "Angular", "Node.js", "Django", "Flask",
                "FastAPI", "Express.js", "Next.js", "Svelte"
            ],
            "data": [
                "Machine Learning", "Data Science", "Deep Learning", "NLP",
                "Computer Vision", "TensorFlow", "PyTorch", "Scikit-learn",
                "Pandas", "NumPy", "SQL", "NoSQL", "Big Data", "Spark"
            ],
            "cloud": [
                "AWS", "Google Cloud", "Azure", "Docker", "Kubernetes",
                "Terraform", "CI/CD", "DevOps", "Microservices"
            ],
            "design": [
                "UI/UX Design", "Figma", "Sketch", "Adobe XD", "Photoshop",
                "Illustrator", "InVision", "Prototyping", "User Research"
            ],
            "business": [
                "Product Management", "Strategy", "Business Development",
                "Marketing", "Sales", "Operations", "Finance", "Analytics"
            ]
        }
        
        # Job titles by seniority
        self.job_titles = {
            "entry": [
                "Junior Developer", "Associate Consultant", "Analyst",
                "Coordinator", "Assistant"
            ],
            "mid": [
                "Software Engineer", "Product Manager", "Data Scientist",
                "Designer", "Marketing Manager", "Consultant"
            ],
            "senior": [
                "Senior Engineer", "Senior Product Manager", "Lead Data Scientist",
                "Senior Designer", "Director", "Principal Engineer"
            ],
            "executive": [
                "VP Engineering", "CTO", "CEO", "CFO", "COO",
                "Head of Product", "Chief Data Officer"
            ]
        }
        
        # Industries
        self.industries = [
            "Technology", "Finance", "Healthcare", "E-commerce", "Education",
            "Consulting", "Media", "Retail", "Manufacturing", "Real Estate",
            "Energy", "Transportation", "Telecommunications", "Entertainment"
        ]
        
        # Companies by stage
        self.companies = {
            "startup": ["TechVenture", "InnovateCo", "StartupX", "NewWave"],
            "scaleup": ["GrowthTech", "ScaleUp", "RapidGrow", "NextGen"],
            "enterprise": [
                "Google", "Microsoft", "Amazon", "Meta", "Apple",
                "Netflix", "Tesla", "Uber", "Airbnb", "Stripe"
            ]
        }
        
        # Universities
        self.universities = [
            "MIT", "Stanford", "Harvard", "Berkeley", "CMU",
            "Princeton", "Yale", "Columbia", "Penn", "Cornell",
            "UCLA", "USC", "Michigan", "Northwestern", "Duke"
        ]
    
    def generate_profile(self) -> Dict[str, Any]:
        """Generate a single synthetic profile with realistic distribution of types."""
        seniority = random.choice(["entry", "mid", "senior", "executive"])
        years_experience = self._get_years_for_seniority(seniority)
        
        # Determine profile archetype (85% normal, 10% red flag, 5% gem)
        archetype_roll = random.random()
        if archetype_roll < 0.10:
            # Red flag profile (10%)
            archetype = self._create_red_flag_archetype()
        elif archetype_roll < 0.15:
            # Hidden gem profile (5%)
            archetype = "gem"
        else:
            # Normal profile (85%)
            archetype = "normal"
        
        # Apply archetype characteristics
        is_job_hopper = archetype.get("is_job_hopper", False) if isinstance(archetype, dict) else False
        is_collector = archetype.get("is_collector", False) if isinstance(archetype, dict) else False
        is_ghost = archetype.get("is_ghost", False) if isinstance(archetype, dict) else False
        is_spam = archetype.get("is_spam", False) if isinstance(archetype, dict) else False
        is_gem = archetype == "gem"
        
        # Adjust skills based on profile type
        if is_ghost:
            skills = random.sample(list(self.tech_skills.values())[0], random.randint(1, 3))
        elif is_gem:
            # Gems have many valuable skills
            all_skills = []
            for category_skills in self.tech_skills.values():
                all_skills.extend(category_skills)
            num_skills = random.randint(15, 25)
            skills = random.sample(all_skills, min(num_skills, len(all_skills)))
        else:
            skills = self._generate_skills(seniority)
        
        # Adjust about section
        if is_ghost:
            about = random.choice(["Professional", "", "Open to opportunities"])
        elif is_spam:
            about = random.choice([
                "Financial freedom is possible! DM me to learn how.",
                "Build your network marketing empire. Message me for details.",
                "Work from home opportunity - unlimited income potential!"
            ])
        else:
            about = self._generate_about()
        
        # Adjust headline for spam profiles
        if is_spam:
            headline = random.choice([
                "Entrepreneur | Network Marketer | Financial Freedom",
                "Helping people achieve their dreams | MLM | DM me",
                "Business opportunity | Work from anywhere"
            ])
        elif is_ghost or is_collector:
            headline = random.choice(["Professional", "Consultant", "Expert", "Freelancer"])
        else:
            headline = self._generate_headline(seniority)
        
        # Adjust current role for ghost/collector profiles
        if is_collector or is_ghost:
            current_role = random.choice(["Consultant", "Freelancer", "Professional", "Entrepreneur"])
        else:
            current_role = random.choice(self.job_titles[seniority])
        
        # Generate basic info
        profile = {
            "profile_id": generate_id(self.fake.uuid4()),
            "name": self.fake.name(),
            "email": self.fake.email(),
            "location": f"{self.fake.city()}, {self.fake.state_abbr()}",
            "headline": headline,
            "about": about,
            "years_experience": years_experience,
            "seniority_level": seniority,
            "industry": random.choice(self.industries),
            "current_company": self._get_company(seniority),
            "current_role": current_role,
            "skills": skills,
            "experience": self._generate_experience(years_experience, seniority, is_job_hopper),
            "education": [] if is_ghost else self._generate_education(),
            "connections": self._generate_connections(seniority, is_collector, is_gem),
            "goals": self._generate_goals(seniority),
            "needs": self._generate_needs(seniority),
            "can_offer": self._generate_offerings(seniority),
            "remote_preference": random.choice(["remote", "hybrid", "onsite"]),
            "source": "synthetic",
            "generated_at": datetime.now().isoformat(),
            "profile_archetype": archetype if isinstance(archetype, str) else "red_flag",
        }
        
        return profile
    
    def _create_red_flag_archetype(self) -> Dict[str, bool]:
        """Create a red flag archetype with specific characteristics."""
        red_flag_types = [
            {"is_job_hopper": True, "is_collector": False, "is_ghost": False, "is_spam": False},
            {"is_job_hopper": False, "is_collector": True, "is_ghost": False, "is_spam": False},
            {"is_job_hopper": False, "is_collector": False, "is_ghost": True, "is_spam": False},
            {"is_job_hopper": False, "is_collector": False, "is_ghost": False, "is_spam": True},
        ]
        return random.choice(red_flag_types)
    
    def _get_years_for_seniority(self, seniority: str) -> int:
        """Get appropriate years of experience for seniority level."""
        ranges = {
            "entry": (0, 2),
            "mid": (3, 7),
            "senior": (8, 15),
            "executive": (15, 30)
        }
        min_years, max_years = ranges[seniority]
        return random.randint(min_years, max_years)
    
    def _generate_headline(self, seniority: str) -> str:
        """Generate realistic headline."""
        role = random.choice(self.job_titles[seniority])
        specialty = random.choice(["Tech", "Product", "Data", "Design", "Business"])
        return f"{role} | {specialty} | Building impactful solutions"
    
    def _generate_about(self) -> str:
        """Generate about section."""
        templates = [
            "Passionate about building innovative solutions and leading high-performing teams.",
            "Experienced professional focused on driving growth and delivering results.",
            "Technical leader with a track record of successful product launches.",
            "Creative problem solver dedicated to creating exceptional user experiences.",
            "Strategic thinker with expertise in scaling organizations and products.",
        ]
        return random.choice(templates)
    
    def _get_company(self, seniority: str) -> str:
        """Get appropriate company based on seniority."""
        if seniority in ["entry", "mid"]:
            stage = random.choice(["startup", "scaleup", "enterprise"])
        elif seniority == "senior":
            stage = random.choice(["scaleup", "enterprise"])
        else:
            stage = random.choice(["scaleup", "enterprise"])
        
        return random.choice(self.companies[stage])
    
    def _generate_skills(self, seniority: str) -> List[str]:
        """Generate relevant skills."""
        num_skills = {
            "entry": (5, 10),
            "mid": (10, 15),
            "senior": (15, 20),
            "executive": (15, 25)
        }
        
        min_skills, max_skills = num_skills[seniority]
        count = random.randint(min_skills, max_skills)
        
        # Select from multiple categories
        all_skills = []
        for category_skills in self.tech_skills.values():
            all_skills.extend(category_skills)
        
        return random.sample(all_skills, min(count, len(all_skills)))
    
    def _generate_experience(self, years: int, seniority: str, is_job_hopper: bool = False) -> List[Dict]:
        """Generate work experience."""
        if is_job_hopper:
            # Job hoppers have many short-term positions
            num_jobs = max(3, min(years // 1, 8))
        else:
            num_jobs = max(1, min(years // 3, 5))  # Average 3 years per job
        
        experience = []
        
        for i in range(num_jobs):
            if is_job_hopper:
                job_years = random.choice([0.3, 0.5, 0.8, 1.0])  # 4-12 months
                duration_months = int(job_years * 12)
            else:
                job_years = random.randint(1, 4)
                duration_months = job_years * 12
            
            experience.append({
                "title": random.choice(self.job_titles[seniority]),
                "company": self._get_company(seniority),
                "duration": f"{job_years} years" if not is_job_hopper else f"{duration_months} months",
                "duration_months": duration_months,
                "description": "Led team and delivered impactful projects"
            })
        
        return experience
    
    def _generate_education(self) -> List[Dict]:
        """Generate education history."""
        degrees = ["BS", "MS", "MBA", "PhD"]
        fields = [
            "Computer Science", "Engineering", "Business", "Data Science",
            "Design", "Economics", "Mathematics", "Physics"
        ]
        
        return [{
            "school": random.choice(self.universities),
            "degree": random.choice(degrees),
            "field": random.choice(fields),
            "years": "4 years"
        }]
    
    def _generate_connections(self, seniority: str, is_collector: bool = False, is_gem: bool = False) -> int:
        """Generate realistic connection count."""
        if is_collector:
            # Connection collectors have excessive connections
            return random.randint(5000, 15000)
        elif is_gem:
            # Hidden gems are undervalued - fewer connections than expected
            ranges = {
                "entry": (20, 150),
                "mid": (100, 400),
                "senior": (200, 800),
                "executive": (300, 1200)
            }
        else:
            ranges = {
                "entry": (50, 300),
                "mid": (300, 1000),
                "senior": (1000, 3000),
                "executive": (2000, 5000)
            }
        
        min_conn, max_conn = ranges[seniority]
        return random.randint(min_conn, max_conn)
    
    def _generate_goals(self, seniority: str) -> List[str]:
        """Generate professional goals."""
        goals_by_seniority = {
            "entry": ["Learn new skills", "Get promoted", "Build network"],
            "mid": ["Lead projects", "Mentor others", "Specialize"],
            "senior": ["Scale impact", "Strategic role", "Executive position"],
            "executive": ["Build company", "Exit strategy", "Advisory roles"]
        }
        return random.sample(goals_by_seniority[seniority], 2)
    
    def _generate_needs(self, seniority: str) -> List[str]:
        """Generate what the person needs."""
        needs_pool = [
            "funding", "hiring", "mentorship", "clients", "partnerships",
            "technical expertise", "business advice", "network connections",
            "career guidance", "job opportunities"
        ]
        return random.sample(needs_pool, 3)
    
    def _generate_offerings(self, seniority: str) -> List[str]:
        """Generate what the person can offer."""
        offerings_pool = [
            "technical mentorship", "career advice", "industry connections",
            "product feedback", "investment", "partnership opportunities",
            "hiring referrals", "consulting", "speaking opportunities"
        ]
        return random.sample(offerings_pool, 3)
    
    def generate_batch(self, count: int) -> List[Dict[str, Any]]:
        """
        Generate multiple profiles.
        
        Args:
            count: Number of profiles to generate
            
        Returns:
            List of profile dictionaries
        """
        logger.info(f"Generating {count} synthetic profiles...")
        
        profiles = []
        for i in range(count):
            if (i + 1) % 1000 == 0:
                logger.info(f"Generated {i + 1}/{count} profiles")
            
            profile = self.generate_profile()
            profiles.append(profile)
        
        logger.info(f"Successfully generated {len(profiles)} synthetic profiles")
        return profiles
