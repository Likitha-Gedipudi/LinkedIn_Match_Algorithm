"""
Conversation starters generator for professional networking.
Generates personalized icebreakers based on profile compatibility.
"""

import pandas as pd
import random
from typing import Dict, Any, List, Tuple

from ..utils import get_logger

logger = get_logger()


class ConversationStarterGenerator:
    """
    Generate personalized conversation starters for connection requests.
    
    Creates 3 types of starters:
    - Questions (asking for advice/insights)
    - Introductions (warm, personalized intro)
    - Value propositions (what you can offer)
    """
    
    def __init__(self, config: Dict = None):
        """Initialize generator with config."""
        self.config = config or {}
        
        # Template categories
        self._load_templates()
    
    def _load_templates(self):
        """Load conversation starter templates."""
        
        # Question templates (asking for help/advice)
        self.question_templates = [
            "Hi {name}, I noticed you have {years} years of experience in {field}. I'm currently {situation}, and would love to learn from your experience. Would you be open to a quick chat?",
            "Hello {name}! I saw that you work at {company} as a {role}. I'm interested in {interest} and would appreciate any insights you could share. Do you have 15 minutes for a coffee chat?",
            "Hey {name}, your background in {skill1} and {skill2} is impressive. I'm working on {project} and could use advice from someone with your expertise. Mind if I pick your brain?",
            "{name}, I'm trying to break into {industry} and noticed you've been successful there. What would you say was the most important factor in your career growth?",
            "Hi {name}, I see we both have experience with {shared_skill}. I'm curious how you've applied it at {company}. Would you be willing to share your approach?",
        ]
        
        # Introduction templates (warm opening)
        self.introduction_templates = [
            "Hi {name}! I came across your profile and was impressed by your work in {field}. I'm a {my_role} working on {my_focus}, and thought we might have some interesting synergies. Would love to connect!",
            "Hello {name}, we seem to have similar backgrounds in {shared_interest}. I've been following developments in {topic} and would enjoy exchanging ideas with someone in your position.",
            "Hey {name}! Fellow {industry} professional here. I noticed we both care about {shared_goal}. I'd love to connect and potentially collaborate.",
            "{name}, I see you're at {company} - that's exciting! I'm working on something in the {industry} space and thought you might find it interesting. Open to connecting?",
            "Hi {name}, your experience with {skill} caught my eye. I think there might be valuable insights we could share given our complementary backgrounds.",
        ]
        
        # Value proposition templates (offering help)
        self.value_prop_templates = [
            "Hi {name}, I noticed you're {their_goal}. I have connections in {my_network} that might be helpful. Would you be interested in an intro?",
            "Hello {name}! I saw you need help with {their_need}. I've worked on {my_expertise} for {years} years and would be happy to share insights. Let's connect?",
            "{name}, I see you're looking to {their_goal}. I've been through that process and learned a lot. Happy to share what worked for me if you're interested.",
            "Hey {name}, your work in {their_field} is impressive. I could introduce you to some people in {industry} who might be valuable connections. Interested?",
            "Hi {name}, I noticed you're hiring for {role}. I know several talented {skill} professionals who might be a fit. Want me to send them your way?",
        ]
        
        # Mentorship-specific templates
        self.mentorship_templates = [
            "Hi {name}, I'm {years_junior} years into my career in {field} and would love to learn from someone with your experience. Would you be open to an occasional mentorship chat?",
            "{name}, your career trajectory from {early_role} to {current_role} is exactly the path I'm aiming for. Any chance you'd be willing to mentor someone earlier in their journey?",
            "Hello {name}! I'm looking for guidance as I {goal}, and your background makes you the perfect person to learn from. Would you consider being a mentor?",
        ]
        
        # Collaboration templates
        self.collaboration_templates = [
            "Hi {name}, I'm working on {project} and think your expertise in {their_skill} would be invaluable. Any interest in collaborating?",
            "{name}, I see you're passionate about {topic}. I'm building something in that space - want to discuss potential synergies?",
            "Hello {name}! Your {skill} skills + my {my_skill} experience could be a powerful combination. Open to exploring a collaboration?",
        ]
    
    def generate_starters(
        self,
        profile_a: pd.Series,
        profile_b: pd.Series,
        compatibility_features: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate 3 conversation starters for a profile pair.
        
        Args:
            profile_a: First profile (the one reaching out)
            profile_b: Second profile (the recipient)
            compatibility_features: Optional compatibility data
            
        Returns:
            Dictionary with 3 starters and metadata
        """
        # Determine relationship type
        relationship_type = self._determine_relationship_type(profile_a, profile_b)
        
        # Generate starters based on relationship
        starters = []
        
        if relationship_type == "mentorship":
            starters.append(self._generate_mentorship_starter(profile_a, profile_b))
            starters.append(self._generate_question_starter(profile_a, profile_b))
            starters.append(self._generate_introduction_starter(profile_a, profile_b))
        elif relationship_type == "peer":
            starters.append(self._generate_collaboration_starter(profile_a, profile_b))
            starters.append(self._generate_introduction_starter(profile_a, profile_b))
            starters.append(self._generate_value_prop_starter(profile_a, profile_b))
        elif relationship_type == "value_exchange":
            starters.append(self._generate_value_prop_starter(profile_a, profile_b))
            starters.append(self._generate_introduction_starter(profile_a, profile_b))
            starters.append(self._generate_question_starter(profile_a, profile_b))
        else:  # general
            starters.append(self._generate_introduction_starter(profile_a, profile_b))
            starters.append(self._generate_question_starter(profile_a, profile_b))
            starters.append(self._generate_value_prop_starter(profile_a, profile_b))
        
        # Calculate personalization scores
        personalization_scores = [
            self._calculate_personalization_score(starter, profile_a, profile_b)
            for starter in starters
        ]
        
        return {
            "starter_1": starters[0],
            "starter_2": starters[1],
            "starter_3": starters[2],
            "starter_1_type": self._get_starter_type(starters[0]),
            "starter_2_type": self._get_starter_type(starters[1]),
            "starter_3_type": self._get_starter_type(starters[2]),
            "avg_personalization_score": sum(personalization_scores) / 3,
            "relationship_type": relationship_type,
        }
    
    def _determine_relationship_type(self, profile_a: pd.Series, profile_b: pd.Series) -> str:
        """Determine the type of professional relationship."""
        years_a = profile_a.get("years_experience", 0)
        years_b = profile_b.get("years_experience", 0)
        
        experience_gap = abs(years_a - years_b)
        
        # Mentorship relationship
        if experience_gap >= 5:
            return "mentorship"
        
        # Peer relationship
        if experience_gap <= 2:
            # Check if they have complementary skills
            needs_a = set(profile_a.get("needs", []))
            can_offer_b = set(profile_b.get("can_offer", []))
            
            if needs_a and can_offer_b and needs_a.intersection(can_offer_b):
                return "value_exchange"
            
            return "peer"
        
        # Value exchange
        return "value_exchange"
    
    def _generate_question_starter(self, profile_a: pd.Series, profile_b: pd.Series) -> str:
        """Generate a question-based starter."""
        template = random.choice(self.question_templates)
        
        # Get profile data
        name = profile_b.get("name", "there").split()[0]
        years_b = profile_b.get("years_experience", 5)
        role_b = profile_b.get("current_role", "your role")
        company_b = profile_b.get("current_company", "your company")
        industry_b = profile_b.get("industry", "the industry")
        
        # Get skills
        skills_b = profile_b.get("skills", [])
        skill1 = skills_b[0] if len(skills_b) > 0 else "your expertise"
        skill2 = skills_b[1] if len(skills_b) > 1 else "your skills"
        
        # Find shared skills
        skills_a = set(profile_a.get("skills", []))
        shared_skills = list(skills_a.intersection(set(skills_b)))
        shared_skill = shared_skills[0] if shared_skills else skill1
        
        # Get goals from profile A
        goals_a = profile_a.get("goals", [])
        situation = goals_a[0] if goals_a else "growing my career"
        
        # Fill template
        starter = template.format(
            name=name,
            years=years_b,
            field=industry_b,
            situation=situation,
            company=company_b,
            role=role_b,
            interest=industry_b,
            skill1=skill1,
            skill2=skill2,
            shared_skill=shared_skill,
            project=f"projects in {industry_b}",
            industry=industry_b
        )
        
        return starter
    
    def _generate_introduction_starter(self, profile_a: pd.Series, profile_b: pd.Series) -> str:
        """Generate an introduction-based starter."""
        template = random.choice(self.introduction_templates)
        
        name = profile_b.get("name", "there").split()[0]
        industry_b = profile_b.get("industry", "the industry")
        company_b = profile_b.get("current_company", "your company")
        
        # Get profile A data
        role_a = profile_a.get("current_role", "professional")
        industry_a = profile_a.get("industry", "the industry")
        
        # Find shared interests
        skills_a = set(profile_a.get("skills", []))
        skills_b = set(profile_b.get("skills", []))
        shared_skills = list(skills_a.intersection(skills_b))
        shared_interest = shared_skills[0] if shared_skills else industry_b
        
        goals_a = profile_a.get("goals", [])
        my_focus = goals_a[0] if goals_a else f"advancing in {industry_a}"
        
        starter = template.format(
            name=name,
            field=industry_b,
            my_role=role_a,
            my_focus=my_focus,
            shared_interest=shared_interest,
            topic=shared_interest,
            industry=industry_a,
            shared_goal=shared_interest,
            company=company_b,
            skill=shared_interest
        )
        
        return starter
    
    def _generate_value_prop_starter(self, profile_a: pd.Series, profile_b: pd.Series) -> str:
        """Generate a value proposition starter."""
        template = random.choice(self.value_prop_templates)
        
        name = profile_b.get("name", "there").split()[0]
        
        # What can A offer to B?
        needs_b = profile_b.get("needs", [])
        can_offer_a = profile_a.get("can_offer", [])
        
        their_need = needs_b[0] if needs_b else "growing your network"
        their_goal = needs_b[0] if needs_b else "advance your career"
        
        my_expertise = can_offer_a[0] if can_offer_a else "my field"
        my_network = profile_a.get("industry", "my industry")
        
        years_a = profile_a.get("years_experience", 5)
        role_b = profile_b.get("current_role", "a role")
        skills_a = profile_a.get("skills", [])
        skill_a = skills_a[0] if skills_a else "skilled professionals"
        
        industry_a = profile_a.get("industry", "the industry")
        their_field = profile_b.get("industry", "your field")
        
        starter = template.format(
            name=name,
            their_goal=their_goal,
            my_network=my_network,
            their_need=their_need,
            my_expertise=my_expertise,
            years=years_a,
            their_field=their_field,
            industry=industry_a,
            role=role_b,
            skill=skill_a
        )
        
        return starter
    
    def _generate_mentorship_starter(self, profile_a: pd.Series, profile_b: pd.Series) -> str:
        """Generate a mentorship request starter."""
        template = random.choice(self.mentorship_templates)
        
        name = profile_b.get("name", "there").split()[0]
        years_a = profile_a.get("years_experience", 3)
        years_b = profile_b.get("years_experience", 10)
        
        field = profile_a.get("industry", "the industry")
        current_role_b = profile_b.get("current_role", "senior role")
        
        goals_a = profile_a.get("goals", [])
        goal = goals_a[0] if goals_a else "grow in my career"
        
        starter = template.format(
            name=name,
            years_junior=years_a,
            field=field,
            early_role="early career",
            current_role=current_role_b,
            goal=goal
        )
        
        return starter
    
    def _generate_collaboration_starter(self, profile_a: pd.Series, profile_b: pd.Series) -> str:
        """Generate a collaboration proposal starter."""
        template = random.choice(self.collaboration_templates)
        
        name = profile_b.get("name", "there").split()[0]
        
        skills_a = profile_a.get("skills", [])
        skills_b = profile_b.get("skills", [])
        
        my_skill = skills_a[0] if skills_a else "my expertise"
        their_skill = skills_b[0] if skills_b else "your expertise"
        
        goals_a = profile_a.get("goals", [])
        project = goals_a[0] if goals_a else "an exciting project"
        
        # Find shared interests
        skills_set_a = set(skills_a)
        skills_set_b = set(skills_b)
        shared = list(skills_set_a.intersection(skills_set_b))
        topic = shared[0] if shared else their_skill
        
        starter = template.format(
            name=name,
            project=project,
            their_skill=their_skill,
            topic=topic,
            skill=their_skill,
            my_skill=my_skill
        )
        
        return starter
    
    def _calculate_personalization_score(
        self,
        starter: str,
        profile_a: pd.Series,
        profile_b: pd.Series
    ) -> float:
        """
        Calculate how personalized a starter is (0-100).
        
        Higher score = more specific details from profiles
        """
        score = 50.0  # Base score
        
        # Check for specific profile elements
        name_b = profile_b.get("name", "").split()[0]
        if name_b.lower() in starter.lower():
            score += 15
        
        company_b = profile_b.get("current_company", "")
        if company_b and company_b.lower() in starter.lower():
            score += 10
        
        industry_b = profile_b.get("industry", "")
        if industry_b and industry_b.lower() in starter.lower():
            score += 10
        
        # Check for skills mentioned
        skills_b = profile_b.get("skills", [])
        skill_mentioned = any(skill.lower() in starter.lower() for skill in skills_b[:3])
        if skill_mentioned:
            score += 15
        
        return min(100, score)
    
    def _get_starter_type(self, starter: str) -> str:
        """Determine the type of starter based on content."""
        starter_lower = starter.lower()
        
        if any(word in starter_lower for word in ["would love to learn", "advice", "insights", "curious"]):
            return "question"
        elif any(word in starter_lower for word in ["introduce", "help with", "connections in", "know several"]):
            return "value_proposition"
        elif any(word in starter_lower for word in ["mentor", "mentorship", "guidance"]):
            return "mentorship_request"
        elif any(word in starter_lower for word in ["collaborate", "synergies", "working on"]):
            return "collaboration"
        else:
            return "introduction"
    
    def batch_generate(
        self,
        pairs_df: pd.DataFrame,
        profiles_df: pd.DataFrame,
        min_compatibility_score: float = 60.0
    ) -> pd.DataFrame:
        """
        Generate conversation starters for a batch of profile pairs.
        
        Args:
            pairs_df: DataFrame of compatibility pairs
            profiles_df: DataFrame of all profiles
            min_compatibility_score: Only generate for pairs above this score
            
        Returns:
            DataFrame with conversation starters
        """
        logger.info(f"Generating conversation starters for high-value pairs (score >= {min_compatibility_score})...")
        
        # Filter for high-value pairs
        high_value_pairs = pairs_df[pairs_df["compatibility_score"] >= min_compatibility_score].copy()
        
        logger.info(f"Found {len(high_value_pairs)} high-value pairs")
        
        # Create profile lookup
        profile_lookup = profiles_df.set_index("profile_id")
        
        # Generate starters
        starters_data = []
        for idx, pair in high_value_pairs.iterrows():
            profile_a_id = pair["profile_a_id"]
            profile_b_id = pair["profile_b_id"]
            
            if profile_a_id not in profile_lookup.index or profile_b_id not in profile_lookup.index:
                continue
            
            profile_a = profile_lookup.loc[profile_a_id]
            profile_b = profile_lookup.loc[profile_b_id]
            
            starters = self.generate_starters(profile_a, profile_b)
            starters["pair_id"] = pair.get("pair_id", f"{profile_a_id}_{profile_b_id}")
            starters["profile_a_id"] = profile_a_id
            starters["profile_b_id"] = profile_b_id
            starters["compatibility_score"] = pair["compatibility_score"]
            
            starters_data.append(starters)
        
        result_df = pd.DataFrame(starters_data)
        
        logger.info(f"Generated {len(result_df)} conversation starter sets")
        
        return result_df


def generate_conversation_starters(
    pairs_df: pd.DataFrame,
    profiles_df: pd.DataFrame,
    min_compatibility_score: float = 60.0,
    config: Dict = None
) -> pd.DataFrame:
    """
    Convenience function to generate conversation starters.
    
    Args:
        pairs_df: DataFrame of compatibility pairs
        profiles_df: DataFrame of profiles
        min_compatibility_score: Minimum compatibility score to generate starters
        config: Optional configuration
        
    Returns:
        DataFrame with conversation starters
    """
    generator = ConversationStarterGenerator(config)
    return generator.batch_generate(pairs_df, profiles_df, min_compatibility_score)
