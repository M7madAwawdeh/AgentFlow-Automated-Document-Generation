"""
Documenter Agent - Generates comprehensive documentation for code elements
Analyzes PHP classes, methods, functions, and routes to create clear explanations
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from langchain_core.messages import HumanMessage

from .base_agent import BaseAgent, AgentConfig, AgentResult

logger = logging.getLogger(__name__)

@dataclass
class DocumentationElement:
    """Represents a documented code element"""
    element_type: str  # class, method, function, route, model, migration
    element_name: str
    file_path: str
    line_number: Optional[int] = None
    description: str = ""
    parameters: List[Dict[str, Any]] = None
    return_value: str = ""
    examples: List[str] = None
    code_snippets: List[str] = None
    dependencies: List[str] = None
    related_elements: List[str] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = []
        if self.examples is None:
            self.examples = []
        if self.code_snippets is None:
            self.code_snippets = []
        if self.dependencies is None:
            self.dependencies = []
        if self.related_elements is None:
            self.related_elements = []

class DocumenterAgent(BaseAgent):
    """
    AI Agent specialized in generating comprehensive code documentation
    
    Capabilities:
    - Analyze PHP classes, methods, and functions
    - Generate clear descriptions and examples
    - Identify parameters and return values
    - Create usage examples and code snippets
    - Document routes and API endpoints
    - Generate model and migration documentation
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        # Set default configuration for documentation
        if config is None:
            config = AgentConfig(
                model="llama-3-70b",
                temperature=0.1,
                max_tokens=6000,
                tone="professional"
            )
        
        super().__init__(config)
        
        # Documentation patterns and templates
        self.documentation_patterns = {
            "class": r"class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w\s,]+))?",
            "method": r"(?:public|private|protected|static)?\s*function\s+(\w+)\s*\(",
            "function": r"function\s+(\w+)\s*\(",
            "route": r"Route::(?:get|post|put|patch|delete)\s*\(\s*['\"]([^'\"]+)['\"]",
            "model": r"class\s+(\w+)\s+extends\s+Model",
            "migration": r"class\s+(\w+)\s+extends\s+Migration"
        }
    
    async def analyze(
        self,
        parsed_elements: Dict[str, Any],
        project_id: int,
        model: Optional[str] = None,
        tone: Optional[str] = None
    ) -> AgentResult:
        """
        Analyze parsed code elements and generate documentation
        
        Args:
            parsed_elements: Parsed code elements from the parser
            project_id: Database project ID
            model: Override default model
            tone: Override default tone
        
        Returns:
            AgentResult with generated documentation
        """
        try:
            if model:
                self.config.model = model
            if tone:
                self.config.tone = tone
            
            logger.info(f"Starting documentation analysis for project {project_id}")
            
            # Extract documentation elements from parsed code
            doc_elements = self._extract_documentation_elements(parsed_elements)
            
            # Generate documentation for each element
            documented_elements = []
            
            for element in doc_elements:
                try:
                    documentation = await self._generate_element_documentation(element)
                    if documentation:
                        documented_elements.append(documentation)
                except Exception as e:
                    logger.warning(f"Failed to document element {element.element_name}: {e}")
                    continue
            
            # Create comprehensive documentation report
            documentation_report = {
                "project_id": project_id,
                "total_elements": len(doc_elements),
                "documented_elements": len(documented_elements),
                "elements": documented_elements,
                "summary": self._generate_documentation_summary(documented_elements),
                "metadata": {
                    "agent": "documenter",
                    "model": self.config.model,
                    "tone": self.config.tone,
                    "timestamp": self.last_run.isoformat() if self.last_run else None
                }
            }
            
            logger.info(f"Documentation analysis completed for project {project_id}")
            
            return AgentResult(
                success=True,
                data=documentation_report,
                metadata={
                    "model": self.config.model,
                    "tone": self.config.tone,
                    "elements_processed": len(doc_elements),
                    "elements_documented": len(documented_elements)
                }
            )
            
        except Exception as e:
            logger.error(f"Documentation analysis failed: {e}")
            return AgentResult(
                success=False,
                data={},
                metadata={"error": str(e)},
                errors=[str(e)]
            )
    
    def _extract_documentation_elements(self, parsed_elements: Dict[str, Any]) -> List[DocumentationElement]:
        """Extract documentation elements from parsed code"""
        elements = []
        
        for file_path, file_data in parsed_elements.items():
            try:
                file_content = file_data.get("content", "")
                file_lines = file_content.split('\n')
                
                # Extract classes
                class_matches = re.finditer(self.documentation_patterns["class"], file_content)
                for match in class_matches:
                    class_name = match.group(1)
                    extends = match.group(2)
                    implements = match.group(3)
                    
                    element = DocumentationElement(
                        element_type="class",
                        element_name=class_name,
                        file_path=file_path,
                        line_number=self._find_line_number(file_lines, match.start()),
                        dependencies=[extends] if extends else [],
                        related_elements=[implements] if implements else []
                    )
                    elements.append(element)
                
                # Extract methods and functions
                method_matches = re.finditer(self.documentation_patterns["method"], file_content)
                for match in method_matches:
                    method_name = match.group(1)
                    
                    element = DocumentationElement(
                        element_type="method",
                        element_name=method_name,
                        file_path=file_path,
                        line_number=self._find_line_number(file_lines, match.start())
                    )
                    elements.append(element)
                
                # Extract routes
                route_matches = re.finditer(self.documentation_patterns["route"], file_content)
                for match in route_matches:
                    route_path = match.group(1)
                    
                    element = DocumentationElement(
                        element_type="route",
                        element_name=route_path,
                        file_path=file_path,
                        line_number=self._find_line_number(file_lines, match.start())
                    )
                    elements.append(element)
                
                # Extract models
                model_matches = re.finditer(self.documentation_patterns["model"], file_content)
                for match in model_matches:
                    model_name = match.group(1)
                    
                    element = DocumentationElement(
                        element_type="model",
                        element_name=model_name,
                        file_path=file_path,
                        line_number=self._find_line_number(file_lines, match.start())
                    )
                    elements.append(element)
                
                # Extract migrations
                migration_matches = re.finditer(self.documentation_patterns["migration"], file_content)
                for match in migration_matches:
                    migration_name = match.group(1)
                    
                    element = DocumentationElement(
                        element_type="migration",
                        element_name=migration_name,
                        file_path=file_path,
                        line_number=self._find_line_number(file_lines, match.start())
                    )
                    elements.append(element)
                
            except Exception as e:
                logger.warning(f"Failed to extract elements from {file_path}: {e}")
                continue
        
        return elements
    
    def _find_line_number(self, lines: List[str], char_position: int) -> Optional[int]:
        """Find the line number for a character position"""
        try:
            current_pos = 0
            for i, line in enumerate(lines):
                current_pos += len(line) + 1  # +1 for newline
                if current_pos > char_position:
                    return i + 1
            return None
        except Exception:
            return None
    
    async def _generate_element_documentation(self, element: DocumentationElement) -> Optional[Dict[str, Any]]:
        """Generate documentation for a single element using LLM"""
        try:
            # Create context for the LLM
            context = {
                "element_type": element.element_type,
                "element_name": element.element_name,
                "file_path": element.file_path,
                "line_number": element.line_number,
                "dependencies": element.dependencies,
                "related_elements": element.related_elements
            }
            
            # Create prompt for documentation generation
            prompt = self._create_documentation_prompt(element)
            
            # Call LLM to generate documentation
            messages = [HumanMessage(content=prompt)]
            result = await self._call_llm(messages, context)
            
            if result.success:
                # Process and enhance the documentation
                documentation = self._enhance_documentation(element, result.data)
                return documentation
            else:
                logger.warning(f"Failed to generate documentation for {element.element_name}: {result.errors}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating documentation for {element.element_name}: {e}")
            return None
    
    def _create_documentation_prompt(self, element: DocumentationElement) -> str:
        """Create a prompt for documentation generation"""
        
        base_prompt = f"""
You are an expert PHP developer and technical writer. Generate comprehensive documentation for the following code element:

Element Type: {element.element_type}
Element Name: {element.element_name}
File Path: {element.file_path}
Line Number: {element.line_number or 'Unknown'}

Please provide:

1. **Description**: A clear, concise description of what this element does
2. **Parameters**: If applicable, list and describe all parameters
3. **Return Value**: If applicable, describe what this element returns
4. **Examples**: Provide 2-3 practical usage examples
5. **Code Snippets**: Include relevant code snippets that demonstrate usage
6. **Dependencies**: List any dependencies or requirements
7. **Related Elements**: Mention related classes, methods, or functions

Use a {self.config.tone} tone and be specific and actionable. Focus on helping developers understand how to use this element effectively.

Format your response as JSON with the following structure:
{{
    "description": "Clear description",
    "parameters": [
        {{"name": "param_name", "type": "param_type", "description": "param_description", "required": true/false}}
    ],
    "return_value": "Description of return value",
    "examples": ["Example 1", "Example 2"],
    "code_snippets": ["Code snippet 1", "Code snippet 2"],
    "dependencies": ["dependency1", "dependency2"],
    "related_elements": ["related1", "related2"]
}}
"""
        
        # Add element-specific guidance
        if element.element_type == "class":
            base_prompt += "\n\nFor classes, focus on the class's purpose, responsibilities, and how it fits into the overall architecture."
        elif element.element_type == "method":
            base_prompt += "\n\nFor methods, focus on the method's purpose, parameters, return values, and usage patterns."
        elif element.element_type == "route":
            base_prompt += "\n\nFor routes, focus on the endpoint's purpose, HTTP method, expected input/output, and authentication requirements."
        elif element.element_type == "model":
            base_prompt += "\n\nFor models, focus on the data structure, relationships, and common operations."
        elif element.element_type == "migration":
            base_prompt += "\n\nFor migrations, focus on the database changes, purpose, and rollback considerations."
        
        return base_prompt
    
    def _enhance_documentation(self, element: DocumentationElement, llm_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance LLM-generated documentation with additional context"""
        
        enhanced_doc = {
            "element_type": element.element_type,
            "element_name": element.element_name,
            "file_path": element.file_path,
            "line_number": element.line_number,
            "description": llm_data.get("description", ""),
            "parameters": llm_data.get("parameters", []),
            "return_value": llm_data.get("return_value", ""),
            "examples": llm_data.get("examples", []),
            "code_snippets": llm_data.get("code_snippets", []),
            "dependencies": llm_data.get("dependencies", []) + (element.dependencies or []),
            "related_elements": llm_data.get("related_elements", []) + (element.related_elements or []),
            "metadata": {
                "generated_by": "documenter_agent",
                "model": self.config.model,
                "tone": self.config.tone,
                "timestamp": self.last_run.isoformat() if self.last_run else None
            }
        }
        
        # Clean up empty lists
        for key in ["parameters", "examples", "code_snippets", "dependencies", "related_elements"]:
            if not enhanced_doc[key]:
                enhanced_doc[key] = []
        
        return enhanced_doc
    
    def _generate_documentation_summary(self, documented_elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary of the documentation"""
        
        element_types = {}
        total_elements = len(documented_elements)
        
        for element in documented_elements:
            element_type = element.get("element_type", "unknown")
            if element_type not in element_types:
                element_types[element_type] = 0
            element_types[element_type] += 1
        
        return {
            "total_elements": total_elements,
            "element_type_breakdown": element_types,
            "coverage_percentage": 100 if total_elements > 0 else 0,
            "documentation_quality": "comprehensive" if total_elements > 0 else "none"
        }
    
    def get_system_prompt(self, tone: str = "professional") -> str:
        """Get the system prompt for the documenter agent"""
        
        tone_guidance = {
            "professional": "Use formal, technical language suitable for professional documentation.",
            "friendly": "Use approachable, conversational language while maintaining technical accuracy.",
            "strict": "Use precise, formal language with strict adherence to technical standards.",
            "mentor": "Use educational language that explains concepts and provides learning opportunities.",
            "casual": "Use relaxed, informal language while maintaining clarity and usefulness."
        }
        
        return f"""You are an expert PHP developer and technical writer specializing in code documentation.

Your mission is to create clear, comprehensive, and actionable documentation for PHP code elements including classes, methods, functions, routes, models, and migrations.

{tone_guidance.get(tone, tone_guidance['professional'])}

Key principles:
1. **Clarity**: Explain what the code does in simple terms
2. **Completeness**: Cover all important aspects (parameters, returns, examples)
3. **Practicality**: Provide real-world usage examples
4. **Accuracy**: Ensure all information is technically correct
5. **Consistency**: Use consistent formatting and terminology

Always structure your responses as JSON and focus on being helpful to developers who will use this code."""
    
    def process_response(self, response: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process the LLM response into structured documentation data"""
        
        try:
            # Try to parse JSON response
            if response.strip().startswith('{'):
                # Extract JSON from the response
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                json_str = response[json_start:json_end]
                
                parsed_data = json.loads(json_str)
                return parsed_data
            else:
                # Fallback: try to extract structured information
                return self._extract_structured_info(response)
                
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            # Fallback to text extraction
            return self._extract_structured_info(response)
        except Exception as e:
            logger.error(f"Error processing response: {e}")
            return {"error": f"Failed to process response: {str(e)}"}
    
    def _extract_structured_info(self, response: str) -> Dict[str, Any]:
        """Extract structured information from text response"""
        
        extracted_data = {
            "description": "",
            "parameters": [],
            "return_value": "",
            "examples": [],
            "code_snippets": [],
            "dependencies": [],
            "related_elements": []
        }
        
        # Extract description (first paragraph)
        lines = response.split('\n')
        description_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith(('**', '-', '1.', '2.')):
                description_lines.append(line)
                if len(description_lines) >= 3:  # Limit to first few lines
                    break
        
        extracted_data["description"] = ' '.join(description_lines)
        
        # Extract examples (lines starting with numbers or dashes)
        for line in lines:
            line = line.strip()
            if line.startswith(('1.', '2.', '3.', '-')) and len(line) > 3:
                example = line[3:].strip()
                if example:
                    extracted_data["examples"].append(example)
        
        return extracted_data
