"""
Module: clone_repo.py
Purpose: Handles cloning and Updating Git repositories.
Dependencies: GitPython, logging

This module provides functionality to either clone a new repository or update an existing one,
ensuring the codebase is ready for vulnerability analysis. It includes comprhensive error 
handling and logging to track the repository management process.
"""

import os
import logging
from git import Repo, GitCommandError
from typing import Tuple, Optional
from pathlib import Path

# Configuring logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def clone_or_update_repo(
        repo_url: str,
        destination: str,
        branch: Optional[str] = "main",
) -> Tuple[bool, str]:
    """
    Clone a new repository or update an existing one to the specified branch.

    Args:
        repo_url (str): URL of the Git repository to clone/update
        desitination (str): Local path where the repository should be clone/updated
        branch (str, optional): Branch to checkout. Defaults to "main".

    Returns:
        Tuple[bool, str]: A tuple containing:
            - bool: Success status (True if operation succeeded, False otherwise)
            - str: Success message or error description

    Raises:
        GitCommandError: If Git operations fail
        Exception: If any other unexpected error occurs
    """

    try:
        destination_path = Path(destination)

        # Case 1: Repository already exists
        if destination_path.exists():
            logger.info(f"Repository directory exists at {destination_path}")

            try:
                # Opening existing repository
                repo = Repo(destination)
                logger.info("Successfully opened existing repository")

                # Fetch latest changes from remote
                logger.info("Fetching latest changes from remote")
                repo.remotes.origin.fetch()

                # Ensure we're on the specified branch
                current = repo.active_branch.name
                if current != branch:
                    logger.info(
                        f"Switching from branch '{current}' to branch '{branch}'")
                    repo.git.checkout(branch)

                # Pull latest changes
                repo.remotes.origin.pull()
                logger.info(
                    f"Successfully updated repository to branch '{branch}'")

                return True, f"Repository successfully updated at '{destination}'"

            except GitCommandError as git_err:
                error_msg = f"Git Operation failed: {str(git_err)}"
                logger.error(error_msg)
                return False, error_msg
            except Exception as e:
                error_msg = f"Unexpected error occurred: {str(e)}"
                logger.error(error_msg)
                return False, error_msg 

        # Case 2: New repository needs to be cloned
        else:
            logger.info(f"Cloning new repository to {destination}")

            try:
                # Create parent directories if they don't exist
                destination_path.parent.mkdir(parents=True, exist_ok=True)

                # Clone the repository
                repo = Repo.clone_from(
                    repo_url,
                    destination,
                    branch=branch
                )
                logger.info(f"Successfully cloned repository to {destination}")

                return True, f"Repository successfully cloned to '{destination}'"

            except GitCommandError as git_err:
                error_msg = f"Git Operation failed: {str(git_err)}"
                logger.error(error_msg)
                return False, error_msg
            except Exception as e:
                error_msg = f"Unexpected error occurred: {str(e)}"
                logger.error(error_msg)
                return False, error_msg 
    
    except GitCommandError as git_err:
                error_msg = f"Git Operation failed: {str(git_err)}"
                logger.error(error_msg)
                return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error occurred: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def validate_repo_url(repo_url: str) -> bool:
    """
    Validate if the provided URL appears to be valid Git Repository URL.

    Args:
        repo_url (str): URL to validate

    Returns:
        bool: True if URL appears to be a valid Git Repository URL, False otherwise
    """

    # Basic Validation - check if url ends with .git or it is from a known host
    valid_indicators = [
        '.git',
        'github.com',
        'gitlab.com',
        'bitbucket.org',
        # Add more as needed
    ]

    return any(indicator in repo_url.lower() for indicator in valid_indicators)