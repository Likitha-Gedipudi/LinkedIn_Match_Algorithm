"""
Configuration management system.
Loads and validates configuration from YAML files and environment variables.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings


class AppConfig(BaseModel):
    """Application configuration."""
    name: str
    version: str
    environment: str
    debug: bool = False
    log_level: str = "INFO"


class DatabaseConfig(BaseModel):
    """Database configuration."""
    
    class PostgresConfig(BaseModel):
        host: str = "localhost"
        port: int = 5432
        database: str = "linkedin_match"
        user: str = "postgres"
        password: str = ""
        pool_size: int = 10
        max_overflow: int = 20
        
        def get_url(self) -> str:
            """Get PostgreSQL connection URL."""
            return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    class RedisConfig(BaseModel):
        host: str = "localhost"
        port: int = 6379
        db: int = 0
        password: Optional[str] = None
        ttl: int = 3600
        
        def get_url(self) -> str:
            """Get Redis connection URL."""
            auth = f":{self.password}@" if self.password else ""
            return f"redis://{auth}{self.host}:{self.port}/{self.db}"
    
    postgres: PostgresConfig
    redis: RedisConfig


class ScraperConfig(BaseModel):
    """Scraper configuration."""
    
    class LinkedInConfig(BaseModel):
        enabled: bool = True
        rate_limit: int = 10
        max_profiles: int = 10000
        timeout: int = 30
        retry_attempts: int = 3
        retry_delay: int = 5
        use_proxy: bool = False
        proxy_list: list[str] = Field(default_factory=list)
        user_agents: list[str] = Field(default_factory=list)
        delay_between_requests: int = 2
        respect_robots_txt: bool = True
        public_only: bool = True
    
    class GitHubConfig(BaseModel):
        enabled: bool = True
        api_token: str = ""
        rate_limit: int = 30
        max_profiles: int = 5000
        timeout: int = 15
    
    class CompanyConfig(BaseModel):
        enabled: bool = True
        sources: list[str] = Field(default_factory=list)
        rate_limit: int = 20
        max_companies: int = 5000
    
    class JobConfig(BaseModel):
        enabled: bool = True
        sources: list[str] = Field(default_factory=list)
        rate_limit: int = 15
        max_postings: int = 10000
    
    linkedin: LinkedInConfig
    github: GitHubConfig
    companies: CompanyConfig
    jobs: JobConfig


class DataConfig(BaseModel):
    """Data processing configuration."""
    raw_data_path: str = "data/raw"
    processed_data_path: str = "data/processed"
    batch_size: int = 1000
    num_workers: int = 4
    validation_enabled: bool = True
    
    class ProfileConfig(BaseModel):
        min_fields_required: int = 5
        require_skills: bool = True
        require_experience: bool = True
        deduplication: bool = True
    
    class SyntheticConfig(BaseModel):
        enabled: bool = True
        generation_count: int = 10000
        quality_level: str = "high"
        seed: int = 42
    
    profiles: ProfileConfig
    synthetic: SyntheticConfig


class FeatureConfig(BaseModel):
    """Feature engineering configuration."""
    
    class SkillFeatures(BaseModel):
        skill_taxonomy: str = "data/taxonomies/skills.json"
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
        complementarity_weight: float = 0.40
    
    class NetworkFeatures(BaseModel):
        max_degrees: int = 3
        centrality_metrics: list[str] = Field(default_factory=list)
        network_value_weight: float = 0.30
    
    class CareerFeatures(BaseModel):
        experience_gap_optimal: int = 3
        same_industry_bonus: int = 10
        adjacent_industry_bonus: int = 5
        alignment_weight: float = 0.20
    
    class GeographicFeatures(BaseModel):
        same_city_bonus: int = 15
        same_region_bonus: int = 5
        remote_penalty: int = -5
        weight: float = 0.10
    
    skills: SkillFeatures
    network: NetworkFeatures
    career: CareerFeatures
    geographic: GeographicFeatures


class ModelConfig(BaseModel):
    """Model configuration."""
    
    class CompatibilityModel(BaseModel):
        model_type: str = "neural_network"
        architecture: Dict[str, Any] = Field(default_factory=dict)
        training: Dict[str, Any] = Field(default_factory=dict)
    
    class RankingModel(BaseModel):
        model_type: str = "learning_to_rank"
        algorithm: str = "lambdamart"
        num_trees: int = 500
        learning_rate: float = 0.1
    
    class RedFlagModel(BaseModel):
        model_type: str = "random_forest"
        n_estimators: int = 200
        max_depth: int = 15
    
    class HiddenGemModel(BaseModel):
        model_type: str = "isolation_forest"
        contamination: float = 0.1
    
    compatibility: CompatibilityModel
    ranking: RankingModel
    red_flags: RedFlagModel
    hidden_gems: HiddenGemModel
    save_path: str = "data/models"
    versioning: bool = True


class Config(BaseSettings):
    """Main configuration class."""
    
    app: AppConfig
    database: DatabaseConfig
    scrapers: ScraperConfig
    data: DataConfig
    features: FeatureConfig
    models: ModelConfig
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class ConfigLoader:
    """Configuration loader utility."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration loader.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path or self._find_config()
        self.config: Optional[Config] = None
    
    def _find_config(self) -> str:
        """Find configuration file in standard locations."""
        possible_paths = [
            "config/config.yaml",
            "config/config.yml",
            "../config/config.yaml",
            "../../config/config.yaml",
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                return path
        
        # Return example config if nothing found
        return "config/config.example.yaml"
    
    def load(self) -> Config:
        """Load configuration from file."""
        if self.config:
            return self.config
        
        config_file = Path(self.config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(config_file, 'r') as f:
            config_dict = yaml.safe_load(f)
        
        # Override with environment variables
        config_dict = self._override_with_env(config_dict)
        
        self.config = Config(**config_dict)
        return self.config
    
    def _override_with_env(self, config_dict: Dict) -> Dict:
        """Override configuration with environment variables."""
        # Example: LINKEDIN_MATCH_DATABASE_POSTGRES_PASSWORD
        prefix = "LINKEDIN_MATCH_"
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Remove prefix and convert to nested dict path
                config_key = key[len(prefix):].lower()
                keys = config_key.split('_')
                
                # Navigate to nested dict
                current = config_dict
                for k in keys[:-1]:
                    if k not in current:
                        current[k] = {}
                    current = current[k]
                
                # Set value
                current[keys[-1]] = value
        
        return config_dict
    
    def get_config(self) -> Config:
        """Get loaded configuration or load if not already loaded."""
        if not self.config:
            return self.load()
        return self.config


# Global configuration instance
_config_loader = ConfigLoader()


def get_config() -> Config:
    """Get global configuration instance."""
    return _config_loader.get_config()


def reload_config(config_path: Optional[str] = None):
    """Reload configuration from file."""
    global _config_loader
    _config_loader = ConfigLoader(config_path)
    return _config_loader.load()
