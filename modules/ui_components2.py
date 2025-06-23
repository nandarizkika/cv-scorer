import re
import streamlit as st
import pandas as pd
from typing import Dict, List
from modules.data_handling import calculate_weighted_score, get_requirement_stats, format_dataframe, prepare_comparison_data
from modules.ai_scoring import generate_ai_summary, generate_interview_questions, generate_cv_questions
from modules.requirement_templates import RequirementTemplateManager


def highlight_score(s):
    """Apply color highlighting to scores in dataframe"""
    if s.name == "Overall Score":
        return [
            'background-color: #d4f7d4' if float(x.strip('%')) >= 80 else
            'background-color: #d4e6f7' if float(x.strip('%')) >= 60 else
            'background-color: #f7ecd4' if float(x.strip('%')) >= 40 else
            'background-color: #f7d4d4' 
            for x in s
        ]
    else:
        return [''] * len(s)

def display_template_selection():
    """Display UI for selecting requirement templates"""
    # Initialize template manager
    template_manager = RequirementTemplateManager()
    
    # Positions with "Choose Role" as the first option
    positions = ["Choose Role"] + template_manager.get_template_positions()
    
    # Select position with "Choose Role" as default
    selected_position = st.selectbox(
        "Job Position", 
        positions, 
        index=0,  # Default to "Choose Role"
        key="job_position_template_select_unique",
        help="Select a role to load its predefined requirements template"
    )
    
    # If "Choose Role" is selected, show info and return
    if selected_position == "Choose Role":
        st.info("Select a role to view its template requirements")
        return
    
    # Get template requirements
    template_requirements = template_manager.get_template_requirements(selected_position)
    
    # Use This Template button
    if st.button("Use This Template", type="primary", key=f"use_template_{selected_position}"):
        # Clear existing requirements
        st.session_state.requirements = []
        
        # Add template requirements to session state
        for req in template_requirements:
            st.session_state.requirements.append({
                "text": req["text"],
                "weight": req["weight"],
                "type": req["type"]
            })
        st.success(f"{selected_position} template requirements added!")
    
    # Save Template section
    new_template_position = st.text_input("Save as New Template", key="new_template_input")
    
    if st.button("Save Template", key=f"save_template_{selected_position}"):
        if new_template_position:
            template_manager = RequirementTemplateManager()
            current_requirements = [
                {
                    "text": req["text"],
                    "weight": req["weight"],
                    "type": req["type"]
                } for req in st.session_state.requirements
            ]
            
            if template_manager.create_new_template(new_template_position, current_requirements):
                st.success(f"New template '{new_template_position}' created successfully!")
        else:
            st.warning("Please enter a name for the new template")

def create_requirement_ui():
    """Create and manage requirement UI elements in the sidebar"""
    # Initialize template manager
    template_manager = RequirementTemplateManager()
    
    # Get available positions
    positions = template_manager.get_template_positions()
    
    with st.expander("Add New Requirement", expanded=True):
        # New requirement input
        new_req = st.text_input("New Requirement")
        
        # Priority and Scoring Type in a single row
        col1, col2 = st.columns(2)
        with col1:
            new_weight = st.selectbox(
                "Priority",
                ["Low", "Medium", "High"]
            )
        
        with col2:
            new_type = st.selectbox(
                "Scoring Type",
                ["boolean", "score"],
                format_func=lambda x: "Boolean (0/1)" if x == "boolean" else "Score (0-100)"
            )
        
        # Buttons in a single row
        col1, col2 = st.columns([3, 1])
        
        with col2:
            if st.button("Add New", type="primary", use_container_width=True):
                if new_req:  # Only add if requirement text is not empty
                    st.session_state.requirements.append({
                        "text": new_req,
                        "weight": new_weight,
                        "type": new_type
                    })
                    st.rerun()
                else:
                    st.warning("Please enter a requirement text")
        
        # Template selection
        st.subheader("Select Template Requirements")
        selected_template = st.selectbox(
            "Choose a Role Template", 
            ["Choose Template"] + positions,
            index=0,
            help="Select a predefined template to load requirements"
        )
        
        # If a template is selected (not the default "Choose Template")
        if selected_template != "Choose Template":
            # Get template requirements
            template_requirements = template_manager.get_template_requirements(selected_template)
            
            # Display template requirements
            st.write(f"**{selected_template} Requirements Template:**")
            req_data = [
                {
                    'Requirement': req['text'], 
                    'Priority': req['weight'], 
                    'Type': req['type']
                } for req in template_requirements
            ]
            st.table(req_data)
            
            # Button to use this template
            if st.button("Use This Template", type="primary"):
                # Clear existing requirements
                st.session_state.requirements = []
                
                # Add template requirements to session state
                for req in template_requirements:
                    st.session_state.requirements.append({
                        "text": req["text"],
                        "weight": req["weight"],
                        "type": req["type"]
                    })
                st.success(f"{selected_template} template requirements added!")


def display_requirements():
    """Display and manage existing requirements"""
    if st.session_state.requirements:
        st.subheader("Current Requirements")
        for idx, req in enumerate(st.session_state.requirements):
            with st.container():
                st.markdown(f"**{idx + 1}. {req['text']}**")
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    # Dropdown to change priority
                    new_priority = st.selectbox(
                        "Priority",
                        ["Low", "Medium", "High"],
                        index=["Low", "Medium", "High"].index(req["weight"]),
                        key=f"priority_{idx}"
                    )
                    # Update priority if changed
                    if new_priority != req["weight"]:
                        st.session_state.requirements[idx]["weight"] = new_priority
                        st.rerun()
                with col2:
                    # Dropdown to change type
                    new_type = st.selectbox(
                        "Type",
                        ["boolean", "score"],
                        index=["boolean", "score"].index(req["type"]),
                        format_func=lambda x: "Boolean (0/1)" if x == "boolean" else "Score (0-100)",
                        key=f"type_{idx}"
                    )
                    # Update type if changed
                    if new_type != req["type"]:
                        st.session_state.requirements[idx]["type"] = new_type
                        st.rerun()
                with col3:
                    if st.button("⨯", key=f"remove_{idx}", help="Remove this requirement"):
                        st.session_state.requirements.pop(idx)
                        st.rerun()
                st.divider()


def create_progress_ui():
    """Create progress UI elements with counters"""
    col1, col2 = st.columns([4, 1])

    with col1:
        overall_progress = st.progress(0)
    with col2:
        overall_counter = st.empty()

    with col1:
        file_progress = st.progress(0)
    with col2:
        file_counter = st.empty()
    
    # Create a placeholder for the file status
    file_status = st.empty()
    
    return overall_progress, overall_counter, file_progress, file_counter, file_status


def display_enhanced_interview_questions(scores, avg_score, cv_text=""):
    """Display enhanced interview questions with improved UI"""
    # Add CSS for styled interview questions
    st.markdown("""
    <style>
    .interview-questions-container {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        margin-top: 20px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    .question-header {
        display: flex;
        align-items: center;
        margin-bottom: 20px;
        border-bottom: 1px solid #f0f0f0;
        padding-bottom: 10px;
    }
    .question-header-icon {
        background-color: #e6f0ff;
        color: #4a90e2;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 15px;
        font-size: 20px;
    }
    .question-header-text {
        font-size: 18px;
        font-weight: 600;
        color: #333;
    }
    .question-category {
        display: inline-block;
        background-color: #f0f7ff;
        border-radius: 20px;
        padding: 3px 10px;
        font-size: 12px;
        color: #4a90e2;
        margin-right: 5px;
        margin-bottom: 5px;
    }
    .interview-question {
        background-color: white;
        border: 1px solid #eee;
        border-left: 4px solid #4a90e2;
        padding: 15px;
        margin-bottom: 15px;
        border-radius: 5px;
        transition: all 0.2s ease;
    }
    .interview-question:hover {
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        border-left-color: #2a70c2;
    }
    .question-number {
        display: inline-block;
        background-color: #e6f0ff;
        color: #4a90e2;
        border-radius: 50%;
        width: 28px;
        height: 28px;
        text-align: center;
        line-height: 28px;
        font-weight: bold;
        margin-right: 10px;
        font-size: 14px;
    }
    .question-text {
        display: inline;
        font-size: 15px;
        color: #333;
    }
    .technical-question {
        border-left-color: #4a90e2;
    }
    .behavioral-question {
        border-left-color: #9c27b0;
    }
    .experience-question {
        border-left-color: #4caf50;
    }
    .general-question {
        border-left-color: #ff9800;
    }
    </style>
    """, unsafe_allow_html=True)
    
    try:
        # Generate interview questions
        interview_questions = generate_interview_questions(scores, avg_score, cv_text)
        
        # Container for interview questions
        st.subheader("📋 Interview Questions")
        st.write("These questions are tailored based on the candidate's profile and job requirements.")
        
        # Extract and categorize questions
        questions = [q.strip() for q in interview_questions.split('\n') if q.strip() and not q.startswith('Here')]
        
        # Function to determine question category
        def get_question_category(question):
            question_lower = question.lower()
            if any(term in question_lower for term in ['technical', 'programming', 'develop', 'code', 'implement', 'architecture']):
                return 'technical-question', 'Technical'
            elif any(term in question_lower for term in ['team', 'collaborate', 'conflict', 'challenge', 'pressure', 'difficult']):
                return 'behavioral-question', 'Behavioral'
            elif any(term in question_lower for term in ['experience', 'background', 'previous', 'worked on', 'project']):
                return 'experience-question', 'Experience'
            else:
                return 'general-question', 'General'
        
        # Display each question using Streamlit components instead of raw HTML
        for i, question in enumerate(questions, 1):
            class_name, category = get_question_category(question)
            
            # Create a container with appropriate styling based on category
            with st.container():
                col1, col2 = st.columns([1, 20])
                
                with col1:
                    # Question number in a circle
                    st.markdown(f"""
                    <div style="
                        background-color: #e6f0ff;
                        color: #4a90e2;
                        border-radius: 50%;
                        width: 28px;
                        height: 28px;
                        text-align: center;
                        line-height: 28px;
                        font-weight: bold;
                        font-size: 14px;
                    ">{i}</div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    # Question text with category highlighting
                    border_color = {
                        'technical-question': '#4a90e2',
                        'behavioral-question': '#9c27b0',
                        'experience-question': '#4caf50',
                        'general-question': '#ff9800'
                    }.get(class_name, '#4a90e2')
                    
                    st.markdown(f"""
                    <div style="
                        border-left: 4px solid {border_color};
                        padding: 10px 15px;
                        background-color: white;
                        border-radius: 5px;
                        margin-bottom: 5px;
                    ">
                        <span style="font-size: 15px; color: #333;">
                            <strong>{i}. </strong>{question}
                        </span>
                        <div style="margin-top: 8px;">
                            <span style="
                                display: inline-block;
                                background-color: #f0f7ff;
                                border-radius: 20px;
                                padding: 3px 10px;
                                font-size: 12px;
                                color: #4a90e2;
                            ">{category}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Add some space between questions
            st.write("")
        
    except Exception as e:
        st.error(f"Error generating enhanced interview questions: {str(e)}")
        # Fallback to simpler display
        st.markdown("### 📝 Interview Questions")
        st.markdown("We couldn't generate enhanced interview questions. Please try again.")


def display_streamlit_interview_questions(scores, avg_score, cv_text=""):
    """Display interview questions in two tabs: requirement-based and CV-based"""
    try:
        # Create container with styling
        st.markdown("### 📋 Interview Questions")
        st.markdown("These questions are tailored based on the candidate's profile and job requirements.")
        
        # Create tabs
        req_tab, cv_tab = st.tabs(["Requirement-based Questions", "CV-based Questions"])
        
        # Tab 1: Requirement-based Questions
        with req_tab:
            # Generate interview questions based on requirements
            interview_questions = generate_interview_questions(scores, avg_score, cv_text)
            
            # Create a container for all questions
            st.markdown("""
            <div style="
                background-color: white;
                border-radius: 8px;
                padding: 20px;
                border: 1px solid #e0e0e0;
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            ">
            """, unsafe_allow_html=True)
            
            # Split by lines to process each line
            lines = interview_questions.split('\n')
            
            # Track the current skill heading
            current_heading = None
            
            # Process each line
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # If it's a numbered skill heading
                if re.match(r'^\d+\.', line) and ':' in line:
                    # Display the heading in bold
                    current_heading = line
                    st.markdown(f"**{current_heading}**")
                    
                # If it's a bullet point question
                elif line.startswith('•') or line.startswith('-') or line.startswith('*'):
                    # Clean up any extra markers
                    question = re.sub(r'^[•\-\*]\s*', '', line)
                    
                    # Display the bullet point
                    st.markdown(f"• {question}")
                    
                    # Add space after a question group (after a bullet point)
                    st.write("")
            
            # If we couldn't parse it properly, show the raw text with some basic processing
            if not current_heading:
                # Simple fallback method - try to identify patterns
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    if re.match(r'^\d+\.', line) and ':' in line:
                        # It's likely a heading
                        st.markdown(f"**{line}**")
                    else:
                        # It's likely a question - add a bullet if it doesn't have one
                        if not line.startswith('•') and not line.startswith('-'):
                            st.markdown(f"• {line}")
                        else:
                            st.markdown(line)
                            
                        # Add space after each question section
                        st.write("")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Tab 2: CV-based Questions
        with cv_tab:
            try:
                # Generate CV-based questions
                cv_questions = generate_cv_questions(cv_text)
                
                # Create a container for CV-based questions
                st.markdown("""
                <div style="
                    background-color: white;
                    border-radius: 8px;
                    padding: 20px;
                    border: 1px solid #e0e0e0;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                ">
                """, unsafe_allow_html=True)
                
                # Process and display CV-based questions
                lines = cv_questions.split('\n')
                
                for i, line in enumerate(lines):
                    line = line.strip()
                    if not line or line.startswith("Here"):
                        continue
                        
                    # If it's a numbered question
                    if re.match(r'^\d+\.', line):
                        # Format like "Background Experience:" or similar
                        parts = line.split(':', 1)
                        if len(parts) > 1:
                            st.markdown(f"**{parts[0]}:**")
                            st.markdown(f"• {parts[1].strip()}")
                        else:
                            # No colon format, just display as a bullet
                            question = re.sub(r'^\d+\.\s*', '', line)
                            st.markdown(f"**{i+1}. CV-specific Question:**")
                            st.markdown(f"• {question}")
                    else:
                        # Add as a bullet point if it seems like a question
                        if '?' in line:
                            st.markdown(f"• {line}")
                
                st.markdown("</div>", unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Error generating CV-based questions: {str(e)}")
                st.markdown("We couldn't generate CV-based questions. Please try again.")
        
        # Add a note for interviewers below the tabs
        st.markdown("""
        <div style="
            background-color: #f0f7ff;
            border-radius: 5px;
            padding: 10px;
            margin-top: 15px;
            border: 1px solid #d1e6ff;
            font-size: 12px;
        ">
            <strong>Note:</strong> These questions are designed to assess the candidate's qualifications and fit for the role.
            The requirement-based questions focus on specific job skills, while the CV-based questions explore the candidate's unique background.
        </div>
        """, unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Error generating interview questions: {str(e)}")
        st.markdown("We couldn't generate interview questions. Please try again.")

def display_cv_results(cv_name, scores, _format_score=None):
    """Display detailed results for a single CV with enhanced interview questions"""
    
    # Create DataFrame for this CV's scores
    df = format_dataframe(scores)
    
    # Display scores table
    st.dataframe(
        df[['requirement', 'formatted_score', 'priority', 'type']].rename(columns={
            'requirement': 'Requirement',
            'formatted_score': 'Score',
            'priority': 'Priority',
            'type': 'Type'
        }),
        use_container_width=True
    )

    # Calculate overall score using the shared function
    avg_score = calculate_weighted_score(scores)

    # Determine recommendation and color
    if avg_score >= 80:
        recommendation = "Highly Recommended"
        recommendation_color = "green"
    elif avg_score >= 60:
        recommendation = "Recommended with Additional Training"
        recommendation_color = "blue"
    elif avg_score >= 40:
        recommendation = "Need Further Consideration"
        recommendation_color = "orange"
    else:
        recommendation = "Not Meet Requirements"
        recommendation_color = "red"

    # Generate AI summary
    try:
        format_func = _format_score if _format_score else lambda x: f"{x['score']:.1f}%"
        summary = generate_ai_summary(scores, avg_score, format_func)
    except Exception as e:
        summary = "Unable to generate detailed summary."
        st.error(f"Error generating summary: {str(e)}")

    # Create CSS for layout
    st.markdown("""
    <style>
    .score-summary-container {
        display: flex;
        align-items: stretch;
        gap: 20px;
        margin-top: 20px;
        min-height: 250px;
    }
    .overall-score-container, 
    .candidate-summary-container {
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        background-color: #f0f7ff;
        border-radius: 10px;
        padding: 20px;
    }
    .candidate-summary-container {
        flex: 2;
    }
    .overall-score-container {
        flex: 1;
        text-align: center;
        align-items: center;
    }
    .overall-score-container h1 {
        font-size: 5em; 
        font-weight: bold;
        margin: 0;
        line-height: 1; 
    }
    .overall-score-container h3, 
    .candidate-summary-container h3 {
        font-size: 1.5em;
        margin-bottom: 15px;
        color: #333;
        width: 100%;
        text-align: left;
    }
    .candidate-summary-container h3 {
        padding-left: 0;
    }
    .overall-score-container h4 {
        margin-top: 10px;
        font-size: 1em;
    }
    .candidate-summary-container p {
        text-align: left;
        margin: 0;
        font-size: 0.9em;  /* Smaller font size */
        line-height: 1.5;
    }
    .interview-questions-header {
        display: flex;
        align-items: center;
        margin-top: 30px;
        margin-bottom: 15px;
        cursor: pointer;
    }
    .interview-questions-icon {
        margin-right: 10px;
        font-size: 24px;
    }
    .interview-questions-title {
        font-size: 18px;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

    # Create the combined layout
    st.markdown(f"""
    <div class="score-summary-container">
        <div class="overall-score-container">
            <h3>Overall Match Score</h3>
            <h1 style="color: {recommendation_color};">{avg_score:.1f}%</h1>
            <h4 style="color: {recommendation_color};">{recommendation}</h4>
        </div>
        <div class="candidate-summary-container">
            <h3>Candidate Summary</h3>
            <p>✍️ {summary}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Add spacer
    st.write("")
    st.write("")
    
    # Use the CV name as a default text if no CV text is provided
    # This helps generate interview questions even if the full CV text isn't available
    cv_text_for_questions = ""  # Initialize with empty string as fallback
    
    # Try to get CV text from session state if available
    if 'processing' in st.session_state and 'processed_files' in st.session_state.processing:
        if cv_name in st.session_state.processing['processed_files']:
            cv_text_for_questions = st.session_state.processing['processed_files'][cv_name]
    
    # Add a horizontal rule to visually separate the sections
    st.markdown("<hr style='margin-bottom: 20px;'>", unsafe_allow_html=True)
    
    # Display interview questions
    display_streamlit_interview_questions(scores, avg_score, "")

    
    return avg_score


def display_summary(scores, avg_score, format_score_func):
    """Display summary section with overall assessment and requirements summary"""
    st.subheader("Summary")
    col1, col2 = st.columns(2)


    with col1:
        st.write("**Overall Assessment**")
        if avg_score >= 80:
            st.success("Strong Match ✨")
            recommendation = "Highly recommended for the position"
        elif avg_score >= 60:
            st.info("Good Match 👍")
            recommendation = "Good candidate, but may need some additional training"
        elif avg_score >= 40:
            st.warning("Moderate Match 🤔")
            recommendation = "May need significant training or development"
        else:
            st.error("Low Match ⚠️")
            recommendation = "May not be suitable for this position"
        st.write(recommendation)
        
    with col2:
        st.write("**Requirements Summary**")

        # Get statistics using the shared function
        boolean_reqs, met_boolean, score_reqs, high_scores, score_based_avg = get_requirement_stats(scores)
        
        # Display summary statistics
        if boolean_reqs > 0:
            st.write(f"✓ Met {met_boolean}/{boolean_reqs} required qualifications")
        if score_reqs > 0:
            st.write(f"📊 Average score for rated skills: {score_based_avg:.1f}%")


def display_ai_summary(scores, avg_score, format_score_func, client):
    """Display AI-generated assessment summary"""
    with st.spinner("Generating AI assessment..."):
        try:
            # Use the shared function for generating summaries
            summary = generate_ai_summary(scores, avg_score, format_score_func)
            
            st.write("**Assessment Summary:**")
            with st.container():
                st.markdown("""
                    <style>
                    .ai-summary {
                        padding: 20px;
                        border-radius: 10px;
                        background-color: #f0f7ff;
                        border-left: 5px solid #0096ff;
                        margin: 10px 0;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                
                st.markdown(f"""
                    <div class="ai-summary">
                    ✍️ {summary}
                    </div>
                    """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error generating AI summary: {str(e)}")


def display_detailed_analysis(scores):
    """Display detailed analysis of individual requirements"""
    st.subheader("Detailed Analysis")
    for score in scores:
        with st.expander(f"Requirement: {score['requirement']}"):
            st.write(f"Score Type: {score['type'].capitalize()}")
            if score['type'] == 'boolean':
                st.write(f"Score: {'Yes' if score['score'] == 1 else 'No'}")
            else:
                st.write(f"Score: {score['score']:.1f}%")
            st.write(f"Priority: {score['priority']}")


@st.cache_data
def prepare_comparison_data_for_display(all_results):
    """Prepare comparison data (cacheable part)"""
    from modules.data_handling import prepare_comparison_data
    
    # Use the shared function to prepare comparison data
    comparison_df = prepare_comparison_data(all_results)
    
    # Generate CSV for download
    csv = comparison_df.to_csv(index=False).encode('utf-8')
    
    return comparison_df, csv


def display_comparison_view(all_results, key_suffix="main"):
    """Display comparison view for all candidates with expander and styled container"""
    # Create a container with a border and some padding
    st.markdown("""
    <style>
    .comparison-container {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 15px;
        background-color: #f9f9f9;
    }
    .download-btn-container {
        display: flex;
        justify-content: center;
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Use an expander similar to Filter Results
    with st.expander("Candidates Comparison", expanded=True):
        # Add container inside the expander
        st.markdown('<div class="comparison-container">', unsafe_allow_html=True)
        
        # Use the shared function to prepare comparison data
        comparison_df = prepare_comparison_data(all_results)
        
        # Apply styling here (outside of caching)
        styled_df = comparison_df.style.apply(highlight_score)
        
        # Display the dataframe
        st.dataframe(styled_df, use_container_width=True)
        
        # Export button with unique key
        csv = comparison_df.to_csv(index=False).encode('utf-8')
        st.markdown('<div class="download-btn-container">', unsafe_allow_html=True)
        st.download_button(
            label="📥 Download Comparison as CSV",
            data=csv,
            file_name="cv_comparison_results.csv",
            mime="text/csv",
            key=f"download_csv_{key_suffix}"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    return comparison_df