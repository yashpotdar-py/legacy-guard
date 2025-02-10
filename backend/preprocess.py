"""
Module: preprocess.py
Purpose: Preprocesses repository code files for vulnerability analysis

This module handles the initial processing of code files from a cloned repository.
It performs several key functions:
1. Identifying relevant code files based on their extensions
2. Reading file contents with proper encoding detection
3. Chunking large files into manageable segments
4. Creating a structured representation of the codebase

The output of this module serves as input for both static analysis and LLM-based
analysis, making it a critical component in the vulnerability detection pipeline.
"""

import os
import logging
from typing import List, Dict, Set, Optional, Iterator
from pathlib import Path
import chardet
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Default configuration (can be overridden via environment variables)
ALLOWED_EXTENSIONS = {
    # Web technologies
    '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.php',
    # Systems programming
    '.c', '.cpp', '.h', '.hpp', '.rs', '.go',
    # JVM languages
    '.java', '.scala', '.kt',
    # Python
    '.py', '.pyw', '.pyx',
    # .NET
    '.cs', '.vb', '.fs',
    # Shell scripts
    '.sh', '.bash', '.zsh',
    # Configuration
    '.xml', '.json', '.yaml', '.yml'
}


def list_code_files(
    repository_path: str,
    allowed_extensions: Optional[Set[str]] = None
) -> Iterator[Path]:
    """
    Recursively identify code files in the repository that match allowed extensions.

    This function walks through the repository directory and yields paths to files
    that have extensions matching our criteria. It automatically skips common
    directories that shouldn't be analyzed (like .git, node_modules, etc.).

    Args:
        repository_path (str): Path to the root of the repository
        allowed_extensions (Set[str], optional): Set of file extensions to include.
            Defaults to ALLOWED_EXTENSIONS if None.

    Yields:
        Path: Path objects for each matching file found

    Example:
        >>> for file_path in list_code_files('./my-repo'):
        ...     print(f"Found code file: {file_path}")
    """
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_EXTENSIONS

    # Directories to skip (common build and dependency directories)
    SKIP_DIRS = {
        '.git', 'node_modules', 'venv', '__pycache__',
        'build', 'dist', 'target', 'bin', 'obj'
    }

    try:
        repo_path = Path(repository_path)
        for root, dirs, files in os.walk(repository_path):
            # Skip unwanted directories
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in allowed_extensions:
                    yield file_path

    except Exception as e:
        logger.error(f"Error scanning repository: {str(e)}")
        raise


def read_file(file_path: Path) -> Optional[str]:
    """
    Safely read a file's contents with automatic encoding detection.

    This function attempts to read a file while handling various potential issues:
    - Automatic encoding detection using chardet
    - Fallback to common encodings if detection fails
    - Graceful handling of read errors

    Args:
        file_path (Path): Path to the file to read

    Returns:
        Optional[str]: File contents if successful, None if file couldn't be read

    Example:
        >>> content = read_file(Path('./src/main.py'))
        >>> if content:
        ...     print(f"File has {len(content)} characters")
    """
    try:
        # First try: Read raw bytes and detect encoding
        raw_bytes = file_path.read_bytes()
        result = chardet.detect(raw_bytes)
        encoding = result['encoding'] if result['confidence'] > 0.7 else 'utf-8'

        try:
            return raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            # Second try: Attempt common encodings
            for enc in ['utf-8', 'latin-1', 'cp1252', 'ascii']:
                try:
                    return raw_bytes.decode(enc)
                except UnicodeDecodeError:
                    continue

            # If all attempts fail, log and return None
            logger.warning(f"Failed to decode {file_path} with any encoding")
            return None

    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        return None


def chunk_text(
    text: str,
    max_lines: int = 50,
    overlap_lines: int = 5
) -> List[str]:
    """
    Split text into overlapping chunks based on line count.

    This function creates chunks of text that are suitable for processing by LLMs
    or static analysis tools. It maintains context by including overlapping lines
    between chunks.

    Args:
        text (str): The text content to split
        max_lines (int): Maximum number of lines per chunk
        overlap_lines (int): Number of lines to overlap between chunks

    Returns:
        List[str]: List of text chunks

    Example:
        >>> text = "line1\\nline2\\nline3\\nline4\\nline5"
        >>> chunks = chunk_text(text, max_lines=2, overlap_lines=1)
        >>> for i, chunk in enumerate(chunks):
        ...     print(f"Chunk {i}: {chunk}")
    """
    lines = text.splitlines()
    chunks = []

    # Handle empty or small files
    if len(lines) <= max_lines:
        return [text]

    # Create overlapping chunks
    start = 0
    while start < len(lines):
        # Calculate end position for this chunk
        end = min(start + max_lines, len(lines))

        # Create chunk from lines
        chunk = '\n'.join(lines[start:end])
        chunks.append(chunk)

        # Move start position for next chunk, accounting for overlap
        start = end - overlap_lines if end < len(lines) else len(lines)

    return chunks


def preprocess_repository(
    repository_path: str,
    max_lines_per_chunk: int = 50,
    overlap_lines: int = 5
) -> Dict[str, List[str]]:
    """
    Process all code files in a repository and prepare them for analysis.

    This function orchestrates the entire preprocessing pipeline:
    1. Finding all relevant code files
    2. Reading their contents
    3. Chunking large files
    4. Creating a structured representation

    Args:
        repository_path (str): Path to the repository root
        max_lines_per_chunk (int): Maximum lines per text chunk
        overlap_lines (int): Number of overlapping lines between chunks

    Returns:
        Dict[str, List[str]]: Mapping of file paths to their content chunks

    Example:
        >>> repo_data = preprocess_repository('./my-repo')
        >>> for file_path, chunks in repo_data.items():
        ...     print(f"{file_path}: {len(chunks)} chunks")
    """
    processed_files: Dict[str, List[str]] = {}
    file_count = 0
    error_count = 0

    logger.info(f"Starting preprocessing of repository: {repository_path}")

    try:
        for file_path in list_code_files(repository_path):
            file_count += 1
            relative_path = str(file_path.relative_to(repository_path))

            # Read file contents
            content = read_file(file_path)
            if content is None:
                error_count += 1
                continue

            # Create chunks
            chunks = chunk_text(
                content,
                max_lines=max_lines_per_chunk,
                overlap_lines=overlap_lines
            )

            # Store results
            processed_files[relative_path] = chunks

        logger.info(
            f"Preprocessing complete:\n"
            f"- Files processed: {file_count}\n"
            f"- Files with errors: {error_count}\n"
            f"- Total files chunked: {len(processed_files)}"
        )

        return processed_files

    except Exception as e:
        logger.error(f"Fatal error during preprocessing: {str(e)}")
        raise


if __name__ == "__main__":
    """
    Main execution block for testing the preprocessing module.

    This allows the module to be run standalone for testing purposes.
    It will process the repository specified in CLONE_DIR environment
    variable and print out a summary of the results.
    """
    # Get repository path from environment
    repository_path = os.getenv('CLONE_DIR')
    if not repository_path:
        print("Error: CLONE_DIR environment variable not set")
        exit(1)

    try:
        # Process the repository
        results = preprocess_repository(repository_path)

        # Print summary
        print("\nPreprocessing Results Summary:")
        print("-" * 40)
        print(f"Total files processed: {len(results)}")

        # Show preview of first few files
        print("\nFile Previews:")
        for path, chunks in list(results.items())[:3]:
            print(f"\nFile: {path}")
            print(f"Number of chunks: {len(chunks)}")
            if chunks:
                preview = chunks[0][:200] + \
                    "..." if len(chunks[0]) > 200 else chunks[0]
                print(f"First chunk preview:\n{preview}")

    except Exception as e:
        print(f"Error during preprocessing: {str(e)}")
        exit(1)
