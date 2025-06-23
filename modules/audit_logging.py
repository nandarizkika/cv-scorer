import os
import json
import uuid
from datetime import datetime
import streamlit as st
import pandas as pd
import hashlib
import logging
from typing import Dict, List, Any

class AuditLogger:
    """
    Comprehensive audit logging system for CV scoring application
    Supports multiple logging mechanisms:
    1. File-based logging
    2. Database logging (optional)
    3. Secure, anonymized storage
    4. Performance tracking
    """
    
    def __init__(self, 
                 log_dir: str = 'audit_logs', 
                 enable_database_logging: bool = False):
        """
        Initialize the audit logger
        
        Args:
            log_dir (str): Directory to store log files
            enable_database_logging (bool): Flag to enable database logging
        """
        # Ensure log directory exists
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Setup file-based logging
        self.logger = logging.getLogger('cv_scoring_audit')
        self.logger.setLevel(logging.INFO)
        
        # File handler for detailed logs
        file_handler = logging.FileHandler(
            os.path.join(log_dir, f'cv_scoring_audit_{datetime.now().strftime("%Y%m%d")}.log')
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(file_handler)
        
        # Database logging (placeholder - can be extended)
        self.enable_database_logging = enable_database_logging
        
        # Ensure audit log storage exists in session state
        if 'audit_logs' not in st.session_state:
            st.session_state.audit_logs = []
    
    def generate_secure_id(self, candidate_data: Dict) -> str:
        """
        Generate a secure, anonymized ID for the candidate
        
        Args:
            candidate_data (Dict): Candidate's data
        
        Returns:
            str: Secure, anonymized identifier
        """
        # Create a hash based on non-identifying information
        hash_input = json.dumps({
            'skills': candidate_data.get('skills', []),
            'experience_years': candidate_data.get('experience_years'),
            'education_level': candidate_data.get('education_level')
        }, sort_keys=True)
        
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    def log_candidate_evaluation(
        self, 
        candidate_data: Dict[str, Any], 
        scoring_results: Dict[str, Any]
    ) -> None:
        """
        Log detailed candidate evaluation information
        
        Args:
            candidate_data (Dict): Raw candidate information
            scoring_results (Dict): Scoring and evaluation results
        """
        # Generate secure candidate ID
        candidate_id = self.generate_secure_id(candidate_data)
        
        # Prepare audit log entry
        audit_entry = {
            'log_id': str(uuid.uuid4()),
            'candidate_id': candidate_id,
            'timestamp': datetime.now().isoformat(),
            'source_file': candidate_data.get('source_file', 'Unknown'),
            'overall_score': scoring_results.get('overall_score', 0),
            'requirement_scores': scoring_results.get('requirement_scores', []),
            'recommendations': scoring_results.get('recommendations', []),
            'risk_assessment': scoring_results.get('risk_assessment', {}),
            'processing_metadata': {
                'ai_model_version': scoring_results.get('ai_model_version', 'Unknown'),
                'scoring_method': scoring_results.get('scoring_method', 'Standard')
            }
        }
        
        # Log to file
        self.logger.info(json.dumps(audit_entry, indent=2))
        
        # Store in session state for potential UI display
        st.session_state.audit_logs.append(audit_entry)
        
        # Optional database logging
        if self.enable_database_logging:
            self._log_to_database(audit_entry)
    
    def _log_to_database(self, audit_entry: Dict):
        """
        Placeholder for database logging
        
        Args:
            audit_entry (Dict): Audit log entry to be stored
        """
        # Implement database logging (e.g., SQLAlchemy, MongoDB)
        # This is a placeholder - actual implementation depends on your database choice
        pass
    
    def export_audit_logs(self, format: str = 'csv') -> bytes:
        """
        Export audit logs to a file
        
        Args:
            format (str): Export format (csv or json)
        
        Returns:
            bytes: Exported log file
        """
        # Convert logs to DataFrame
        if not st.session_state.audit_logs:
            return b''
        
        df = pd.DataFrame(st.session_state.audit_logs)
        
        if format == 'csv':
            return df.to_csv(index=False).encode('utf-8')
        elif format == 'json':
            return json.dumps(st.session_state.audit_logs, indent=2).encode('utf-8')
    
    def generate_truly_unique_id(self, candidate_data: Dict) -> str:
        """
        Generate a more robust unique identifier
        
        Args:
            candidate_data (Dict): Candidate's information
        
        Returns:
            str: Unique, secure identifier
        """
        import hashlib
        import time
        
        # Combine multiple unique elements
        unique_input = '|'.join([
            str(candidate_data.get('source_file', '')),
            str(candidate_data.get('overall_score', 0)),
            str(time.time()),
            str(hash(frozenset(candidate_data.items())))
        ])
        
        # Generate a secure hash
        return hashlib.sha256(unique_input.encode()).hexdigest()[:16]
    
    def analyze_performance_metrics(self) -> Dict:
        """
        Analyze overall performance metrics from audit logs
        
        Returns:
            Dict: Performance analysis results
        """
        if not st.session_state.audit_logs:
            return {}
        
        df = pd.DataFrame(st.session_state.audit_logs)
        
        # Calculate top performers based on overall score
        top_performer_threshold = 80  # Configurable threshold
        top_performers_count = (df['overall_score'] >= top_performer_threshold).sum()
        top_performers_percentage = (top_performers_count / len(df)) * 100 if len(df) > 0 else 0
        
        return {
            'total_candidates_processed': len(df),
            'average_overall_score': df['overall_score'].mean(),
            'score_distribution': df['overall_score'].describe().to_dict(),
            'top_performers_count': top_performers_count,
            'top_performers_percentage': top_performers_percentage,
            'candidates_by_source': df['source_file'].value_counts().to_dict()
        }
    
    def log_candidate_evaluation(
        self, 
        candidate_data: Dict[str, Any], 
        scoring_results: Dict[str, Any]
    ) -> None:
        """
        Log detailed candidate evaluation information with improved unique ID
        """
        # Merge candidate data and scoring results for ID generation
        merged_data = {**candidate_data, **scoring_results}
        
        # Generate truly unique candidate ID
        candidate_id = self.generate_truly_unique_id(merged_data)
        
        # Prepare audit log entry
        audit_entry = {
            'log_id': str(uuid.uuid4()),
            'candidate_id': candidate_id,
            'timestamp': datetime.now().isoformat(),
            'source_file': candidate_data.get('source_file', 'Unknown'),
            'overall_score': scoring_results.get('overall_score', 0),
            'requirement_scores': scoring_results.get('requirement_scores', []),
            'recommendations': scoring_results.get('recommendations', []),
            'risk_assessment': scoring_results.get('risk_assessment', {}),
            'processing_metadata': {
                'ai_model_version': scoring_results.get('ai_model_version', 'Unknown'),
                'scoring_method': scoring_results.get('scoring_method', 'Standard')
            }
        }
        
        # Continue with existing logging logic...
        self.logger.info(json.dumps(audit_entry, indent=2))
        st.session_state.audit_logs.append(audit_entry)
        
        if self.enable_database_logging:
            self._log_to_database(audit_entry)
    
    def display_audit_dashboard(self):
        """
        Create a Streamlit dashboard for audit logs and performance metrics
        """
        st.subheader("Audit Log Dashboard")
        
        # Performance Metrics
        metrics = self.analyze_performance_metrics()
        
        # Metrics display
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Candidates", metrics.get('total_candidates_processed', 0))
        with col2:
            st.metric("Avg Score", f"{metrics.get('average_overall_score', 0):.1f}%")
        with col3:
            st.metric("Top Performers", 
                      f"{metrics.get('top_performers_count', 0)} "
                      f"({metrics.get('top_performers_percentage', 0):.1f}%)")
        
        # Detailed Metrics Expander
        with st.expander("Detailed Performance Metrics"):
            st.json(metrics)
        
        # Export Options
        export_col1, export_col2 = st.columns(2)
        with export_col1:
            if st.download_button(
                label="Export as CSV",
                data=self.export_audit_logs(format='csv'),
                file_name=f"cv_scoring_audit_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            ):
                st.success("Audit log exported successfully!")
        
        with export_col2:
            if st.download_button(
                label="Export as JSON",
                data=self.export_audit_logs(format='json'),
                file_name=f"cv_scoring_audit_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            ):
                st.success("Audit log exported successfully!")
        
        # Recent Logs Table
        st.subheader("Recent Evaluation Logs")
        if st.session_state.audit_logs:
            recent_logs_df = pd.DataFrame(st.session_state.audit_logs[-10:])
            st.dataframe(recent_logs_df[['log_id', 'candidate_id', 'timestamp', 'overall_score']])

# Usage example in app.py
def integrate_audit_logging(app_function):
    """
    Decorator to integrate audit logging into the main application function
    """
    def wrapper(*args, **kwargs):
        # Initialize audit logger
        audit_logger = AuditLogger()
        
        try:
            # Run the main application function
            result = app_function(*args, **kwargs)
            
            # Log successful processing
            audit_logger.log_candidate_evaluation(
                candidate_data={
                    'source_file': 'Multiple CVs',
                    'processing_timestamp': datetime.now()
                },
                scoring_results={
                    'overall_score': result.get('overall_score', 0),
                    'ai_model_version': 'v1.0',
                    'scoring_method': 'Multi-model Voting'
                }
            )
            
            return result
        
        except Exception as e:
            # Log any processing errors
            audit_logger.logger.error(f"Processing error: {str(e)}")
            raise
    
    return wrapper

# Utility for privacy and compliance
def anonymize_personal_data(cv_text: str) -> str:
    """
    Remove personally identifiable information from CV text
    
    Args:
        cv_text (str): Original CV text
    
    Returns:
        str: Anonymized CV text
    """
    # Regular expression patterns to remove
    import re
    
    # Remove phone numbers
    cv_text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE REDACTED]', cv_text)
    
    # Remove email addresses
    cv_text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL REDACTED]', cv_text)
    
    # Remove addresses (basic pattern)
    cv_text = re.sub(r'\d+\s+[A-Za-z0-9\s,]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr)\b', '[ADDRESS REDACTED]', cv_text)
    
    return cv_text