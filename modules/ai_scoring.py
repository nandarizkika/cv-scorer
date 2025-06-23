import streamlit as st
from openai import OpenAI
import re
from typing import Dict
import hashlib

# Initialize client with API key
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def ensure_cache_exists():
    """Ensure the score_cache exists in session state"""
    if 'score_cache' not in st.session_state:
        st.session_state.score_cache = {}

# Initialize cache immediately
ensure_cache_exists()

def get_cache_key(requirement: Dict, cv_text: str, model: str = "gpt-4o-mini") -> str:
    """Generate a unique cache key for a requirement/CV/model combination"""
    # Make sure cache exists
    ensure_cache_exists()
    
    # Create a string with the relevant data
    cache_str = f"{model}:{requirement['text']}:{requirement['type']}:{requirement['weight']}:{cv_text[:1000]}"
    # Hash it for a compact key
    return hashlib.md5(cache_str.encode()).hexdigest()


def format_score(score_data):
    """Format score based on type"""
    if score_data['type'] == 'boolean':
        return 'Yes' if score_data['score'] == 1 else 'No'
    else:
        return f"{score_data['score']:.1f}%"

def get_openai_score(requirement: Dict, cv_text: str) -> float:
    """Get score for a requirement using OpenAI API"""

    # Make sure cache exists
    ensure_cache_exists()

    cache_key = get_cache_key(requirement, cv_text)
    if cache_key in st.session_state.score_cache:
        return st.session_state.score_cache[cache_key]

    prompt = f"""
    Based on the following job requirement and CV content, provide a score.
    
    Requirement: {requirement['text']}
    Scoring Type: {'Boolean (0 or 1)' if requirement['type'] == 'boolean' else 'Score (0-100)'}
    Priority: {requirement['weight']}
    
    CV Content:
    {cv_text[:8000]}  # Limiting CV content length for API
    
    Please analyze if the CV meets this requirement.
    If scoring type is Boolean, respond with either 0 or 1.
    If scoring type is Score, provide a score from 0 to 100.
    Only respond with the numeric score, nothing else.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a CV analysis expert. Provide only numeric scores based on how well a CV matches given requirements."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
        )    
        
        score = float(response.choices[0].message.content.strip())
        if requirement['type'] == 'boolean':
            score = min(1, max(0, round(score)))
        else:
            score = min(100, max(0, score))
        
        st.session_state.score_cache[cache_key] = score
        return score
    
    except ValueError:
        return 0
    
    except Exception as e:
        st.error(f"Error with OpenAI API: {str(e)}")
        return 0

def get_openai_score_with_voting(requirement: Dict, cv_text: str) -> float:
    """Get score for a requirement using multiple OpenAI models (voting system)"""

    # Make sure cache exists
    ensure_cache_exists()

    models = ["gpt-4o", "gpt-4o-mini", "gpt-4o-2024-11-20"]
    results = []
    
    prompt = f"""
    Based on the following job requirement and CV content, provide a score.
    
    Requirement: {requirement['text']}
    Scoring Type: {'Boolean (0 or 1)' if requirement['type'] == 'boolean' else 'Score (0-100)'}
    Priority: {requirement['weight']}
    
    CV Content:
    {cv_text[:8000]}  # Limiting CV content length for API
    
    Please analyze if the CV meets this requirement.
    If scoring type is Boolean, respond with either 0 or 1.
    If scoring type is Score, provide a score from 0 to 100.
    Only respond with the numeric score, nothing else.
    Do not include words like 'Score:' or any other text.
    """
    
    voting_cache_key = get_cache_key(requirement, cv_text, "voting")
    if voting_cache_key in st.session_state.score_cache:
        return st.session_state.score_cache[voting_cache_key]    


    for model in models:

        model_cache_key = get_cache_key(requirement, cv_text, model)
        if model_cache_key in st.session_state.score_cache:
            results.append(st.session_state.score_cache[model_cache_key])
            continue

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a CV analysis expert. Your job is to provide ONLY a numeric score based on how well a CV matches given requirements with no additional text or explanation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
            )

            # Get the raw response
            raw_response = response.choices[0].message.content.strip()

            number_match = re.search(r'\d+', raw_response)
            if number_match:
                score = float(number_match.group())
                
                if requirement['type'] == 'boolean':
                    score = min(1, max(0, round(score)))  # Ensure it's 0 or 1
                else:
                    score = min(100, max(0, score))  # Ensure score is between 0 and 100
                    
                st.session_state.score_cache[model_cache_key] = score
                results.append(score)


            else:
                st.warning(f"Model {model} returned invalid response: {raw_response}")
                score = 0 if requirement['type'] == 'boolean' else 50
                results.append(score)

        except Exception as e:
            st.error(f"Error with model {model}: {str(e)}")
            score = 0 if requirement['type'] == 'boolean' else 50
            results.append(score)
    
    # Determine final score based on type
    if requirement['type'] == 'boolean':
        # Use mode (most common value) for boolean
        ones = results.count(1)
        zeros = results.count(0)
        final_score = 1 if ones > zeros else 0

    else:
        # Use median for score
        results.sort()
        if len(results) % 2 == 0:
            final_score = (results[len(results)//2 - 1] + results[len(results)//2]) / 2
        else:
            final_score = results[len(results)//2]


    st.session_state.score_cache[voting_cache_key] = final_score
    return final_score


def generate_ai_summary(scores, avg_score, format_score_func):
    """Generate an AI summary for a CV"""
    # Use cache if available
    cache_key = f"summary_{str(scores)}_{avg_score}"
    cache_key = hashlib.md5(cache_key.encode()).hexdigest()
    
    if cache_key in st.session_state.score_cache:
        return st.session_state.score_cache[cache_key]
        
    summary_prompt = f"""
    Based on the following CV screening results, provide a brief 2-3 sentence summary of the candidate's fit for the position.
    
    Overall Score: {avg_score:.1f}%
    
    Requirements and Scores:
    {', '.join([f"{score['requirement']}: {format_score_func(score)}" for score in scores])}
    
    Focus on:
    1. Key strengths
    2. Notable gaps
    3. Overall recommendation
    
    Keep it concise and professional.
    """
    
    try:
        summary_response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using gpt-4o for better summaries
            messages=[
                {"role": "system", "content": "You are a professional HR analyst providing concise candidate assessments."},
                {"role": "user", "content": summary_prompt}
            ],
            temperature=0.7,
        )
        
        summary = summary_response.choices[0].message.content
        st.session_state.score_cache[cache_key] = summary
        return summary
    
    except Exception as e:
        return f"Unable to generate summary: {str(e)}"


def generate_interview_questions(scores, avg_score, cv_text):
    """Generate interview questions based on CV and scores"""
    # Use cache if available
    cache_key = f"interview_questions_{str(scores)}_{avg_score}"
    cache_key = hashlib.md5(cache_key.encode()).hexdigest()
    
    if cache_key in st.session_state.score_cache:
        return st.session_state.score_cache[cache_key]
    
    # Prepare requirements context
    requirements_context = ', '.join([
        f"{score['requirement']} (Priority: {score['priority']})" 
        for score in scores
    ])
    
    # Prompt for generating interview questions with the specific format requested
    interview_prompt = f"""
    Based on the following CV details and job requirements, generate a list of targeted interview questions:

    Job Requirements:
    {requirements_context}

    Overall Candidate Score: {avg_score:.1f}%

    CV Context:
    {cv_text[:4000]}  # Limit CV context to avoid excessive token usage

    Please generate 5-7 specific interview questions formatted exactly as follows:

    1. [Skill Area Assessment]:
    • [Detailed question about this skill area]

    2. [Next Skill Area]:
    • [Detailed question about this skill area]

    For example:
    1. Programming Skills Assessment:
    • Can you describe a project where you used Python (or R) for data analysis? What libraries did you utilize and what challenges did you face during the implementation?

    2. Data Manipulation and Analysis:
    • In your experience with data manipulation using Pandas or NumPy, can you walk us through a specific instance where you had to clean and transform a complex dataset? What techniques did you employ to ensure data accuracy and integrity?

    Make sure each skill area has only one bullet point with a comprehensive question. Use the format "Number. Skill Area:" followed by a bullet point with the question.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert HR interviewer creating targeted, insightful interview questions. Follow the formatting instructions precisely."},
                {"role": "user", "content": interview_prompt}
            ],
            temperature=0.7,
        )
        
        interview_questions = response.choices[0].message.content
        
        # Cache the results
        st.session_state.score_cache[cache_key] = interview_questions
        return interview_questions
    
    except Exception as e:
        return f"Unable to generate interview questions: {str(e)}"

def generate_cv_questions(cv_text):
    """Generate personalized interview questions based on the candidate's CV"""
    # Create a cache key for CV-based questions
    cache_key = f"cv_questions_{cv_text[:1000]}"
    cache_key = hashlib.md5(cache_key.encode()).hexdigest()
    
    if cache_key in st.session_state.score_cache:
        return st.session_state.score_cache[cache_key]
    
    # Prompt for generating personalized CV questions
    cv_prompt = f"""
    Based on the candidate's CV below, generate 5 interview questions that are highly specific to this individual's background and experience.

    CV Content:
    {cv_text[:6000]}
    
    Create 5 numbered questions that:
    1. Reference specific details (exact role names, projects, technologies, achievements) from their CV
    2. Do not use placeholders like "[specific skill]" - always use actual names/details from the CV
    3. Are impossible to answer without having this specific person's experience
    
    Format your response exactly as:
    
    1. Question topic:
    • Specific question about their experience
    
    2. Question topic:
    • Specific question about their experience
    
    Each question should only have one bullet point. Make sure each question references actual details from their CV.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert interviewer creating personalized questions based on a candidate's CV. Always use specific details from their CV, never use placeholders like '[specific skill]'."},
                {"role": "user", "content": cv_prompt}
            ],
            temperature=0.7,
        )
        
        cv_questions = response.choices[0].message.content
        
        # Cache the results
        st.session_state.score_cache[cache_key] = cv_questions
        return cv_questions
    
    except Exception as e:
        return f"Unable to generate CV-based questions: {str(e)}"