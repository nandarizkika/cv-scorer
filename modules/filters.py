import streamlit as st
import uuid
from typing import Dict, List
from modules.data_handling import calculate_weighted_score


def create_filter_ui():
    """Create an improved filter UI with persistent state"""

    # Ensure filter_state exists and has all necessary keys
    if 'filter_state' not in st.session_state:
        st.session_state.filter_state = {
            "min_score": 0,
            "selected_requirements": [],
            "must_meet_all_boolean": False
        }

    if 'filter_results_expanded' not in st.session_state:
        st.session_state.filter_results_expanded = False

    with st.container():
        with st.expander("Filter Results", 
                         expanded=st.session_state.filter_results_expanded):

            # Two column layout for filters
            left_col, right_col = st.columns([3, 2])
            
            with left_col:
                st.subheader("Score Filter")
                
                # Use session state value with a default fallback
                current_min_score = st.session_state.filter_state.get("min_score", 0)
                
                # Slider with persistent state
                min_score = st.slider(
                    "Minimum Overall Score", 
                    0, 100, 
                    value=current_min_score,
                    step=5,
                    help="Only show candidates with scores at or above this threshold",
                    key=f"persistent_min_score_slider"
                )
                

                # Score range buttons
                score_cols = st.columns(4)
                with score_cols[0]:
                    if st.button("All", key="score_all_btn", use_container_width=True):
                        min_score = 0
                with score_cols[1]:
                    if st.button("≥ 70%", key="score_70_btn", use_container_width=True):
                        min_score = 70
                with score_cols[2]:
                    if st.button("≥ 80%", key="score_80_btn", use_container_width=True):
                        min_score = 80
                with score_cols[3]:
                    if st.button("≥ 90%", key="score_90_btn", use_container_width=True):
                        min_score = 90
                

                # Boolean requirements option
                st.subheader("Qualification Filter")
                current_must_meet_all = st.session_state.filter_state.get("must_meet_all_boolean", False)
                must_meet_all_boolean = st.checkbox(
                    "Must meet all boolean requirements", 
                    value=current_must_meet_all,
                    help="Only show candidates that meet all required qualifications",
                    key="persistent_must_meet_all_checkbox"
                )
            

            with right_col:
                # Specific requirements selection
                st.subheader("Requirements")
                
                # Determine the current state of all requirements
                current_selected = st.session_state.filter_state.get("selected_requirements", [])
                num_requirements = len(st.session_state.requirements)
                
                # Select/Unselect All option with explicit state management
                select_all = st.checkbox(
                    "Select All Requirements", 
                    value=num_requirements > 0 and len(current_selected) == num_requirements,
                    key="select_all_requirements_checkbox"
                )
                
                # Scrollable container with fixed height
                with st.container(height=200):
                    selected_requirements = []
                    for req in st.session_state.requirements:
                        # Determine checkbox state
                        if select_all:
                            # When "Select All" is checked, all are selected
                            is_selected = True
                        else:
                            # When "Select All" is unchecked, none are selected
                            is_selected = False
                        
                        # Add visual cue for requirement type
                        prefix = "🔶 " if req["type"] == "boolean" else "📊 "
                        
                        # Use a consistent key for each requirement
                        checkbox_key = f"req_checkbox_{req['text']}"
                        
                        # Checkbox with persistent state
                        if st.checkbox(
                            f"{prefix} {req['text']}", 
                            value=is_selected,
                            key=checkbox_key
                        ):
                            selected_requirements.append(req["text"])

                # If select all is true, ensure all requirements are selected
                # If select all is false, ensure no requirements are selected
                if select_all:
                    selected_requirements = [req["text"] for req in st.session_state.requirements]
                else:
                    selected_requirements = []
            

            # Bottom controls
            st.divider()
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Apply filters button
                filter_button = st.button(
                    "Apply Filters", 
                    type="primary", 
                    use_container_width=True,
                    key="apply_filters_persistent_btn"
                )
            
            with col2:
                # Clear filters button
                clear_button = st.button(
                    "Reset Filters", 
                    use_container_width=True,
                    key="reset_filters_persistent_btn"
                )
            
            # Handle clear button
            if clear_button:
                # Reset filter state
                st.session_state.filter_state = {
                    "min_score": 0,
                    "selected_requirements": [],
                    "must_meet_all_boolean": False
                }
                st.session_state.filters_applied = False
                st.rerun()

            if filter_button or clear_button:
                st.session_state.filter_results_expanded = False
            
            # Always update session state
            st.session_state.filter_state.update({
                "min_score": min_score,
                "selected_requirements": selected_requirements,
                "must_meet_all_boolean": must_meet_all_boolean
            })

    # Return filter parameters and whether to apply filters
    return {
        "min_score": min_score,
        "selected_requirements": selected_requirements,
        "must_meet_all_boolean": must_meet_all_boolean
    }, filter_button


def apply_filters(all_results, filter_params):
    """Apply filters to results based on filter parameters"""
    filtered_results = {}
    
    for cv_name, scores in all_results.items():
        # Calculate overall score
        cv_score = calculate_weighted_score(scores)
        
        # Filter by minimum score
        if cv_score < filter_params["min_score"]:
            continue

        # Filter by meeting all boolean requirements
        if filter_params["must_meet_all_boolean"]:
            boolean_scores = [score for score in scores if score["type"] == "boolean"]
            if not all(score["score"] == 1 for score in boolean_scores):
                continue

        # Filter by specific requirements
        filtered_scores = scores
        if filter_params["selected_requirements"]:
            # Only keep requirements that are selected
            filtered_scores = [score for score in scores 
                              if score["requirement"] in filter_params["selected_requirements"]]
            
            # Skip CV if no matching requirements
            if not filtered_scores:
                continue
                
        # Add to filtered results if it passed all filters
        filtered_results[cv_name] = filtered_scores
    
    return filtered_results