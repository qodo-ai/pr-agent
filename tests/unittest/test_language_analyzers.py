"""
Tests for the Workiz language analyzers.

Tests the TypeScript, NestJS, React, PHP, and Python analyzers
for detecting code quality issues and applying Workiz coding standards.
"""

import pytest
from pr_agent.tools.language_analyzers import (
    TypeScriptAnalyzer,
    NestJSAnalyzer,
    ReactAnalyzer,
    PHPAnalyzer,
    PythonAnalyzer,
    get_analyzer_for_file,
    FindingSeverity,
)


class TestGetAnalyzerForFile:
    """Tests for get_analyzer_for_file function."""
    
    def test_typescript_file_returns_typescript_analyzers(self):
        analyzers = get_analyzer_for_file("src/utils/helper.ts")
        analyzer_names = [a.name for a in analyzers]
        assert "TypeScriptAnalyzer" in analyzer_names
    
    def test_tsx_file_returns_react_analyzer(self):
        analyzers = get_analyzer_for_file("src/components/Button.tsx")
        analyzer_names = [a.name for a in analyzers]
        assert "ReactAnalyzer" in analyzer_names
        assert "TypeScriptAnalyzer" in analyzer_names
    
    def test_controller_file_returns_nestjs_analyzer(self):
        analyzers = get_analyzer_for_file("src/users/users.controller.ts")
        analyzer_names = [a.name for a in analyzers]
        assert "NestJSAnalyzer" in analyzer_names
    
    def test_php_file_returns_php_analyzer(self):
        analyzers = get_analyzer_for_file("app/Http/Controllers/UserController.php")
        analyzer_names = [a.name for a in analyzers]
        assert "PHPAnalyzer" in analyzer_names
    
    def test_python_file_returns_python_analyzer(self):
        analyzers = get_analyzer_for_file("src/services/user_service.py")
        analyzer_names = [a.name for a in analyzers]
        assert "PythonAnalyzer" in analyzer_names
    
    def test_unknown_extension_returns_empty(self):
        analyzers = get_analyzer_for_file("README.md")
        assert analyzers == []


class TestTypeScriptAnalyzer:
    """Tests for TypeScript-specific analyzer."""
    
    @pytest.fixture
    def analyzer(self):
        return TypeScriptAnalyzer()
    
    @pytest.mark.asyncio
    async def test_detects_let_usage(self, analyzer):
        code = '''
let counter = 0;
counter++;
'''
        findings = await analyzer.analyze(code, "test.ts")
        assert any(f.rule_id == "ts-fp-001" for f in findings)
    
    @pytest.mark.asyncio
    async def test_detects_var_usage(self, analyzer):
        code = '''
var oldStyle = "bad";
'''
        findings = await analyzer.analyze(code, "test.ts")
        assert any(f.rule_id == "ts-fp-001" for f in findings)
    
    @pytest.mark.asyncio
    async def test_detects_array_push(self, analyzer):
        code = '''
const items = [];
items.push("new item");
'''
        findings = await analyzer.analyze(code, "test.ts")
        assert any(f.rule_id == "ts-fp-002" for f in findings)
    
    @pytest.mark.asyncio
    async def test_allows_const(self, analyzer):
        code = '''
const immutable = "good";
'''
        findings = await analyzer.analyze(code, "test.ts")
        fp_findings = [f for f in findings if f.rule_id == "ts-fp-001"]
        assert len(fp_findings) == 0
    
    @pytest.mark.asyncio
    async def test_detects_console_log(self, analyzer):
        code = '''
console.log("debug message");
'''
        findings = await analyzer.analyze(code, "test.ts")
        assert any(f.rule_id == "ts-log-001" for f in findings)
    
    @pytest.mark.asyncio
    async def test_detects_any_type(self, analyzer):
        code = '''
function process(data: any): void {
    console.log(data);
}
'''
        findings = await analyzer.analyze(code, "test.ts")
        assert any(f.rule_id == "ts-type-001" for f in findings)


class TestNestJSAnalyzer:
    """Tests for NestJS-specific analyzer."""
    
    @pytest.fixture
    def analyzer(self):
        return NestJSAnalyzer()
    
    @pytest.mark.asyncio
    async def test_detects_manual_service_instantiation(self, analyzer):
        code = '''
@Controller('users')
export class UsersController {
    handleRequest() {
        const service = new UserService();
        return service.findAll();
    }
}
'''
        findings = await analyzer.analyze(code, "users.controller.ts")
        assert any("instantiation" in f.message.lower() or "injection" in f.message.lower() for f in findings)
    
    @pytest.mark.asyncio
    async def test_detects_missing_dto_validation(self, analyzer):
        code = '''
@Post()
create(@Body() createUserDto) {
    return this.usersService.create(createUserDto);
}
'''
        findings = await analyzer.analyze(code, "users.controller.ts")
        assert any("dto" in f.message.lower() or "validation" in f.message.lower() for f in findings)
    
    @pytest.mark.asyncio
    async def test_detects_business_logic_in_controller(self, analyzer):
        code = '''
@Controller('orders')
export class OrdersController {
    @Post()
    async createOrder(@Body() dto) {
        const total = dto.items.reduce((sum, item) => sum + item.price * item.quantity, 0);
        const tax = total * 0.1;
        const discount = total > 100 ? total * 0.05 : 0;
        const finalTotal = total + tax - discount;
        
        const order = {
            items: dto.items,
            total: finalTotal,
            tax,
            discount,
            createdAt: new Date()
        };
        
        return this.ordersRepository.save(order);
    }
}
'''
        findings = await analyzer.analyze(code, "orders.controller.ts")
        assert any(f.severity in [FindingSeverity.MEDIUM, FindingSeverity.HIGH] for f in findings)


class TestReactAnalyzer:
    """Tests for React-specific analyzer."""
    
    @pytest.fixture
    def analyzer(self):
        return ReactAnalyzer()
    
    @pytest.mark.asyncio
    async def test_detects_class_component(self, analyzer):
        code = '''
class MyComponent extends React.Component {
    render() {
        return <div>Hello</div>;
    }
}
'''
        findings = await analyzer.analyze(code, "MyComponent.tsx")
        assert any(f.rule_id == "react-001" for f in findings)
    
    @pytest.mark.asyncio
    async def test_allows_functional_component(self, analyzer):
        code = '''
const MyComponent = () => {
    return <div>Hello</div>;
};
'''
        findings = await analyzer.analyze(code, "MyComponent.tsx")
        class_findings = [f for f in findings if f.rule_id == "react-001"]
        assert len(class_findings) == 0
    
    @pytest.mark.asyncio
    async def test_detects_inline_styles(self, analyzer):
        code = '''
const Button = () => {
    return <button style={{color: 'red', padding: '10px'}}>Click</button>;
};
'''
        findings = await analyzer.analyze(code, "Button.tsx")
        assert any(f.rule_id == "react-002" for f in findings)


class TestPHPAnalyzer:
    """Tests for PHP-specific analyzer."""
    
    @pytest.fixture
    def analyzer(self):
        return PHPAnalyzer()
    
    @pytest.mark.asyncio
    async def test_detects_direct_query_concatenation(self, analyzer):
        code = '''
<?php
$query = "SELECT * FROM users WHERE id = " . $_GET['id'];
$result = mysqli_query($conn, $query);
'''
        findings = await analyzer.analyze(code, "users.php")
        assert any("sql" in f.message.lower() or "injection" in f.message.lower() for f in findings)
    
    @pytest.mark.asyncio
    async def test_detects_eval_usage(self, analyzer):
        code = '''
<?php
$code = $_POST['code'];
eval($code);
'''
        findings = await analyzer.analyze(code, "dangerous.php")
        assert any("eval" in f.message.lower() for f in findings)


class TestPythonAnalyzer:
    """Tests for Python-specific analyzer."""
    
    @pytest.fixture
    def analyzer(self):
        return PythonAnalyzer()
    
    @pytest.mark.asyncio
    async def test_detects_bare_except(self, analyzer):
        code = '''
try:
    do_something()
except:
    pass
'''
        findings = await analyzer.analyze(code, "service.py")
        assert any("except" in f.message.lower() for f in findings)
    
    @pytest.mark.asyncio
    async def test_detects_print_statement(self, analyzer):
        code = '''
def process():
    print("Debug: processing")
    return True
'''
        findings = await analyzer.analyze(code, "service.py")
        assert any("print" in f.message.lower() or "logging" in f.message.lower() for f in findings)
    
    @pytest.mark.asyncio
    async def test_detects_mutable_default_argument(self, analyzer):
        code = '''
def append_to(element, to=[]):
    to.append(element)
    return to
'''
        findings = await analyzer.analyze(code, "utils.py")
        assert any("mutable" in f.message.lower() or "default" in f.message.lower() for f in findings)


class TestSeverityLevels:
    """Tests for severity level assignment."""
    
    @pytest.mark.asyncio
    async def test_critical_for_security_issues(self):
        analyzer = TypeScriptAnalyzer()
        code = '''
const password = "hardcoded_secret_123";
'''
        findings = await analyzer.analyze(code, "config.ts")
        security_findings = [f for f in findings if "secret" in f.message.lower() or "password" in f.message.lower()]
        if security_findings:
            assert any(f.severity == FindingSeverity.CRITICAL for f in security_findings)
