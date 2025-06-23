import os
import json
import streamlit as st

def get_templates_directory():
    """
    Get the absolute path to the requirement templates directory
    
    Returns:
        str: Path to the requirement templates directory
    """
    # Get the current script's directory (modules)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Go to the parent directory and then into requirement_templates
    templates_dir = os.path.join(os.path.dirname(current_dir), 'requirement_templates')
    
    # Ensure the directory exists
    os.makedirs(templates_dir, exist_ok=True)
    
    return templates_dir

def load_templates_from_folder():
    """
    Dynamically load all JSON templates from the templates directory
    
    Returns:
        dict: A dictionary of templates with position names as keys
    """
    templates = {}
    templates_dir = get_templates_directory()
    
    # Iterate through all files in the directory
    for filename in os.listdir(templates_dir):
        # Only process JSON files
        if filename.endswith('.json'):
            try:
                filepath = os.path.join(templates_dir, filename)
                
                # Read the JSON file
                with open(filepath, 'r') as f:
                    template_data = json.load(f)
                
                # Convert filename to a readable position name
                # Remove .json and convert underscores to spaces, then title case
                position_name = (filename.replace('.json', '')
                                         .replace('_', ' ')
                                         .title())
                
                # Extract requirements (assuming a consistent structure)
                requirements = template_data.get('requirements', [])
                
                # Add to templates if requirements exist
                if requirements:
                    templates[position_name] = requirements
            
            except json.JSONDecodeError:
                st.error(f"Error decoding JSON from {filename}")
            except Exception as e:
                st.error(f"Error processing template {filename}: {e}")
    
    return templates

class RequirementTemplateManager:
    """Manage requirement templates for different job positions"""
    
    def __init__(self):
        """Initialize template manager"""
        self.templates_dir = get_templates_directory()
        self.templates = self.load_templates()
    
    def load_templates(self):
        """Load templates using the flexible loader"""
        return load_templates_from_folder()
    
    def get_template_positions(self):
        """Get available job positions with templates"""
        return list(self.templates.keys())
    
    def get_template_requirements(self, position):
        """Get requirements for a specific position"""
        return self.templates.get(position, [])
    
    def save_template(self, position, requirements):
        """Save a template to a JSON file"""
        # Convert position name to filename
        filename = position.lower().replace(' ', '_') + '.json'
        filepath = os.path.join(self.templates_dir, filename)
        
        try:
            # Prepare data structure
            template_data = {
                "requirements": requirements
            }
            
            # Write to file
            with open(filepath, 'w') as f:
                json.dump(template_data, f, indent=4)
            
            # Refresh templates
            self.templates = self.load_templates()
            return True
        
        except Exception as e:
            st.error(f"Error saving template {position}: {e}")
            return False
    
    def create_new_template(self, position, requirements):
        """Create a new template if it doesn't exist"""
        if position in self.templates:
            st.warning(f"Template for {position} already exists.")
            return False
        
        return self.save_template(position, requirements)