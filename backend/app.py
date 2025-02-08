"""
Module: app.py
Purpose: Flask application entry point for the Legacy Guard project

This module implements a REST API service that handles repository management operations.
It serves as the main interface for the frontend to interact with the backend services.
The application uses environment variables for configuration and implements proper error
handling and input validation.

Dependencies:
    - Flask: Web framework for the REST API
    - python-dotenv: For loading environment variables
    - Our custom clone_repo module: For repository management
"""

import os
import logging
from typing import Dict, Tuple, Any
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from werkzeug.exceptions import BadRequest

# Import custom modules
from backend.clone_repo import clone_or_update_repo, validate_repo_url

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize Flask application
app = Flask(__name__)

# Load configuuration from environment variables


class Config:
    """Configuration settings loaded from environment variables."""
    CLONE_DIR = os.getenv('CLONE_DIR', '/tmp/repos')
    DEFAULT_BRANCH = os.getenv('DEFAULT_BRANCH', 'main')
    # Ensure the clone directory exists
    Path(CLONE_DIR).mkdir(parents=True, exist_ok=True)


def validate_clone_request(data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate the repository clone request payload.

    Args:
        data (Dict[str, Any]): The request payload.

    Returns:
        Tuple[bool, str]: Validation result and error message if any.
    """

    if not data:
        return False, "Request payload is empty"

    if 'repo_url' not in data:
        return False, "Repository URL is missing"

    if not validate_repo_url(data['repo_url']):
        return False, "Invalid repository URL"

    return True, ""


@app.route('/', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify the service is running.
    """
    return jsonify({
        'status': 'ok',
        'message': 'Service is running'
    })


@app.route('/clone', methods=['POST'])
def clone_repository():
    """
    API endpoint to clone a repository.

    Expected JSON Payload:
        {
            repo_url (str): The URL of the repository to clone.
            branch (str, optional): The branch to clone. Defaults to 'main'.
        }

    Returns:
        JSON response with the clone status.
    """

    try:
        # Parse and validate request data
        data = request.get_json()
        is_valid, error_message = validate_clone_request(data)

        if not is_valid:
            raise BadRequest(error_message)

        # Extract parameters
        repo_url = data['repo_url']
        branch = data.get('branch', Config.DEFAULT_BRANCH)

        # Generate a unique clone directory name
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        destination_dir = os.path.join(Config.CLONE_DIR, repo_name)

        # Attempt to clone/update the directory
        success, message = clone_or_update_repo(
            repo_url=repo_url,
            destination=destination_dir,
            branch=branch
        )

        if success:
            logging.info(f"Successfully cloned repository: {repo_url}")
            reponse = {
                'status': 'success',
                'message': message,
                'data': {
                    'repo_name': repo_name,
                    'destination': destination_dir,
                    'branch': branch
                }
            }
            return jsonify(reponse), 200

        else:
            logging.error(f"Failed to clone repository: {message}")
            response = {
                'status': 'error',
                'message': message
            }
            return jsonify(response), 400

    except BadRequest as e:
        logging.error(f"Bad request: {str(e)}")
        response = {
            'status': 'error',
            'message': str(e)
        }
        return jsonify(response), 400

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        response = {
            'status': 'error',
            'message': 'An unexpected error occurred'
        }
        return jsonify(response), 500


@app.errorhandler(404)
def not_found(error):
    """"Handle 404 errors"""
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found'
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify({
        'status': 'error',
        'message': 'Method not allowed'
    }), 405


if __name__ == '__main__':
    # Get port from environment variable or use a default
    port = int(os.getenv('PORT', 5000))

    # Start the Flask application
    app.run(
        host='0.0.0.0',
        port=port,
        debug=os.getenv('FLASK_ENV') == 'development'
    )
