"""
Module: streamlit_app.py
Purpose: Streamlit frontend for the Legacy Guard project

This module implements an interactive web interface using Streamlit that allows users to:
1. Input repository details for analysis
2. Trigger repository cloning/updating operations
3. View operation results
4. Access API documentation

The application serves both as a user interface and as living documentation for API integration.
"""

import os
import json
import requests
from typing import Tuple, Dict, Any
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()

# Configuration
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:5000')
DEFAULT_BRANCH = os.getenv('DEFAULT_BRANCH', 'main')


def make_api_request(repo_url: str, branch: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Send a repository cloning request to the backend API.

    Args:
        repo_url (str): URL of the Git repository
        branch (str): Name of the branch to clone/update

    Returns:
        Tuple[bool, str, Dict[str, Any]]: Success status, message, and response data
    """
    try:
        response = requests.post(
            f"{BACKEND_URL}/clone",
            json={
                "repo_url": repo_url,
                "branch": branch
            },
            headers={"Content-Type": "application/json"}
        )

        data = response.json()

        if response.status_code == 200:
            return True, data.get('message', 'Success'), data.get('data', {})
        else:
            return False, data.get('message', 'Unknown error'), {}

    except requests.exceptions.RequestException as e:
        return False, f"Failed to connect to backend: {str(e)}", {}


def main():
    """Main function that defines the Streamlit interface"""

    # Set page configuration
    st.set_page_config(
        page_title="Legacy Guard - Repository Manager",
        page_icon="🛡️",
        layout="wide"
    )

    # Title and description
    st.title("🛡️ Legacy Guard - Repository Manager")
    st.markdown("""
    Welcome to Legacy Guard's Repository Manager. This tool helps you analyze legacy codebases
    for potential vulnerabilities by combining traditional static analysis with advanced LLM-based
    techniques.
    
    Start by providing the details of the repository you want to analyze:
    """)

    # Create a form for repository details
    with st.form("repo_form"):
        # Repository URL input
        repo_url = st.text_input(
            "Repository URL",
            placeholder="https://github.com/username/repo.git",
            help="Enter the full URL of the Git repository you want to analyze"
        )

        # Branch selection
        branch = st.text_input(
            "Branch (optional)",
            value=DEFAULT_BRANCH,
            help="Specify the branch to analyze. Defaults to 'main' if not provided"
        )

        # Submit button
        submit_button = st.form_submit_button("Clone/Update Repository")

    # Handle form submission
    if submit_button:
        if not repo_url:
            st.error("Please provide a repository URL")
        else:
            # Show progress indicator
            with st.spinner("Processing repository..."):
                success, message, data = make_api_request(repo_url, branch)

                if success:
                    st.success(message)
                    if data:
                        st.json(data)
                else:
                    st.error(message)

    # API Documentation Section
    st.markdown("---")
    st.header("API Integration Guide")
    st.markdown("""
    The Repository Manager provides a RESTful API that can be integrated with other systems.
    Below is the documentation for available endpoints:
    
    ### Clone/Update Repository Endpoint
    
    **Endpoint:** `/clone`  
    **Method:** POST  
    **Content-Type:** application/json
    
    #### Request Payload:
    ```json
    {
        "repo_url": "https://github.com/username/repo.git",
        "branch": "main"  // optional, defaults to configured DEFAULT_BRANCH
    }
    ```
    
    #### Success Response (200 OK):
    ```json
    {
        "status": "success",
        "message": "Repository successfully cloned/updated",
        "data": {
            "repository_path": "/path/to/repository",
            "branch": "main"
        }
    }
    ```
    
    #### Error Response (400 Bad Request):
    ```json
    {
        "status": "error",
        "message": "Error description"
    }
    ```
    
    ### Integration Example (Python):
    ```python
    import requests
    
    response = requests.post(
        "http://localhost:5000/clone",
        json={
            "repo_url": "https://github.com/username/repo.git",
            "branch": "main"
        },
        headers={"Content-Type": "application/json"}
    )
    
    result = response.json()
    print(result)
    ```
    
    ### Integration Example (curl):
    ```bash
    curl -X POST http://localhost:5000/clone \\
         -H "Content-Type: application/json" \\
         -d '{"repo_url": "https://github.com/username/repo.git", "branch": "main"}'
    ```
    """)


if __name__ == "__main__":
    main()
