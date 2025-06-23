import time
import streamlit as st
from datetime import datetime, timedelta
import zipfile
import io
from modules.pdf_processor import process_pdf
from modules.ai_scoring import get_openai_score, get_openai_score_with_voting

class BatchProcessingTracker:
    """Track batch processing progress and estimate completion time"""
    def __init__(self, total_files, total_requirements):
        self.start_time = time.time()
        self.total_files = total_files
        self.total_requirements = total_requirements
        self.total_operations = total_files * total_requirements
        self.completed_operations = 0
        self.file_times = []
        self.req_times = []
        self.current_file_start = None
        self.current_req_start = None
    
    def start_file(self):
        """Mark the start of processing a new file"""
        self.current_file_start = time.time()
        
    def complete_file(self):
        """Mark completion of a file and record time"""
        if self.current_file_start:
            elapsed = time.time() - self.current_file_start
            self.file_times.append(elapsed)
            self.current_file_start = None
    
    def start_requirement(self):
        """Mark the start of processing a requirement"""
        self.current_req_start = time.time()
    
    def complete_requirement(self):
        """Mark completion of a requirement and record time"""
        if self.current_req_start:
            elapsed = time.time() - self.current_req_start
            self.req_times.append(elapsed)
            self.current_req_start = None
        self.completed_operations += 1
    
    def get_estimated_time_remaining(self):
        """Calculate estimated time remaining"""
        if self.completed_operations == 0:
            return "Calculating..."
        
        elapsed = time.time() - self.start_time
        rate = self.completed_operations / elapsed
        remaining_operations = self.total_operations - self.completed_operations
        
        if rate > 0:
            seconds_remaining = remaining_operations / rate
            remaining_time = timedelta(seconds=int(seconds_remaining))
            return str(remaining_time)
        return "Calculating..."
    
    def get_progress_percentage(self):
        """Get overall progress as percentage"""
        return (self.completed_operations / self.total_operations) * 100

def count_total_files(uploaded_files):
    """Count total files including those in ZIP archives"""
    total = 0
    for file in uploaded_files:
        if file.type == "application/zip":
            with zipfile.ZipFile(file) as z:
                total += sum(1 for f in z.namelist() if f.lower().endswith('.pdf'))
        elif file.type == "application/pdf":
            total += 1
    return total

def process_single_file(filename, file_obj, is_zip, use_voting_system, tracker, file_progress, file_counter, file_status):
    """Process a single file and return scores"""
    tracker.start_file()
    
    # Show current file
    file_status.write(f"Processing: {filename}")
    
    # Reset file progress
    file_progress.progress(0)
    file_counter.write(f"(0/{len(st.session_state.requirements)}) 0%")
    
    try:
        # Extract text from PDF
        if is_zip:
            pdf_bytes = io.BytesIO(file_obj.read())
            cv_text = process_pdf(pdf_bytes)
        else:
            cv_text = process_pdf(file_obj)
        
        if cv_text:
            
            # Store the CV text for later use
            if 'processed_files' not in st.session_state.processing:
                st.session_state.processing['processed_files'] = {}
            st.session_state.processing['processed_files'][filename] = cv_text

            # Score requirements
            scores = []
            total_reqs = len(st.session_state.requirements)
            
            for j, req in enumerate(st.session_state.requirements):
                # Start tracking this requirement
                tracker.start_requirement()
                
                # Use voting if enabled
                if use_voting_system:
                    score = get_openai_score_with_voting(req, cv_text)
                else:
                    score = get_openai_score(req, cv_text)
                
                scores.append({
                    "requirement": req["text"],
                    "score": score,
                    "priority": req["weight"],
                    "type": req["type"]
                })
                
                # Update requirement progress
                file_progress.progress((j+1)/total_reqs)
                file_counter.write(f"({j+1}/{total_reqs}) {int((j+1)/total_reqs*100)}%")
                
                # Mark requirement as complete for timing
                tracker.complete_requirement()
            
            # Complete file tracking
            tracker.complete_file()
            return scores
            
    except Exception as e:
        st.error(f"Error processing {filename}: {str(e)}")
        file_progress.progress(1.0)
        file_counter.write("(Error)")
    
    # Complete file tracking
    tracker.complete_file()
    return None

def process_files(uploaded_files, use_voting_system, background_processing, tracker, ui_components):
    """Process files and return results"""
    # Create progress UI
    overall_progress, overall_counter, file_progress, file_counter, file_status = ui_components.create_progress_ui()
    
    # Dictionary to store results for each CV
    all_results = {}
    file_counter_value = 0
    total_files = tracker.total_files
    
    # Process each file
    for file_idx, uploaded_file in enumerate(uploaded_files):
        # Update overall progress
        overall_progress.progress(file_idx / total_files if total_files > 0 else 0)
        overall_counter.write(f"({file_idx}/{total_files}) {int(file_idx/total_files*100 if total_files > 0 else 0)}%")
        
        if uploaded_file.type == "application/zip":
            # Process ZIP file
            with zipfile.ZipFile(uploaded_file) as z:
                pdf_files = [f for f in z.namelist() if f.lower().endswith('.pdf')]
                
                for i, filename in enumerate(pdf_files):
                    # Process single file from ZIP
                    result = process_single_file(
                        filename, z.open(filename), True, 
                        use_voting_system, tracker,
                        file_progress, file_counter, file_status
                    )
                    
                    if result:
                        all_results[filename] = result
                        
                        # Update current results for partial display
                        st.session_state.processing['current_results'][filename] = result
                        
                        # Rerun to update the UI if showing partial results
                        if background_processing and i % 2 == 0 and i > 0:
                            st.rerun()
                    
                    file_counter_value += 1
        
        elif uploaded_file.type == "application/pdf":
            # Process individual PDF
            result = process_single_file(
                uploaded_file.name, uploaded_file, False, 
                use_voting_system, tracker,
                file_progress, file_counter, file_status
            )
            
            if result:
                all_results[uploaded_file.name] = result
                
                # Update current results for partial display
                st.session_state.processing['current_results'][uploaded_file.name] = result
            
            file_counter_value += 1
        
        # Update overall progress
        overall_progress.progress((file_counter_value) / total_files if total_files > 0 else 0)
        overall_counter.write(f"({file_counter_value}/{total_files}) {int(file_counter_value/total_files*100 if total_files > 0 else 0)}%")
    
    # Complete progress
    file_status.empty()
    file_progress.progress(1.0)
    overall_progress.progress(1.0)
    overall_counter.write(f"({total_files}/{total_files}) 100%")
    
    return all_results

def display_processing_status(tracker):
    """Display processing status information"""
    status_container = st.container()
    with status_container:
        st.subheader("Processing Status")
        
        # Progress bar and percentage
        progress_col, info_col = st.columns([3, 1])
        with progress_col:
            st.progress(tracker.completed_operations / tracker.total_operations if tracker.total_operations > 0 else 0)
        with info_col:
            progress_pct = tracker.get_progress_percentage()
            st.write(f"{progress_pct:.1f}% Complete")
        
        # Status details
        st.write(f"Processed: {tracker.completed_operations}/{tracker.total_operations} operations")
        st.write(f"Estimated time remaining: {tracker.get_estimated_time_remaining()}")
    
    return status_container