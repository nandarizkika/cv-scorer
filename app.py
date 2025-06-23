import streamlit as st
import zipfile
from openai import OpenAI
import traceback
from datetime import datetime

# Import from modules
from modules.pdf_processor import process_pdf
from modules.ai_scoring import (
    get_openai_score, 
    get_openai_score_with_voting, 
    format_score,
    generate_ai_summary
)
import modules.ui_components as ui_components
from modules.ui_components import (
    create_requirement_ui, 
    display_requirements, 
    create_progress_ui
)
from modules.batch_processing import (
    BatchProcessingTracker, 
    count_total_files, 
    process_files, 
    display_processing_status
)
from modules.results_display import display_results, display_detailed_cv_tabs
from modules.data_handling import calculate_weighted_score
from modules.audit_logging import (
    AuditLogger, 
    integrate_audit_logging, 
    anonymize_personal_data
)

class CVScoringApplication:
    def __init__(self):
        """Initialize the CV Scoring Application"""
        # Configure Streamlit page
        st.set_page_config(
            page_title="AI-Powered CV Scoring Engine", 
            layout="wide",
            page_icon="📊"
        )
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
        # Initialize audit logger
        self.audit_logger = AuditLogger()
        
        # Initialize application state
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize or reset session state variables"""
        # Job Requirements
        if 'requirements' not in st.session_state:
            st.session_state.requirements = []
        
        # Processing State
        if 'processing' not in st.session_state:
            st.session_state.processing = {
                'in_progress': False,
                'processed_files': {},
                'current_results': {},
                'tracker': None
            }
        
        # Filter State
        if 'filter_state' not in st.session_state:
            st.session_state.filter_state = {
                "min_score": 0,
                "selected_requirements": [],
                "must_meet_all_boolean": False
            }
        
        # Reset filters
        if 'filters_applied' not in st.session_state:
            st.session_state.filters_applied = False
    
    def _display_application_header(self):
        """Display main application header and description"""
        st.title("🤖 AI-Powered CV Scoring Engine")
        st.markdown("""
        Automated candidate screening and assessment powered by advanced AI.
        Define job requirements and upload CVs for instant, comprehensive evaluation.
        """)
    
    def _setup_sidebar(self):
        """Configure the Streamlit sidebar"""
        with st.sidebar:
            st.header("🎯 Job Requirements")
            create_requirement_ui()
            display_requirements()
            
            # Add an audit log view in the sidebar
            if st.button("📋 View Audit Logs"):
                self.audit_logger.display_audit_dashboard()
    
    def _process_cv_files(self, uploaded_files):
        """
        Process uploaded CV files with advanced options
        
        Args:
            uploaded_files (list): List of uploaded PDF or ZIP files
        
        Returns:
            dict: Processed CV results
        """
        # Validate requirements are defined
        if not st.session_state.requirements:
            st.warning("Please add job requirements before processing CVs.")
            return {}
        
        # Processing options
        col1, col2, col3 = st.columns([3, 3, 2])
        with col1:
            use_voting_system = st.checkbox(
                "Use Multi-Model Voting", 
                help="Leverage multiple AI models for more accurate assessment"
            )
        with col2:
            background_processing = st.checkbox(
                "Show Partial Results", 
                help="Display results as they become available"
            )
        with col3:
            reanalyze_button = st.button(
                "Analyze CVs", 
                type="primary", 
                use_container_width=True
            )
        
        # Process files when button is clicked
        if reanalyze_button:
            try:
                # Prepare for processing
                st.session_state.processing['in_progress'] = True
                st.session_state.processing['current_results'] = {}
                
                # Count total files
                total_files = count_total_files(uploaded_files)
                
                # Create progress tracker
                tracker = BatchProcessingTracker(
                    total_files, 
                    len(st.session_state.requirements)
                )
                st.session_state.processing['tracker'] = tracker
                
                # Process files
                all_results = process_files(
                    uploaded_files, 
                    use_voting_system, 
                    background_processing, 
                    tracker, 
                    ui_components
                )
                
                # Log audit information
                self._log_batch_processing_audit(all_results)
                
                # Complete processing
                st.session_state.processing['in_progress'] = False
                st.session_state.processing['current_results'] = all_results
                st.session_state.all_results = all_results
                
                return all_results
            
            except Exception as e:
                st.error(f"Error processing files: {e}")
                traceback.print_exc()
                return {}
        
        return {}
    
    def _log_batch_processing_audit(self, all_results):
        """
        Log audit information for batch processing
        
        Args:
            all_results (dict): Processed CV results
        """
        try:
            for cv_name, scores in all_results.items():
                # Anonymize CV text if available
                cv_text = st.session_state.processing.get('processed_files', {}).get(cv_name, '')
                anonymized_cv_text = anonymize_personal_data(cv_text)
                
                # Log candidate evaluation
                self.audit_logger.log_candidate_evaluation(
                    candidate_data={
                        'source_file': cv_name,
                        'processing_timestamp': datetime.now()
                    },
                    scoring_results={
                        'overall_score': calculate_weighted_score(scores),
                        'requirement_scores': scores,
                        'ai_model_version': 'v1.0',
                        'scoring_method': 'Multi-model Voting',
                        'risk_assessment': self._assess_candidate_risk(scores)
                    }
                )
        except Exception as e:
            st.error(f"Audit logging error: {e}")
    
    def _assess_candidate_risk(self, scores):
        """
        Assess risk for a candidate based on scoring
        
        Args:
            scores (list): Candidate's requirement scores
        
        Returns:
            dict: Risk assessment details
        """
        risk_indicators = {
            'low_score_requirements': sum(
                1 for score in scores if score['score'] < 40
            ),
            'boolean_failures': sum(
                1 for score in scores 
                if score['type'] == 'boolean' and score['score'] == 0
            ),
            'overall_risk_level': 'Medium'  # Default risk level
        }
        
        # Determine risk level
        if risk_indicators['low_score_requirements'] > 2:
            risk_indicators['overall_risk_level'] = 'High'
        elif risk_indicators['boolean_failures'] > 1:
            risk_indicators['overall_risk_level'] = 'High'
        elif risk_indicators['low_score_requirements'] > 0:
            risk_indicators['overall_risk_level'] = 'Medium'
        else:
            risk_indicators['overall_risk_level'] = 'Low'
        
        return risk_indicators
    
    def run(self):
        """Main application run method"""
        # Display application header
        self._display_application_header()
        
        # Setup sidebar
        self._setup_sidebar()
        
        # File upload section
        uploaded_files = st.file_uploader(
            "Upload CV(s)", 
            type=["pdf", "zip"], 
            accept_multiple_files=True,
            help="Upload one or more PDFs, or a ZIP file containing PDFs"
        )
        
        # Process CV files
        all_results = self._process_cv_files(uploaded_files)
        
        # Display processing status if in progress
        if st.session_state.processing.get('in_progress', False):
            tracker = st.session_state.processing.get('tracker')
            if tracker:
                display_processing_status(tracker)
        
        # Display results if available
        if all_results:
            # Ensure client is passed for any AI-generated content
            display_results(all_results, format_score, self.client)

def main():
    """Entry point for the CV Scoring Application"""
    try:
        # Initialize and run the application
        app = CVScoringApplication()
        app.run()
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()