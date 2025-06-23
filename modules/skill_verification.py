import re
import json
import streamlit as st
from typing import Dict, List, Union
from openai import OpenAI

class SkillVerificationEngine:
    """
    Advanced skill verification system for comprehensive CV analysis
    """
    def __init__(self, client: OpenAI = None):
        """
        Initialize the Skill Verification Engine
        
        :param client: OpenAI client (optional)
        """
        self.client = client or OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
        # Load skill taxonomies and knowledge base
        self.skill_taxonomies = self._load_skill_taxonomies()
    
    def _load_skill_taxonomies(self) -> Dict:
        """
        Load predefined skill taxonomies and related knowledge
        
        :return: Dictionary of skill taxonomies
        """
        # This would typically be loaded from a comprehensive JSON file or database
        default_taxonomies = {
            "software_engineering": {
                "core_skills": [
                    "programming languages", 
                    "software design", 
                    "algorithms", 
                    "data structures"
                ],
                "advanced_skills": [
                    "system architecture", 
                    "distributed systems", 
                    "microservices"
                ]
            },
            "data_science": {
                "core_skills": [
                    "machine learning", 
                    "statistical analysis", 
                    "data visualization", 
                    "python", 
                    "r"
                ],
                "advanced_skills": [
                    "deep learning", 
                    "natural language processing", 
                    "computer vision"
                ]
            }
        }
        return default_taxonomies
    
    def decompose_skill(self, skill_requirement: str) -> List[str]:
        """
        Break down a skill requirement into its core components
        
        :param skill_requirement: Original skill requirement
        :return: List of skill components
        """
        try:
            decomposition_prompt = f"""
            Decompose the following skill requirement into its most specific, 
            measurable components. Provide a JSON list of these components.
            
            Skill Requirement: {skill_requirement}
            
            Guidelines:
            - Break down into specific, observable skills
            - Include both broad and specific aspects
            - Focus on actionable, verifiable components
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert in skill decomposition and analysis."},
                    {"role": "user", "content": decomposition_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            # Parse the JSON response
            components = json.loads(response.choices[0].message.content)
            return components
        except Exception as e:
            # Fallback decomposition
            return [skill_requirement]
    
    def verify_skill_depth(self, skill_components: List[str], cv_text: str) -> Dict[str, float]:
        """
        Verify the depth and authenticity of each skill component
        
        :param skill_components: List of skill components to verify
        :param cv_text: Full CV text
        :return: Dictionary of skill components with verification scores
        """
        skill_verification_results = {}
        
        for component in skill_components:
            verification_prompt = f"""
            Analyze the following skill component in the context of the entire CV:
            
            Skill Component: {component}
            CV Context:
            {cv_text[:6000]}  # Limit context to avoid token limits
            
            Provide a detailed assessment:
            1. Presence of the skill (0-100%)
            2. Evidence of practical application
            3. Level of demonstrated expertise
            4. Credibility of skill claims
            
            Respond with a JSON object containing:
            - score: Numeric score (0-100)
            - confidence: Numeric confidence level (0-1)
            - rationale: Brief explanation of the assessment
            """
            
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an expert CV analyzer and skill verification specialist."},
                        {"role": "user", "content": verification_prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                
                # Parse the verification result
                verification = json.loads(response.choices[0].message.content)
                skill_verification_results[component] = verification
            
            except Exception as e:
                # Fallback verification
                skill_verification_results[component] = {
                    "score": self._basic_skill_check(component, cv_text),
                    "confidence": 0.5,
                    "rationale": "Basic verification due to AI processing error"
                }
        
        return skill_verification_results
    
    def _basic_skill_check(self, skill: str, cv_text: str) -> float:
        """
        Basic skill verification using regex and text matching
        
        :param skill: Skill to check
        :param cv_text: CV text
        :return: Skill presence score (0-100)
        """
        # Convert skill to search pattern
        pattern = re.compile(re.escape(skill), re.IGNORECASE)
        
        # Multiple scoring factors
        factors = [
            # Direct mention score
            50 if pattern.search(cv_text) else 0,
            
            # Context-aware scoring
            20 if any(context in cv_text.lower() for context in [
                "experience", "worked", "project", "developed", "implemented"
            ]) else 0,
            
            # Word proximity bonus
            10 if len(re.findall(pattern, cv_text)) > 1 else 0,
            
            # Related terms bonus
            10 if any(related in cv_text.lower() for related in [
                "expertise", "specialized", "proficient"
            ]) else 0
        ]
        
        return min(sum(factors), 100)
    
    def aggregate_skill_verification(self, verification_results: Dict) -> float:
        """
        Aggregate skill verification results into a final skill score
        
        :param verification_results: Detailed skill verification results
        :return: Aggregate skill score (0-100)
        """
        if not verification_results:
            return 0
        
        # Weighted scoring
        total_weighted_score = 0
        total_weight = 0
        
        for component, result in verification_results.items():
            # Components with higher confidence get more weight
            weight = result.get('confidence', 0.5)
            score = result.get('score', 0)
            
            total_weighted_score += score * weight
            total_weight += weight
        
        # Prevent division by zero
        return total_weighted_score / total_weight if total_weight > 0 else 0
    
    def comprehensive_skill_verification(
        self, 
        requirement: Dict, 
        cv_text: str
    ) -> Dict[str, Union[float, Dict]]:
        """
        Comprehensive skill verification pipeline
        
        :param requirement: Requirement dictionary
        :param cv_text: Full CV text
        :return: Comprehensive skill verification results
        """
        # Decompose the skill requirement
        skill_components = self.decompose_skill(requirement['text'])
        
        # Verify skill depth for each component
        verification_results = self.verify_skill_depth(skill_components, cv_text)
        
        # Aggregate verification results
        aggregate_score = self.aggregate_skill_verification(verification_results)
        
        return {
            "score": aggregate_score,
            "detailed_verification": verification_results,
            "requirement": requirement['text']
        }

# Example usage in AI scoring
def enhanced_skill_scoring(requirement: Dict, cv_text: str) -> float:
    """
    Enhanced skill scoring using comprehensive verification
    
    :param requirement: Requirement dictionary
    :param cv_text: Full CV text
    :return: Enhanced skill score
    """
    # Initialize verification engine
    verification_engine = SkillVerificationEngine()
    
    # Perform comprehensive skill verification
    verification_result = verification_engine.comprehensive_skill_verification(
        requirement, cv_text
    )
    
    # Return the verified skill score
    return verification_result['score']