"""
NestJS Framework Analyzer

Analyzes NestJS-specific patterns and best practices:
- Dependency injection patterns
- Module structure
- Controller/Service patterns
- DTO validation
- Decorator usage
- Structured logging
"""

import re
import logging
from .base_analyzer import BaseAnalyzer, AnalyzerFinding, FindingSeverity

logger = logging.getLogger(__name__)


class NestJSAnalyzer(BaseAnalyzer):
    """
    Analyzer for NestJS framework patterns.
    
    Checks for Workiz NestJS standards:
    - Proper dependency injection
    - Module organization
    - DTO validation with class-validator
    - Structured logging with context
    - Controller/Service separation
    """
    
    name = "NestJSAnalyzer"
    language = "nestjs"
    
    # NestJS decorators that indicate file types
    CONTROLLER_DECORATORS = ['@Controller', '@Get', '@Post', '@Put', '@Delete', '@Patch']
    SERVICE_DECORATORS = ['@Injectable']
    MODULE_DECORATORS = ['@Module']
    DTO_DECORATORS = ['@IsString', '@IsNumber', '@IsBoolean', '@IsOptional', '@IsNotEmpty', '@ValidateNested']
    
    async def analyze(self, content: str, file_path: str) -> list[AnalyzerFinding]:
        """Analyze NestJS file content."""
        self.clear_findings()
        
        if not self._is_nestjs_file(content):
            return []
        
        lines = content.split('\n')
        
        self._check_dependency_injection(content, file_path, lines)
        self._check_dto_validation(content, file_path, lines)
        self._check_structured_logging(content, file_path, lines)
        self._check_controller_patterns(content, file_path, lines)
        self._check_service_patterns(content, file_path, lines)
        self._check_module_structure(content, file_path, lines)
        self._check_exception_handling(content, file_path, lines)
        
        return self.get_findings()
    
    def _is_nestjs_file(self, content: str) -> bool:
        """Check if file appears to be a NestJS file."""
        nestjs_imports = ['@nestjs/common', '@nestjs/core', '@nestjs/testing']
        return any(imp in content for imp in nestjs_imports)
    
    def _check_dependency_injection(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for proper dependency injection patterns."""
        new_pattern = re.compile(r'new\s+(\w+Service|\w+Repository|\w+Provider)\s*\(')
        
        for i, line in enumerate(lines, start=1):
            match = new_pattern.search(line)
            if match:
                class_name = match.group(1)
                self.add_finding(
                    rule_id="NEST001",
                    message=f"Direct instantiation of '{class_name}' detected. Use NestJS dependency injection instead.",
                    severity=FindingSeverity.ERROR,
                    file_path=file_path,
                    line_start=i,
                    code_snippet=line.strip(),
                    suggestion=f"Inject {class_name} via constructor: constructor(private readonly {class_name[0].lower() + class_name[1:]}: {class_name})",
                )
        
        if '@Injectable' in content:
            if 'constructor' not in content:
                injectable_line = self.find_line_number(content, '@Injectable')
                if injectable_line:
                    self.add_finding(
                        rule_id="NEST002",
                        message="Injectable class without constructor. Consider if dependencies are needed.",
                        severity=FindingSeverity.INFO,
                        file_path=file_path,
                        line_start=injectable_line,
                    )
    
    def _check_dto_validation(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for DTO validation patterns."""
        if '.dto.ts' not in file_path.lower():
            return
        
        has_class_validator = 'class-validator' in content
        has_decorators = any(dec in content for dec in self.DTO_DECORATORS)
        
        if not has_class_validator and not has_decorators:
            self.add_finding(
                rule_id="NEST003",
                message="DTO file without class-validator decorators. Add validation decorators to ensure input validation.",
                severity=FindingSeverity.WARNING,
                file_path=file_path,
                line_start=1,
                suggestion="Add class-validator decorators like @IsString(), @IsNotEmpty(), etc.",
            )
        
        property_pattern = re.compile(r'^\s*(\w+)\s*[?:]')
        for i, line in enumerate(lines, start=1):
            if property_pattern.match(line):
                prev_lines = '\n'.join(lines[max(0, i-3):i-1])
                if not any(dec in prev_lines for dec in self.DTO_DECORATORS):
                    prop_match = property_pattern.match(line)
                    if prop_match:
                        prop_name = prop_match.group(1)
                        if prop_name not in ('constructor', 'class', 'export', 'import', 'const', 'let', 'var'):
                            self.add_finding(
                                rule_id="NEST004",
                                message=f"Property '{prop_name}' lacks validation decorators.",
                                severity=FindingSeverity.INFO,
                                file_path=file_path,
                                line_start=i,
                                code_snippet=line.strip(),
                                suggestion=f"Add validation decorator above property, e.g., @IsString() or @IsOptional()",
                            )
    
    def _check_structured_logging(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for structured logging with context."""
        logger_patterns = [
            re.compile(r'this\.logger\.(log|warn|error|debug|verbose)\s*\(\s*[\'"`][^\'"`]+[\'"`]\s*\)'),
            re.compile(r'logger\.(log|warn|error|debug|verbose)\s*\(\s*[\'"`][^\'"`]+[\'"`]\s*\)'),
        ]
        
        for i, line in enumerate(lines, start=1):
            for pattern in logger_patterns:
                if pattern.search(line):
                    if '{' not in line or 'context' not in line.lower():
                        self.add_finding(
                            rule_id="NEST005",
                            message="Logger call without context object. Add structured context for better debugging.",
                            severity=FindingSeverity.WARNING,
                            file_path=file_path,
                            line_start=i,
                            code_snippet=line.strip(),
                            suggestion="Add context object: this.logger.log('message', { accountId, userId, ... })",
                        )
                    break
    
    def _check_controller_patterns(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check controller-specific patterns."""
        if '@Controller' not in content:
            return
        
        if 'async' not in content:
            controller_line = self.find_line_number(content, '@Controller')
            if controller_line:
                self.add_finding(
                    rule_id="NEST006",
                    message="Controller without async methods. Consider using async/await for database operations.",
                    severity=FindingSeverity.INFO,
                    file_path=file_path,
                    line_start=controller_line,
                )
        
        business_logic_patterns = [
            re.compile(r'\.find\s*\('),
            re.compile(r'\.save\s*\('),
            re.compile(r'\.update\s*\('),
            re.compile(r'\.delete\s*\('),
            re.compile(r'\.create\s*\('),
        ]
        
        for i, line in enumerate(lines, start=1):
            if any(pattern.search(line) for pattern in business_logic_patterns):
                if 'this.' in line and 'Service' not in line:
                    self.add_finding(
                        rule_id="NEST007",
                        message="Possible business logic in controller. Controllers should be thin; delegate to services.",
                        severity=FindingSeverity.WARNING,
                        file_path=file_path,
                        line_start=i,
                        code_snippet=line.strip(),
                        suggestion="Move business logic to a service class",
                    )
    
    def _check_service_patterns(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check service-specific patterns."""
        if '@Injectable' not in content or '.service.ts' not in file_path.lower():
            return
        
        if 'try' in content and 'catch' in content:
            try_line = self.find_line_number(content, 'try')
            if try_line:
                self.add_finding(
                    rule_id="NEST008",
                    message="Try-catch in service. Consider letting NestJS exception filters handle errors instead.",
                    severity=FindingSeverity.INFO,
                    file_path=file_path,
                    line_start=try_line,
                    suggestion="Use @workiz/all-exceptions-filter and let exceptions bubble up",
                )
    
    def _check_module_structure(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check module structure patterns."""
        if '@Module' not in content:
            return
        
        module_pattern = re.compile(r'@Module\s*\(\s*\{([^}]+)\}', re.DOTALL)
        match = module_pattern.search(content)
        
        if match:
            module_content = match.group(1)
            
            if 'providers' not in module_content and 'imports' not in module_content:
                module_line = self.find_line_number(content, '@Module')
                if module_line:
                    self.add_finding(
                        rule_id="NEST009",
                        message="Module without providers or imports. Consider if this module is necessary.",
                        severity=FindingSeverity.INFO,
                        file_path=file_path,
                        line_start=module_line,
                    )
    
    def _check_exception_handling(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check exception handling patterns."""
        throw_pattern = re.compile(r'throw\s+new\s+Error\s*\(')
        
        for i, line in enumerate(lines, start=1):
            if throw_pattern.search(line):
                self.add_finding(
                    rule_id="NEST010",
                    message="Throwing generic Error. Use NestJS HttpException or custom exceptions instead.",
                    severity=FindingSeverity.WARNING,
                    file_path=file_path,
                    line_start=i,
                    code_snippet=line.strip(),
                    suggestion="Use HttpException, BadRequestException, NotFoundException, etc.",
                )
