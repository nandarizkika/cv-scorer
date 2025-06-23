# 🤖 AI-Powered CV Scoring Engine

## Overview

The AI-Powered CV Scoring Engine is an advanced, automated candidate screening tool that leverages artificial intelligence to evaluate and compare job candidates based on predefined requirements.

![Application Screenshot](screenshot.png)

## 🌟 Key Features

- **AI-Powered Candidate Screening**
  - Automated CV analysis
  - Intelligent requirement matching
  - Comprehensive candidate evaluation

- **Multi-Model Scoring**
  - Optional multi-model voting system
  - Increased accuracy through ensemble AI models
  - Configurable scoring thresholds

- **Detailed Reporting**
  - Instant candidate comparison
  - Detailed requirement-based scoring
  - AI-generated candidate summaries

- **Robust Audit Logging**
  - Comprehensive evaluation tracking
  - Exportable audit logs
  - Risk assessment for each candidate

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Streamlit
- OpenAI API Key

### Installation

1. Clone the repository
```bash
git clone https://github.com/nandarizkika/cv-scorer.git
cd cv-scoring-engine
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Set up OpenAI API Key
   - Create a `.streamlit/secrets.toml` file
   - Add your OpenAI API key:
     ```toml
     OPENAI_API_KEY = "your-openai-api-key"
     ```

### Running the Application

```bash
streamlit run app.py
```

## 📋 Usage Guide

1. **Define Job Requirements**
   - Use the sidebar to add job requirements
   - Set priority and scoring type for each requirement
   - Use predefined templates or create custom requirements

2. **Upload CVs**
   - Support for single PDFs and ZIP files
   - Drag and drop or browse files
   - Maximum file size: 200MB per file

3. **Analyze Candidates**
   - Choose scoring options
     - Multi-Model Voting
     - Partial Results Display
   - Click "Analyze CVs"

4. **Review Results**
   - View comprehensive candidate comparison
   - Detailed individual CV analysis
   - AI-generated summaries and interview questions

## 🛠 Configuration Options

- **AI Models**
  - Standard: `gpt-4o-mini`
  - Advanced: `gpt-4o`
  - Multi-model voting support

- **Scoring Thresholds**
  - Configurable performance levels
  - Customizable requirement weights

## 📊 Audit Logging

- Comprehensive evaluation tracking
- Exportable logs (CSV and JSON)
- Candidate risk assessment
- Detailed processing metadata

## 🔒 Privacy and Security

- Personal data anonymization
- Secure candidate ID generation
- Compliance with data protection standards

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📜 License

[Specify your license, e.g., MIT License]

## 🙌 Acknowledgements

- OpenAI for powering the AI models
- Streamlit for the application framework
- All contributors and supporters

## 📞 Support

For issues, feature requests, or support:
- Open a GitHub Issue
- Contact: +6282117683153

---

**Disclaimer**: This tool is designed to assist in the candidate screening process and should not be the sole basis for hiring decisions.
