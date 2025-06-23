import streamlit as st
from modules.ui_components import display_cv_results, display_summary, display_detailed_analysis, display_comparison_view
from modules.filters import apply_filters

def display_detailed_cv_tabs(results, format_score, client):
    """Display detailed results in an expandable section"""
    # CSS for styling
    st.markdown("""
    <style>
    .detailed-results-container {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 15px;
        background-color: #f9f9f9;
    }
    .stTabs {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    .stTabs [data-baseweb="tab"] {
        padding-top: 5px !important;
        padding-bottom: 5px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Use an expander similar to Candidates Comparison
    with st.expander("Detailed Results", expanded=True):
        # Container inside the expander
        st.markdown('<div class="detailed-results-container">', unsafe_allow_html=True)
        
        # Create tabs for each CV
        cv_tabs = st.tabs([f"CV: {cv_name}" for cv_name in results.keys()])
        
        for tab, (cv_name, scores) in zip(cv_tabs, results.items()):
            with tab:
                # Display scores and overall match
                avg_score = display_cv_results(cv_name, scores, format_score)
                
                # # Display summary
                # display_summary(scores, avg_score, format_score)
        
        st.markdown('</div>', unsafe_allow_html=True)

def display_results(all_results, format_score, client):
    """Display analysis results with improved filtering UI"""
    if not all_results:
        st.error("No valid CVs were processed. Please check your files and try again.")
        return
        
    st.success(f"Successfully analyzed {len(all_results)} CVs!")
    
    # Save results to session state for filters
    st.session_state.all_results = all_results
    
    # Reset the filter results expander to be closed
    st.session_state.filter_results_expanded = False
    
    # Create filter UI
    from modules.filters import create_filter_ui
    filter_params, filter_applied = create_filter_ui()
    
    # Determine which results to display
    display_results = all_results
    
    # Apply filters when button is clicked
    if filter_applied:
        filtered_results = apply_filters(st.session_state.all_results, filter_params)
        
        # Store filtered results in session state
        st.session_state.filtered_results = filtered_results
        st.session_state.filters_applied = True
        
        # Update display results
        display_results = filtered_results
    elif 'filters_applied' in st.session_state and st.session_state.filters_applied:
        # Use previously filtered results
        display_results = st.session_state.filtered_results
    
    # Display result count with badge styling if filters are applied
    if 'filters_applied' in st.session_state and st.session_state.filters_applied:
        total_cvs = len(st.session_state.all_results)
        filtered_cvs = len(display_results)
        
        # Custom badge styling
        st.markdown(f"""
        <div style="
            background-color: #f0f7ff;
            border-radius: 5px;
            padding: 10px 15px;
            margin-bottom: 15px;
            border-left: 5px solid #0096ff;
            display: flex;
            align-items: center;
        ">
            <span style="font-size: 1.2em; margin-right: 10px;">🔍</span>
            <span>Showing <b>{filtered_cvs}</b> of <b>{total_cvs}</b> candidates that match your filters</span>
        </div>
        """, unsafe_allow_html=True)
    
    # Show comparison view for current results (filtered or all)
    comparison_df = display_comparison_view(display_results, f"results_{id(display_results)}")
    
    # No results message
    if len(display_results) == 0:
        st.warning("No candidates match your current filter criteria. Try adjusting your filters.")
    
    # Show detailed results for each CV
    if len(display_results) > 0:
        display_detailed_cv_tabs(display_results, format_score, client)

    # Add button to start a new analysis if needed
    if st.button("Start New Analysis", key=f"start_new_analysis_{id(display_results)}"):
        # Clear session state for new analysis
        st.session_state.pop('all_results', None)
        st.session_state.pop('filtered_results', None)
        st.session_state.filters_applied = False
        st.session_state.processing = {
            'in_progress': False,
            'processed_files': {},
            'current_results': {},
            'tracker': None
        }
        st.rerun()