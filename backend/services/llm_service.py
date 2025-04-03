from typing import List, Dict, Optional
from transformers import AutoModelForCausalLM, AutoTokenizer
from sentence_transformers import SentenceTransformer
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader
import torch
import os
from datetime import datetime
import json

from ..core.config import settings
from ..models.analysis import AnalysisResult, Severity, VulnerabilityType

class LLMService:
    def __init__(self):
        # Initialize the code generation model
        self.tokenizer = AutoTokenizer.from_pretrained(settings.MODEL_NAME)
        self.model = AutoModelForCausalLM.from_pretrained(
            settings.MODEL_NAME,
            torch_dtype=torch.float16 if settings.DEVICE == "cuda" else torch.float32,
            device_map="auto"
        )
        
        # Initialize the embedding model
        self.embeddings = SentenceTransformer(settings.EMBEDDING_MODEL)
        
        # Initialize vector store
        self.vector_store = Chroma(
            persist_directory="./data/vectorstore",
            embedding_function=self.embeddings
        )
        
        # Initialize prompt template
        self.code_analysis_prompt = """
        Analyze the following {language} code for security vulnerabilities:
        
        Code:
        {code}
        
        Additional Context:
        {context}
        
        Please identify any security vulnerabilities and provide:
        1. Vulnerability type
        2. Severity level (critical, high, medium, low, info)
        3. Description of the vulnerability
        4. Line number (if applicable)
        5. Recommendation for fixing
        6. Confidence score (0-1)
        
        Format your response as JSON.
        """

    async def analyze_code(self, code: str, language: str, file_path: str) -> List[AnalysisResult]:
        """
        Analyze code using LLM for security vulnerabilities
        """
        # Get relevant context from vector store
        context = self._get_relevant_context(code, language)
        
        # Prepare the prompt
        prompt = self.code_analysis_prompt.format(
            code=code,
            language=language,
            context=context
        )
        
        # Generate response
        inputs = self.tokenizer(prompt, return_tensors="pt").to(settings.DEVICE)
        outputs = self.model.generate(
            **inputs,
            max_length=1024,
            num_return_sequences=1,
            temperature=0.1,
            do_sample=True,
            pad_token_id=self.tokenizer.eos_token_id
        )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Parse response and create AnalysisResult objects
        results = self._parse_analysis_response(response, file_path, language)
        return results

    def _get_relevant_context(self, code: str, language: str) -> str:
        """
        Retrieve relevant security context from the vector store
        """
        # Create embeddings for the code
        code_embedding = self.embeddings.encode(code)
        
        # Search for similar documents
        similar_docs = self.vector_store.similarity_search(
            code,
            k=3,
            filter={"language": language}
        )
        
        # Combine context from similar documents
        context = "\n".join([doc.page_content for doc in similar_docs])
        return context

    def _parse_analysis_response(self, response: str, file_path: str, language: str) -> List[AnalysisResult]:
        """
        Parse the LLM response into AnalysisResult objects
        """
        try:
            # Extract JSON from response
            json_str = response.split("```json")[1].split("```")[0].strip()
            vuln_data = json.loads(json_str)
            
            # Convert to AnalysisResult
            return [
                AnalysisResult(
                    id=f"llm_{datetime.now().timestamp()}",
                    project_id="temp",  # Should be passed from the caller
                    file_path=file_path,
                    language=language,
                    vulnerability_type=VulnerabilityType(vuln_data.get("vulnerability_type", "other")),
                    severity=Severity(vuln_data.get("severity", "medium")),
                    description=vuln_data.get("description", "No description provided"),
                    line_number=vuln_data.get("line_number"),
                    code_snippet=vuln_data.get("code_snippet"),
                    recommendation=vuln_data.get("recommendation", "No recommendation provided"),
                    confidence_score=float(vuln_data.get("confidence_score", 0.5)),
                    detection_method="llm",
                    created_at=datetime.now()
                )
            ]
        except Exception as e:
            # Fallback to placeholder if parsing fails
            return [
                AnalysisResult(
                    id=f"llm_{datetime.now().timestamp()}",
                    project_id="temp",
                    file_path=file_path,
                    language=language,
                    vulnerability_type=VulnerabilityType.OTHER,
                    severity=Severity.MEDIUM,
                    description="Failed to parse LLM response",
                    line_number=None,
                    code_snippet=None,
                    recommendation="Please try again or use static analysis",
                    confidence_score=0.5,
                    detection_method="llm",
                    created_at=datetime.now()
                )
            ]

    async def update_knowledge_base(self, security_docs: List[str]):
        """
        Update the vector store with new security documentation
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        for doc in security_docs:
            loader = TextLoader(doc)
            documents = loader.load()
            texts = text_splitter.split_documents(documents)
            self.vector_store.add_documents(texts)
        
        self.vector_store.persist() 