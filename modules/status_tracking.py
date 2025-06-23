import streamlit as st
import time
from datetime import datetime, timedelta

class BatchProcessingStatus:
    """Track and display batch processing status"""
    
    def __init__(self, total_items, process_name="Processing"):
        """Initialize with total number of items to process"""
        # Make sure we have a place to store status
        if 'processing_status' not in st.session_state:
            st.session_state.processing_status = {}
        
        self.process_id = f"{process_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        st.session_state.processing_status[self.process_id] = {
            'start_time': time.time(),
            'total_items': total_items,
            'completed_items': 0,
            'current_item': None,
            'estimated_completion': None,
            'item_times': [],
            'status': 'running'
        }
    
    def update(self, completed_items, current_item=None):
        """Update processing status"""
        status = st.session_state.processing_status[self.process_id]
        
        # Calculate time per item
        elapsed = time.time() - status['start_time']
        if completed_items > 0:
            time_per_item = elapsed / completed_items
            status['item_times'].append(time_per_item)
            
            # Calculate average time for last 3 items (or all if fewer than 3)
            recent_times = status['item_times'][-min(3, len(status['item_times'])):]
            avg_time = sum(recent_times) / len(recent_times)
            
            # Estimate completion time
            remaining_items = status['total_items'] - completed_items
            est_remaining_seconds = remaining_items * avg_time
            status['estimated_completion'] = timedelta(seconds=int(est_remaining_seconds))
        
        status['completed_items'] = completed_items
        status['current_item'] = current_item
        
        # Check if complete
        if completed_items >= status['total_items']:
            status['status'] = 'completed'
    
    def display_status(self, container=None):
        """Display current status in the provided container"""
        status = st.session_state.processing_status[self.process_id]
        display_container = container if container else st
        
        # Progress bar
        progress = status['completed_items'] / status['total_items']
        display_container.progress(progress)
        
        # Status text
        status_text = f"Processing: {status['completed_items']}/{status['total_items']} "
        if status['current_item']:
            status_text += f"(Current: {status['current_item']})"
        
        display_container.text(status_text)
        
        # Estimated time remaining
        if status['estimated_completion'] and status['status'] == 'running':
            display_container.text(f"Estimated time remaining: {status['estimated_completion']}")
        elif status['status'] == 'completed':
            elapsed = time.time() - status['start_time']
            display_container.text(f"Processing completed in {timedelta(seconds=int(elapsed))}")
    
    def is_complete(self):
        """Check if processing is complete"""
        return st.session_state.processing_status[self.process_id]['status'] == 'completed'