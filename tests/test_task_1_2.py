"""Task 1.2: 规则引擎实现 - 单元测试"""
import pytest
from services.rule_engine import RuleEngine, RuleResult


@pytest.fixture
def rule_engine():
    """创建规则引擎实例"""
    return RuleEngine("config/rules.yaml")


def test_rule_engine_initialization(rule_engine):
    """测试规则引擎初始化"""
    assert rule_engine is not None
    assert rule_engine.blacklist_rules is not None
    assert rule_engine.whitelist is not None
    assert rule_engine.automaton is not None


def test_extreme_language_detection(rule_engine):
    """测试极限用语检测"""
    # 测试包含极限用语的文本
    result = rule_engine.check_text("我们是行业第一的产品")
    assert result.is_violated is True
    assert "extreme_language" in result.violation_types
    
    result = rule_engine.check_text("这是最好的选择")
    assert result.is_violated is True
    assert "extreme_language" in result.violation_types


def test_medical_fraud_detection(rule_engine):
    """测试医疗违规检测"""
    result = rule_engine.check_text("包治百病的神药")
    assert result.is_violated is True
    assert "medical_fraud" in result.violation_types
    
    result = rule_engine.check_text("祖传秘方，药到病除")
    assert result.is_violated is True
    assert "medical_fraud" in result.violation_types


def test_contact_info_detection(rule_engine):
    """测试联系方式检测"""
    result = rule_engine.check_text("联系电话：13812345678")
    assert result.is_violated is True
    assert "phone_number" in result.violation_types
    
    result = rule_engine.check_text("微信号：abc123")
    assert result.is_violated is True
    assert "wechat_id" in result.violation_types


def test_whitelist_exemption(rule_engine):
    """测试白名单豁免"""
    # "国家级证书"在白名单中，应该被豁免
    result = rule_engine.check_text("获得国家级证书认证")
    # 由于白名单会移除"国家级证书"，剩余文本不应触发规则
    assert result.is_violated is False or "extreme_language" not in result.violation_types


def test_clean_text(rule_engine):
    """测试正常文本不触发规则"""
    result = rule_engine.check_text("这是一个正常的广告文案")
    assert result.is_violated is False
    assert len(result.violation_types) == 0


def test_empty_text(rule_engine):
    """测试空文本"""
    result = rule_engine.check_text("")
    assert result.is_violated is False
    assert len(result.violation_types) == 0


def test_multiple_violations(rule_engine):
    """测试多重违规"""
    text = "我们是最好的，包治百病，联系电话13812345678"
    result = rule_engine.check_text(text)
    assert result.is_violated is True
    assert len(result.violation_types) >= 2


def test_severity_levels(rule_engine):
    """测试严重程度判断"""
    # critical级别
    result = rule_engine.check_text("包治百病")
    assert result.severity == "critical"
    
    # high级别
    result = rule_engine.check_text("最好的产品")
    assert result.severity == "high"


def test_hot_reload(rule_engine):
    """测试规则热更新"""
    success = rule_engine.hot_reload()
    assert success is True
    assert rule_engine.last_reload_time is not None


def test_get_statistics(rule_engine):
    """测试统计信息"""
    stats = rule_engine.get_statistics()
    assert "total_rules" in stats
    assert "categories" in stats
    assert "whitelist_count" in stats
    assert stats["total_rules"] > 0
    assert len(stats["categories"]) > 0
