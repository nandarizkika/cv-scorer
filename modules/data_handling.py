import pandas as pd
from typing import Dict, List, Tuple
import zipfile
import io
import streamlit as st

@st.cache_data
def calculate_weighted_score(scores: List[Dict]) -> float:
    """Calculate weighted overall score for a set of requirements"""
    weight_map = {"Low": 1, "Medium": 2, "High": 3}
    
    weighted_scores = []
    weights = []
    
    for score in scores:
        weight = weight_map[score["priority"]]
        # For boolean values, convert to percentage (0 -> 0%, 1 -> 100%)
        value = score["score"] * 100 if score['type'] == 'boolean' else score["score"]
        weighted_scores.append(value * weight)
        weights.append(weight)
    
    if sum(weights) == 0:
        return 0
    
    return sum(weighted_scores) / sum(weights)

@st.cache_data
def prepare_comparison_data(all_results: Dict) -> pd.DataFrame:
    """Prepare data for comparison view"""
    comparison_data = []
    for cv_name, scores in all_results.items():
        avg_score = calculate_weighted_score(scores)
        
        # Calculate met requirements
        met_boolean = sum(1 for score in scores 
                    if score['type'] == 'boolean' and score['score'] == 1)
        boolean_reqs = sum(1 for score in scores if score['type'] == 'boolean')
        
        high_scores = sum(1 for score in scores 
                    if score['type'] == 'score' and score['score'] >= 70)
        score_reqs = sum(1 for score in scores if score['type'] == 'score')
        
        comparison_data.append({
            "CV": cv_name,
            "Overall Score": f"{avg_score:.1f}%",
            "Met Requirements": f"{met_boolean}/{boolean_reqs} required" if boolean_reqs > 0 else "N/A",
            "High Scores": f"{high_scores}/{score_reqs} skills" if score_reqs > 0 else "N/A"
        })
    
    # Sort by score descending
    comparison_df = pd.DataFrame(comparison_data)
    if not comparison_df.empty:
        comparison_df = comparison_df.sort_values(
            by="Overall Score", 
            key=lambda x: x.str.rstrip('%').astype(float), 
            ascending=False
        )
        comparison_df.index = range(1, len(comparison_df) + 1)
    
    return comparison_df

@st.cache_data
def get_requirement_stats(scores: List[Dict]) -> Tuple[int, int, int, int, float]:
    """Calculate statistics about requirements"""
    boolean_reqs = sum(1 for score in scores if score['type'] == 'boolean')
    score_reqs = len(scores) - boolean_reqs
    
    # Calculate met boolean requirements
    met_boolean = sum(1 for score in scores 
                   if score['type'] == 'boolean' and score['score'] == 1)
    
    # Calculate high-scoring requirements
    high_scores = sum(1 for score in scores 
                    if score['type'] == 'score' and score['score'] >= 70)
    
    # Calculate average score for score-based requirements
    score_based_avg = 0
    if score_reqs > 0:
        score_based_avg = sum(score['score'] for score in scores 
                           if score['type'] == 'score') / score_reqs
    
    return boolean_reqs, met_boolean, score_reqs, high_scores, score_based_avg

@st.cache_data
def format_dataframe(scores: List[Dict]) -> pd.DataFrame:
    """Format scores data into a DataFrame with proper formatting"""
    df = pd.DataFrame(scores)
    if not df.empty:
        df['formatted_score'] = df.apply(
            lambda x: "Yes" if x['type'] == 'boolean' and x['score'] == 1 else 
                    "No" if x['type'] == 'boolean' else 
                    f"{x['score']:.1f}%",
            axis=1
        )
    
    return df

@st.cache_data
def get_pdfs_from_zip(zip_file) -> List[Tuple[str, io.BytesIO]]:
    """Extract PDF files from a ZIP archive"""
    pdf_files = []
    
    with zipfile.ZipFile(zip_file) as z:
        for filename in z.namelist():
            if filename.lower().endswith('.pdf'):
                with z.open(filename) as pdf_file:
                    # Convert to BytesIO for PdfReader
                    pdf_bytes = io.BytesIO(pdf_file.read())
                    pdf_files.append((filename, pdf_bytes))
    
    return pdf_files

def save_to_csv(comparison_df: pd.DataFrame) -> bytes:
    """Convert comparison dataframe to CSV bytes for download"""
    return comparison_df.to_csv(index=False).encode('utf-8')