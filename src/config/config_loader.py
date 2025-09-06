#!/usr/bin/env python3
"""
Configuration Loading System for PennyGPT
Handles consolidated personality profiles and validation
"""

import json
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class PersonalityProfile:
    """Structured personality profile data"""
    schema_version: str
    name: str
    version: str
    description: str
    
    core_traits: Dict[str, float]
    conversation_style: Dict[str, Any]
    safety: Dict[str, Any]
    unpredictable_enhancement: Dict[str, Any]
    voice_delivery: Dict[str, Any]
    conversation_memory: Dict[str, Any]
    metrics: Dict[str, Any]

class ConfigLoader:
    """Loads and validates PennyGPT configuration"""
    
    def __init__(self, base_config_path: str = "penny_config.json"):
        self.base_config_path = base_config_path
        self.base_config = None
        self.personality_profile = None
    
    def load_base_config(self) -> Dict[str, Any]:
        """Load the main configuration file"""
        try:
            with open(self.base_config_path, 'r') as f:
                self.base_config = json.load(f)
            return self.base_config
        except Exception as e:
            raise ConfigurationError(f"Failed to load base config: {e}")
    
    def load_personality_profile(self, profile_path: str = None) -> Optional[PersonalityProfile]:
        """Load personality profile from path or base config"""
        if not self.base_config:
            self.load_base_config()
        
        # Get profile path from config if not provided
        if not profile_path:
            personality_config = self.base_config.get('personality', {})
            profile_path = personality_config.get('profile_path')
        
        if not profile_path:
            return None
        
        try:
            with open(profile_path, 'r') as f:
                profile_data = json.load(f)
            
            # Validate schema version
            schema_version = profile_data.get('schema_version', '0.0.0')
            if not schema_version.startswith('1.'):
                print(f"⚠️ Warning: Personality schema version {schema_version} may not be compatible")
            
            # Create structured profile
            self.personality_profile = PersonalityProfile(
                schema_version=profile_data.get('schema_version', '1.0.0'),
                name=profile_data.get('name', 'Unknown'),
                version=profile_data.get('version', '1.0.0'),
                description=profile_data.get('description', ''),
                core_traits=profile_data.get('personality', {}).get('core_traits', {}),
                conversation_style=profile_data.get('personality', {}).get('conversation_style', {}),
                safety=profile_data.get('safety', {}),
                unpredictable_enhancement=profile_data.get('unpredictable_enhancement', {}),
                voice_delivery=profile_data.get('voice_delivery', {}),
                conversation_memory=profile_data.get('conversation_memory', {}),
                metrics=profile_data.get('metrics', {})
            )
            
            return self.personality_profile
            
        except Exception as e:
            raise ConfigurationError(f"Failed to load personality profile: {e}")
    
    def get_consolidated_config(self) -> Dict[str, Any]:
        """Get merged configuration with personality profile"""
        if not self.base_config:
            self.load_base_config()
        
        # Load personality profile if specified
        personality_config = self.base_config.get('personality', {})
        if personality_config.get('profile_path'):
            try:
                self.load_personality_profile()
            except ConfigurationError as e:
                print(f"⚠️ Warning: Could not load personality profile: {e}")
                print("   Continuing with default personality settings")
        
        return {
            'base': self.base_config,
            'personality': self.personality_profile
        }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate the complete configuration and return status"""
        issues = []
        warnings = []
        
        # Validate base config
        if not self.base_config:
            try:
                self.load_base_config()
            except Exception as e:
                issues.append(f"Base config invalid: {e}")
        
        # Validate personality profile if specified
        if self.base_config and 'personality' in self.base_config:
            personality_config = self.base_config['personality']
            if 'profile_path' in personality_config:
                try:
                    self.load_personality_profile()
                    if self.personality_profile:
                        # Check schema compatibility
                        if not self.personality_profile.schema_version.startswith('1.'):
                            warnings.append(f"Personality schema version {self.personality_profile.schema_version} may not be compatible")
                except Exception as e:
                    warnings.append(f"Personality profile could not be loaded: {e}")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'loaded_profile': self.personality_profile.name if self.personality_profile else None
        }

class ConfigurationError(Exception):
    """Configuration loading or validation error"""
    pass

def load_config(config_path: str = "penny_config.json") -> Dict[str, Any]:
    """Convenience function to load complete configuration"""
    loader = ConfigLoader(config_path)
    return loader.get_consolidated_config()

def validate_config(config_path: str = "penny_config.json") -> Dict[str, Any]:
    """Convenience function to validate configuration"""
    loader = ConfigLoader(config_path)
    return loader.validate_configuration()

if __name__ == "__main__":
    """Test configuration loading"""
    try:
        print("🔧 Testing Configuration Loading...")
        
        # Test validation
        validation = validate_config()
        print(f"✅ Configuration valid: {validation['valid']}")
        
        if validation['warnings']:
            for warning in validation['warnings']:
                print(f"⚠️ Warning: {warning}")
        
        if validation['issues']:
            for issue in validation['issues']:
                print(f"❌ Issue: {issue}")
        
        if validation['loaded_profile']:
            print(f"🎭 Loaded profile: {validation['loaded_profile']}")
        
        # Test loading
        config = load_config()
        print(f"📋 Base config keys: {list(config['base'].keys())}")
        if config['personality']:
            print(f"🎭 Personality: {config['personality'].name} v{config['personality'].version}")
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
