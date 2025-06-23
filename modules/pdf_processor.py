from pypdf import PdfReader
import streamlit as st
import io

def process_pdf(pdf_file) -> str:
    """Extract text from a PDF file"""
    try:
        pdf_reader = PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        return ""