# LegacyGuard

LegacyGuard is an open-source tool that combines LLM-based semantic analysis, RAG (Retrieval-Augmented Generation), and static analysis for detecting vulnerabilities in legacy codebases across multiple programming languages.

## Features

- Multi-language support for legacy codebases (COBOL, C/C++, Java, FORTRAN, etc.)
- Hybrid analysis approach combining:
  - LLM-based semantic analysis
  - RAG for security knowledge enrichment
  - Static analysis tools
- Modular and extensible architecture
- Web-based interface for code analysis and reporting

## Tech Stack

- **Frontend**: Next.js
- **Backend**: Python (FastAPI)
- **LLM Integration**: Langchain
- **Databases**: 
  - ChromaDB (Vector DB for RAG)
  - PostgreSQL (Structured storage)
- **Static Analysis**: Integration with multiple SAST tools
- **Deployment**: AWS/Hugging Face Spaces

## Project Structure

```
legacy-guard/
├── frontend/                 # Next.js frontend application
├── backend/                  # FastAPI backend service
│   ├── api/                 # API endpoints
│   ├── core/               # Core business logic
│   ├── models/             # Data models
│   ├── services/           # Business services
│   └── utils/              # Utility functions
├── static_analysis/         # Static analysis tools integration
├── llm/                     # LLM and RAG components
├── docs/                    # Documentation
└── tests/                   # Test suite
```

## Getting Started

[Installation instructions will be added]
   docker-compose up --build
   docker-compose down

## Development

[Development setup instructions will be added]

## Contributing

[Contribution guidelines will be added]

## License

[License information will be added] 