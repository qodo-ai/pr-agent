"""
Tests for the Workiz custom rules engine.

Tests the rules loading, pattern matching, and finding generation
for Workiz-specific coding standards.
"""

import pytest
from pr_agent.tools.custom_rules_engine import (
    CustomRulesEngine,
    RuleFinding,
    get_rules_engine,
)


class TestCustomRulesEngine:
    """Tests for the CustomRulesEngine class."""
    
    @pytest.fixture
    def engine(self):
        return get_rules_engine()
    
    @pytest.mark.asyncio
    async def test_load_rules_from_toml(self, engine):
        await engine.load_rules()
        assert len(engine.rules) > 0
    
    @pytest.mark.asyncio
    async def test_rules_have_required_fields(self, engine):
        await engine.load_rules()
        for rule in engine.rules:
            assert rule.id is not None
            assert rule.name is not None
            assert rule.severity is not None
    
    @pytest.mark.asyncio
    async def test_apply_rules_to_typescript_code(self, engine):
        await engine.load_rules()
        
        code = '''
let mutableVar = 0;
mutableVar++;
console.log(mutableVar);
'''
        files_content = {"test.ts": code}
        findings = await engine.apply_rules(files_content)
        
        assert isinstance(findings, list)
        for finding in findings:
            assert isinstance(finding, RuleFinding)
            assert finding.file_path == "test.ts"
    
    @pytest.mark.asyncio
    async def test_detects_let_usage(self, engine):
        await engine.load_rules()
        
        code = "let counter = 0;"
        files_content = {"counter.ts": code}
        findings = await engine.apply_rules(files_content)
        
        let_findings = [f for f in findings if "let" in f.message.lower() or "const" in f.message.lower()]
        assert len(let_findings) > 0
    
    @pytest.mark.asyncio
    async def test_detects_array_mutation(self, engine):
        await engine.load_rules()
        
        code = '''
const items = [];
items.push("item");
items.splice(0, 1);
'''
        files_content = {"items.ts": code}
        findings = await engine.apply_rules(files_content)
        
        mutation_findings = [f for f in findings if "push" in f.message.lower() or "mutation" in f.message.lower() or "splice" in f.message.lower()]
        assert len(mutation_findings) > 0
    
    @pytest.mark.asyncio
    async def test_detects_for_loop(self, engine):
        await engine.load_rules()
        
        code = '''
for (let i = 0; i < 10; i++) {
    console.log(i);
}
'''
        files_content = {"loop.ts": code}
        findings = await engine.apply_rules(files_content)
        
        loop_findings = [f for f in findings if "for" in f.message.lower() or "loop" in f.message.lower() or "map" in f.message.lower()]
        assert len(loop_findings) > 0
    
    @pytest.mark.asyncio
    async def test_detects_console_log(self, engine):
        await engine.load_rules()
        
        code = 'console.log("debug");'
        files_content = {"debug.ts": code}
        findings = await engine.apply_rules(files_content)
        
        console_findings = [f for f in findings if "console" in f.message.lower() or "logger" in f.message.lower()]
        assert len(console_findings) > 0
    
    @pytest.mark.asyncio
    async def test_language_filtering(self, engine):
        await engine.load_rules()
        
        python_code = "print('hello')"
        files_content = {"script.py": python_code}
        findings = await engine.apply_rules(files_content)
        
        ts_only_findings = [f for f in findings if f.rule_id.startswith("fp-") or f.rule_id.startswith("nest-")]
        assert len(ts_only_findings) == 0


class TestRuleFinding:
    """Tests for RuleFinding dataclass."""
    
    def test_finding_creation(self):
        finding = RuleFinding(
            rule_id="test-001",
            rule_name="Test Rule",
            message="This is a test finding",
            severity="medium",
            file_path="test.ts",
            line_start=10,
            line_end=10,
            suggestion="Fix this issue",
        )
        
        assert finding.rule_id == "test-001"
        assert finding.severity == "medium"
        assert finding.line_start == 10


class TestRuleSeverities:
    """Tests for rule severity assignments."""
    
    @pytest.fixture
    def engine(self):
        return get_rules_engine()
    
    @pytest.mark.asyncio
    async def test_security_rules_are_critical(self, engine):
        await engine.load_rules()
        
        code = '''
const apiKey = "sk-1234567890abcdef";
const password = "mysecretpassword";
'''
        files_content = {"config.ts": code}
        findings = await engine.apply_rules(files_content)
        
        security_findings = [f for f in findings if "secret" in f.message.lower() or "password" in f.message.lower() or "key" in f.message.lower()]
        if security_findings:
            assert any(f.severity == "critical" for f in security_findings)
    
    @pytest.mark.asyncio
    async def test_sql_injection_rules_are_critical(self, engine):
        await engine.load_rules()
        
        code = '''
const query = `SELECT * FROM users WHERE id = ${userId}`;
'''
        files_content = {"query.ts": code}
        findings = await engine.apply_rules(files_content)
        
        sql_findings = [f for f in findings if "sql" in f.message.lower() or "injection" in f.message.lower()]
        if sql_findings:
            assert any(f.severity == "critical" for f in sql_findings)


class TestRuleFiltering:
    """Tests for rule filtering by language and file type."""
    
    @pytest.fixture
    def engine(self):
        return get_rules_engine()
    
    @pytest.mark.asyncio
    async def test_migration_rules_apply_to_migration_files(self, engine):
        await engine.load_rules()
        
        code = '''
import { MigrationInterface, QueryRunner, Table } from 'typeorm';

export class CreateUsers implements MigrationInterface {
    async up(queryRunner: QueryRunner) {
        await queryRunner.createTable(new Table({
            name: 'users',
            columns: [{ name: 'id', type: 'int' }]
        }));
    }
}
'''
        files_content = {"migrations/1234-create-users.ts": code}
        findings = await engine.apply_rules(files_content)
        
        migration_findings = [f for f in findings if "migration" in f.message.lower() or "raw sql" in f.message.lower() or "createTable" in f.message.lower()]
        assert len(migration_findings) > 0
    
    @pytest.mark.asyncio
    async def test_react_rules_apply_to_tsx_files(self, engine):
        await engine.load_rules()
        
        code = '''
class OldComponent extends React.Component {
    render() {
        return <div>Old style</div>;
    }
}
'''
        files_content = {"Component.tsx": code}
        findings = await engine.apply_rules(files_content)
        
        react_findings = [f for f in findings if "class component" in f.message.lower() or "functional" in f.message.lower()]
        assert len(react_findings) > 0
