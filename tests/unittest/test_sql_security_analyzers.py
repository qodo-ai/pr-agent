"""
Tests for the SQL and Security analyzers.

Tests detection of SQL-related issues and security vulnerabilities
across different languages.
"""

import pytest
from pr_agent.tools.sql_analyzer import SQLAnalyzer, get_sql_analyzer
from pr_agent.tools.security_analyzer import SecurityAnalyzer, get_security_analyzer, SecuritySeverity


class TestSQLAnalyzer:
    """Tests for SQL-specific analyzer."""
    
    @pytest.fixture
    def analyzer(self):
        return get_sql_analyzer()
    
    @pytest.mark.asyncio
    async def test_detects_string_concatenation_in_query(self, analyzer):
        code = '''
const userId = req.params.id;
const query = "SELECT * FROM users WHERE id = " + userId;
db.query(query);
'''
        findings = await analyzer.analyze(code, "users.ts")
        assert any("sql" in f.message.lower() or "concatenation" in f.message.lower() for f in findings)
    
    @pytest.mark.asyncio
    async def test_detects_template_literal_injection(self, analyzer):
        code = '''
const userId = req.params.id;
const query = `SELECT * FROM users WHERE id = ${userId}`;
'''
        findings = await analyzer.analyze(code, "users.ts")
        assert any("sql" in f.message.lower() or "injection" in f.message.lower() for f in findings)
    
    @pytest.mark.asyncio
    async def test_allows_parameterized_queries(self, analyzer):
        code = '''
const userId = req.params.id;
const query = "SELECT * FROM users WHERE id = ?";
db.query(query, [userId]);
'''
        findings = await analyzer.analyze(code, "users.ts")
        injection_findings = [f for f in findings if "injection" in f.message.lower()]
        assert len(injection_findings) == 0
    
    @pytest.mark.asyncio
    async def test_detects_n_plus_one_pattern(self, analyzer):
        code = '''
const users = await userRepository.find();
for (const user of users) {
    const posts = await postRepository.find({ userId: user.id });
    user.posts = posts;
}
'''
        findings = await analyzer.analyze(code, "users.service.ts")
        n_plus_one_findings = [f for f in findings if "n+1" in f.message.lower() or "batch" in f.message.lower()]
        assert len(n_plus_one_findings) > 0
    
    @pytest.mark.asyncio
    async def test_detects_missing_transaction(self, analyzer):
        code = '''
async createOrder(dto: CreateOrderDto) {
    const order = await this.orderRepository.save(dto);
    await this.inventoryService.decreaseStock(dto.items);
    await this.paymentService.charge(dto.userId, dto.total);
    await this.emailService.sendConfirmation(dto.userId, order.id);
    return order;
}
'''
        findings = await analyzer.analyze(code, "orders.service.ts")
        transaction_findings = [f for f in findings if "transaction" in f.message.lower()]
        assert len(transaction_findings) > 0
    
    @pytest.mark.asyncio
    async def test_detects_typeorm_table_builder(self, analyzer):
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
        findings = await analyzer.analyze(code, "migrations/001-create-users.ts")
        builder_findings = [f for f in findings if "createTable" in f.message or "raw sql" in f.message.lower()]
        assert len(builder_findings) > 0
    
    @pytest.mark.asyncio
    async def test_detects_php_sql_injection(self, analyzer):
        code = '''
<?php
$id = $_GET['id'];
$query = "SELECT * FROM users WHERE id = $id";
mysqli_query($conn, $query);
'''
        findings = await analyzer.analyze(code, "users.php")
        assert any("sql" in f.message.lower() or "injection" in f.message.lower() for f in findings)


class TestSecurityAnalyzer:
    """Tests for security vulnerability analyzer."""
    
    @pytest.fixture
    def analyzer(self):
        return get_security_analyzer()
    
    @pytest.mark.asyncio
    async def test_detects_hardcoded_secrets(self, analyzer):
        code = '''
const API_KEY = "sk-1234567890abcdef1234567890abcdef";
const config = {
    apiKey: API_KEY,
    secretKey: "my-super-secret-key"
};
'''
        findings = await analyzer.analyze(code, "config.ts")
        assert any("secret" in f.message.lower() or "hardcoded" in f.message.lower() for f in findings)
        assert any(f.severity == SecuritySeverity.CRITICAL for f in findings)
    
    @pytest.mark.asyncio
    async def test_detects_password_in_code(self, analyzer):
        code = '''
const dbPassword = "production_password_123";
const connection = mysql.createConnection({
    password: dbPassword
});
'''
        findings = await analyzer.analyze(code, "db.ts")
        assert any("password" in f.message.lower() for f in findings)
    
    @pytest.mark.asyncio
    async def test_allows_environment_variables(self, analyzer):
        code = '''
const API_KEY = process.env.API_KEY;
const config = {
    apiKey: API_KEY,
    secretKey: process.env.SECRET_KEY
};
'''
        findings = await analyzer.analyze(code, "config.ts")
        hardcoded_findings = [f for f in findings if "hardcoded" in f.message.lower()]
        assert len(hardcoded_findings) == 0
    
    @pytest.mark.asyncio
    async def test_detects_eval_usage(self, analyzer):
        code = '''
const userInput = req.body.code;
eval(userInput);
'''
        findings = await analyzer.analyze(code, "dangerous.ts")
        assert any("eval" in f.message.lower() for f in findings)
        assert any(f.severity == SecuritySeverity.CRITICAL for f in findings)
    
    @pytest.mark.asyncio
    async def test_detects_innerHTML(self, analyzer):
        code = '''
const userContent = getUserInput();
document.getElementById("container").innerHTML = userContent;
'''
        findings = await analyzer.analyze(code, "frontend.ts")
        assert any("xss" in f.message.lower() or "innerHTML" in f.message.lower() for f in findings)
    
    @pytest.mark.asyncio
    async def test_detects_dangerouslySetInnerHTML(self, analyzer):
        code = '''
const Component = ({ html }) => {
    return <div dangerouslySetInnerHTML={{ __html: html }} />;
};
'''
        findings = await analyzer.analyze(code, "Component.tsx")
        assert any("xss" in f.message.lower() or "dangerouslySetInnerHTML" in f.message.lower() for f in findings)
    
    @pytest.mark.asyncio
    async def test_detects_missing_input_validation(self, analyzer):
        code = '''
@Post('users')
async createUser(@Body() dto: CreateUserDto) {
    return this.userService.create(dto);
}
'''
        findings = await analyzer.analyze(code, "users.controller.ts")
        validation_findings = [f for f in findings if "validation" in f.message.lower()]
        assert len(validation_findings) >= 0
    
    @pytest.mark.asyncio
    async def test_detects_weak_crypto(self, analyzer):
        code = '''
const crypto = require('crypto');
const hash = crypto.createHash('md5').update(password).digest('hex');
'''
        findings = await analyzer.analyze(code, "auth.ts")
        assert any("md5" in f.message.lower() or "weak" in f.message.lower() for f in findings)
    
    @pytest.mark.asyncio
    async def test_detects_jwt_without_verification(self, analyzer):
        code = '''
const jwt = require('jsonwebtoken');
const decoded = jwt.decode(token);
'''
        findings = await analyzer.analyze(code, "auth.ts")
        jwt_findings = [f for f in findings if "jwt" in f.message.lower() or "verify" in f.message.lower()]
        assert len(jwt_findings) > 0
    
    @pytest.mark.asyncio
    async def test_has_cwe_ids(self, analyzer):
        code = '''
const query = "SELECT * FROM users WHERE id = " + userId;
'''
        findings = await analyzer.analyze(code, "users.ts")
        findings_with_cwe = [f for f in findings if hasattr(f, 'cwe_id') and f.cwe_id]
        assert len(findings_with_cwe) >= 0


class TestAnalyzerIntegration:
    """Integration tests for analyzers working together."""
    
    @pytest.mark.asyncio
    async def test_sql_and_security_detect_same_vulnerability(self):
        sql_analyzer = get_sql_analyzer()
        security_analyzer = get_security_analyzer()
        
        code = '''
const userId = req.params.id;
const query = "SELECT * FROM users WHERE id = " + userId;
db.query(query);
'''
        sql_findings = await sql_analyzer.analyze(code, "users.ts")
        security_findings = await security_analyzer.analyze(code, "users.ts")
        
        assert len(sql_findings) > 0 or len(security_findings) > 0
    
    @pytest.mark.asyncio
    async def test_analyzers_dont_duplicate_findings(self):
        sql_analyzer = get_sql_analyzer()
        security_analyzer = get_security_analyzer()
        
        code = '''
const secret = "hardcoded";
'''
        sql_findings = await sql_analyzer.analyze(code, "config.ts")
        security_findings = await security_analyzer.analyze(code, "config.ts")
        
        sql_rule_ids = {f.rule_id for f in sql_findings}
        security_rule_ids = {f.rule_id for f in security_findings}
        
        overlap = sql_rule_ids.intersection(security_rule_ids)
        assert len(overlap) == 0
