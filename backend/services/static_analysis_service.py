from typing import List, Dict, Optional
import subprocess
import json
import os
from datetime import datetime
import logging

from ..core.config import settings
from ..models.analysis import AnalysisResult, Severity, VulnerabilityType

logger = logging.getLogger(__name__)

class StaticAnalysisService:
    def __init__(self):
        self.tools = settings.STATIC_ANALYSIS_TOOLS
        self.tool_configs = self._load_tool_configs()

    def _load_tool_configs(self) -> Dict:
        """
        Load configurations for different static analysis tools
        """
        # TODO: Load from configuration file
        return {
            "codesonar": {
                "command": "codesonar",
                "args": ["analyze", "-project", "{project_path}"]
            },
            "findbugs": {
                "command": "findbugs",
                "args": ["-textui", "-xml:withMessages", "{project_path}"]
            },
            "veracode": {
                "command": "veracode",
                "args": ["scan", "-project", "{project_path}"]
            }
        }

    async def analyze_project(self, project_path: str, language: str) -> List[AnalysisResult]:
        """
        Run static analysis on the project using configured tools
        """
        results = []
        
        for tool in self.tools:
            try:
                tool_results = await self._run_tool(tool, project_path, language)
                results.extend(tool_results)
            except Exception as e:
                logger.error(f"Error running {tool}: {str(e)}")
                continue
        
        return results

    async def _run_tool(self, tool: str, project_path: str, language: str) -> List[AnalysisResult]:
        """
        Run a specific static analysis tool
        """
        if tool not in self.tool_configs:
            logger.warning(f"Tool {tool} not configured")
            return []

        config = self.tool_configs[tool]
        command = [config["command"]]
        args = [arg.format(project_path=project_path) for arg in config["args"]]
        command.extend(args)

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"Tool {tool} failed: {stderr.decode()}")
                return []

            return self._parse_tool_output(tool, stdout.decode(), language)

        except Exception as e:
            logger.error(f"Error running {tool}: {str(e)}")
            return []

    def _parse_tool_output(self, tool: str, output: str, language: str) -> List[AnalysisResult]:
        """
        Parse the output of a static analysis tool
        """
        # TODO: Implement proper parsing for each tool's output format
        # This is a placeholder implementation
        return [
            AnalysisResult(
                id=f"static_{tool}_{datetime.now().timestamp()}",
                project_id="temp",  # Should be passed from the caller
                file_path="unknown",  # Should be extracted from tool output
                language=language,
                vulnerability_type=VulnerabilityType.OTHER,
                severity=Severity.MEDIUM,
                description=f"Placeholder vulnerability from {tool}",
                line_number=None,
                code_snippet=None,
                recommendation="Placeholder recommendation",
                confidence_score=0.8,  # Static analysis typically has higher confidence
                detection_method="static",
                created_at=datetime.now()
            )
        ]

    async def update_tool_configs(self, new_configs: Dict):
        """
        Update the configurations for static analysis tools
        """
        self.tool_configs.update(new_configs)
        # TODO: Persist configurations to file 