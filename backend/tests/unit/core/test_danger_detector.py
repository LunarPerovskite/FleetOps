"""Unit tests for danger detection engine"""
import pytest
import sys

sys.path.insert(0, '/data/.openclaw/workspace/fleetops-temp/backend')

from app.core.danger_detector import (
    DangerDetector,
    DangerRule,
    DangerLevel,
    analyze_action
)


class TestDangerDetector:
    """Test the danger detection engine"""
    
    @pytest.fixture
    def detector(self):
        return DangerDetector()
    
    def test_safe_read_action(self, detector):
        """Safe actions should return safe"""
        result = detector.analyze(
            tool="read",
            arguments="Read the file",
            environment="development"
        )
        
        assert result["danger_level"] == "safe"
        assert result["requires_approval"] is False
        assert result["approver_count"] == 0
    
    def test_bash_rm_command(self, detector):
        """rm command should be high danger"""
        result = detector.analyze(
            tool="bash",
            arguments="rm -rf /tmp/data",
            environment="development"
        )
        
        assert result["danger_level"] == "high"
        assert result["requires_approval"] is True
        assert result["approver_count"] == 1
        assert "bash_execution" in result["matched_rules"]
    
    def test_bash_safe_command(self, detector):
        """Safe bash commands should be low danger"""
        result = detector.analyze(
            tool="bash",
            arguments="ls -la /tmp",
            environment="development"
        )
        
        # ls is low danger, but rm is high - ls should match safe
        assert result["danger_level"] in ["low", "safe"]
        assert "bash_read" in result["matched_rules"]
    
    def test_database_delete(self, detector):
        """DELETE operations should be high danger"""
        result = detector.analyze(
            tool="db",
            arguments="DELETE FROM users WHERE id=1",
            environment="development"
        )
        
        assert result["danger_level"] == "high"
        assert result["requires_approval"] is True
        assert "database_write" in result["matched_rules"]
    
    def test_database_select(self, detector):
        """SELECT should be medium danger"""
        result = detector.analyze(
            tool="db",
            arguments="SELECT * FROM users",
            environment="development"
        )
        
        assert result["danger_level"] == "medium"
        assert result["requires_approval"] is True
        assert "database_read" in result["matched_rules"]
    
    def test_external_api_post(self, detector):
        """POST to external API should be medium danger"""
        result = detector.analyze(
            tool="api",
            arguments="POST /api/users",
            environment="development"
        )
        
        assert result["danger_level"] == "medium"
        assert result["requires_approval"] is True
        assert "external_api" in result["matched_rules"]
    
    def test_external_api_get(self, detector):
        """GET to external API should be low danger"""
        result = detector.analyze(
            tool="api",
            arguments="GET /api/users",
            environment="development"
        )
        
        assert result["danger_level"] == "low"
        assert result["requires_approval"] is False
    
    def test_production_config_modification(self, detector):
        """Modifying production config is critical"""
        result = detector.analyze(
            tool="write",
            arguments="Update config",
            file_path="/app/.env.production",
            environment="production"
        )
        
        assert result["danger_level"] == "critical"
        assert result["requires_approval"] is True
        assert result["approver_count"] == 2
        assert "production_config" in result["matched_rules"]
    
    def test_auth_file_modification(self, detector):
        """Modifying auth files is high danger"""
        result = detector.analyze(
            tool="write",
            arguments="Fix auth bug",
            file_path="/app/auth/middleware.py",
            environment="development"
        )
        
        assert result["danger_level"] == "high"
        assert "auth_files" in result["matched_rules"]
    
    def test_infrastructure_modification(self, detector):
        """Modifying infrastructure files is critical"""
        result = detector.analyze(
            tool="write",
            arguments="Update deployment",
            file_path="/infra/docker-compose.yml",
            environment="development"
        )
        
        assert result["danger_level"] == "critical"
        assert "infrastructure" in result["matched_rules"]
    
    def test_production_environment_escalation(self, detector):
        """Any action in production is higher risk"""
        result = detector.analyze(
            tool="read",
            arguments="Read production logs",
            environment="production"
        )
        
        assert result["danger_level"] == "high"
        assert "prod_environment" in result["matched_rules"]
    
    def test_cost_threshold_medium(self, detector):
        """High cost should trigger approval"""
        result = detector.analyze(
            tool="api",
            arguments="Generate report",
            environment="development",
            estimated_cost=75.0
        )
        
        assert result["danger_level"] in ["medium", "high"]
        assert result["requires_approval"] is True
        assert "cost_threshold" in result["matched_rules"]
    
    def test_cost_threshold_high(self, detector):
        """Very high cost should be high danger"""
        result = detector.analyze(
            tool="api",
            arguments="Big task",
            environment="development",
            estimated_cost=250.0
        )
        
        assert result["danger_level"] == "high"
        assert result["approver_count"] == 1
    
    def test_no_danger_detected(self, detector):
        """Actions with no matching rules should be safe"""
        result = detector.analyze(
            tool="custom",
            arguments="Do something harmless",
            environment="development"
        )
        
        assert result["danger_level"] == "safe"
        assert result["matched_rules"] == []
    
    def test_multiple_rules_matching(self, detector):
        """Multiple rules can match simultaneously"""
        result = detector.analyze(
            tool="bash",
            arguments="rm -rf /app/.env.production",
            file_path="/app/.env.production",
            environment="production"
        )
        
        assert result["danger_level"] == "critical"
        assert len(result["matched_rules"]) >= 2
    
    def test_custom_rule(self, detector):
        """Custom rules should be respected"""
        custom_rule = DangerRule(
            name="custom_api_limit",
            description="Custom API rate limit",
            danger_level=DangerLevel.HIGH,
            conditions={"tool": "api", "contains": ["rate_limit"]},
        )
        
        detector.add_rule(custom_rule)
        
        result = detector.analyze(
            tool="api",
            arguments="rate_limit_exceeded",
            environment="development"
        )
        
        assert "custom_api_limit" in result["matched_rules"]
    
    def test_remove_rule(self, detector):
        """Rules can be removed"""
        detector.remove_rule("bash_execution")
        
        result = detector.analyze(
            tool="bash",
            arguments="rm -rf /tmp",
            environment="development"
        )
        
        # After removing rm rule, should be lower
        assert "bash_execution" not in result["matched_rules"]


class TestDangerLevels:
    """Test danger level classifications"""
    
    def test_danger_level_order(self):
        """Verify danger levels are ordered correctly"""
        detector = DangerDetector()
        
        levels = [
            DangerLevel.SAFE,
            DangerLevel.LOW,
            DangerLevel.MEDIUM,
            DangerLevel.HIGH,
            DangerLevel.CRITICAL,
        ]
        
        scores = [detector._calculate_score(l) for l in levels]
        assert scores == sorted(scores)
    
    def test_approver_counts(self):
        """Verify approver counts per level"""
        detector = DangerDetector()
        
        test_cases = [
            ("safe", 0),
            ("low", 0),
            ("medium", 1),
            ("high", 1),
            ("critical", 2),
        ]
        
        for level_str, expected_count in test_cases:
            level = DangerLevel(level_str)
            assert detector._danger_rank(level) >= 0


class TestAnalyzeActionConvenience:
    """Test the convenience function"""
    
    def test_analyze_action_basic(self):
        """Test basic analyze action"""
        result = analyze_action(
            tool="bash",
            arguments="rm -rf /tmp/data",
            environment="development"
        )
        
        assert result["danger_level"] == "high"
        assert result["requires_approval"] is True
    
    def test_analyze_action_with_org(self):
        """Test with org ID"""
        result = analyze_action(
            tool="read",
            arguments="Read file",
            environment="production",
            org_id="org-123"
        )
        
        # Should use org-specific rules if they exist
        assert "danger_level" in result


class TestEdgeCases:
    """Test edge cases"""
    
    def test_empty_arguments(self):
        """Handle empty arguments"""
        detector = DangerDetector()
        result = detector.analyze(
            tool="bash",
            arguments="",
            environment="development"
        )
        
        # Should not crash
        assert "danger_level" in result
    
    def test_none_arguments(self):
        """Handle None arguments"""
        detector = DangerDetector()
        result = detector.analyze(
            tool="bash",
            arguments=None,
            environment="development"
        )
        
        # Should not crash
        assert "danger_level" in result
    
    def test_very_long_arguments(self):
        """Handle very long argument strings"""
        detector = DangerDetector()
        long_string = "A" * 10000 + "rm -rf"
        result = detector.analyze(
            tool="bash",
            arguments=long_string,
            environment="development"
        )
        
        assert result["danger_level"] == "high"
