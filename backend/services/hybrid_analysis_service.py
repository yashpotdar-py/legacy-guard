from typing import List, Dict, Optional
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor

from .llm_service import LLMService
from .static_analysis_service import StaticAnalysisService
from ..models.analysis import AnalysisResult, ProjectAnalysis

logger = logging.getLogger(__name__)

class HybridAnalysisService:
    def __init__(self):
        self.llm_service = LLMService()
        self.static_service = StaticAnalysisService()
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def analyze_project(
        self,
        project_id: str,
        project_name: str,
        project_path: str,
        language: str
    ) -> ProjectAnalysis:
        """
        Perform hybrid analysis combining LLM and static analysis
        """
        start_time = datetime.now()
        
        try:
            # Run LLM and static analysis in parallel
            llm_results, static_results = await self._run_parallel_analysis(
                project_path,
                language
            )
            
            # Combine and deduplicate results
            combined_results = self._combine_results(llm_results, static_results)
            
            # Generate summary
            summary = self._generate_summary(combined_results)
            
            return ProjectAnalysis(
                project_id=project_id,
                project_name=project_name,
                total_files=0,  # TODO: Implement file counting
                analyzed_files=0,  # TODO: Implement analyzed files tracking
                vulnerabilities_found=len(combined_results),
                analysis_start_time=start_time,
                analysis_end_time=datetime.now(),
                results=combined_results,
                summary=summary,
                status="completed"
            )
            
        except Exception as e:
            logger.error(f"Error in hybrid analysis: {str(e)}")
            return ProjectAnalysis(
                project_id=project_id,
                project_name=project_name,
                total_files=0,
                analyzed_files=0,
                vulnerabilities_found=0,
                analysis_start_time=start_time,
                analysis_end_time=datetime.now(),
                results=[],
                summary={},
                status="failed",
                error_message=str(e)
            )

    async def _run_parallel_analysis(
        self,
        project_path: str,
        language: str
    ) -> tuple[List[AnalysisResult], List[AnalysisResult]]:
        """
        Run LLM and static analysis in parallel
        """
        # Run both analyses concurrently
        llm_task = self.llm_service.analyze_code(
            code=self._get_project_code(project_path),
            language=language,
            file_path=project_path
        )
        
        static_task = self.static_service.analyze_project(
            project_path=project_path,
            language=language
        )
        
        llm_results, static_results = await asyncio.gather(llm_task, static_task)
        return llm_results, static_results

    def _combine_results(
        self,
        llm_results: List[AnalysisResult],
        static_results: List[AnalysisResult]
    ) -> List[AnalysisResult]:
        """
        Combine and deduplicate results from different analysis methods
        """
        # Create a map of unique vulnerabilities based on file and line number
        unique_vulns = {}
        
        # Process static analysis results first (higher confidence)
        for result in static_results:
            key = f"{result.file_path}:{result.line_number}"
            unique_vulns[key] = result
        
        # Process LLM results, only adding if not already present
        for result in llm_results:
            key = f"{result.file_path}:{result.line_number}"
            if key not in unique_vulns:
                unique_vulns[key] = result
        
        return list(unique_vulns.values())

    def _generate_summary(self, results: List[AnalysisResult]) -> Dict[str, int]:
        """
        Generate a summary of vulnerabilities by severity
        """
        summary = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        }
        
        for result in results:
            summary[result.severity.value] += 1
        
        return summary

    def _get_project_code(self, project_path: str) -> str:
        """
        Read and combine code from project files
        """
        # TODO: Implement proper code reading and combining
        # This is a placeholder implementation
        return "// Placeholder code"

    async def update_analysis_configs(
        self,
        llm_config: Optional[Dict] = None,
        static_config: Optional[Dict] = None
    ):
        """
        Update configurations for both analysis methods
        """
        if llm_config:
            await self.llm_service.update_knowledge_base(
                llm_config.get("security_docs", [])
            )
        
        if static_config:
            await self.static_service.update_tool_configs(
                static_config.get("tool_configs", {})
            ) 