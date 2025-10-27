"""Task 1.1: 项目脚手架搭建 - 单元测试"""
import os
import pytest
from pathlib import Path


def test_project_structure():
    """测试项目目录结构是否正确创建"""
    base_dir = Path(__file__).parent.parent
    
    # 检查主要目录
    assert (base_dir / "api").exists()
    assert (base_dir / "core").exists()
    assert (base_dir / "services").exists()
    assert (base_dir / "models").exists()
    assert (base_dir / "utils").exists()
    assert (base_dir / "config").exists()
    assert (base_dir / "data").exists()
    assert (base_dir / "scripts").exists()
    assert (base_dir / "tests").exists()


def test_config_files():
    """测试配置文件是否存在"""
    base_dir = Path(__file__).parent.parent
    
    assert (base_dir / "requirements.txt").exists()
    assert (base_dir / ".env.example").exists()
    assert (base_dir / ".gitignore").exists()
    assert (base_dir / "config" / "rules.yaml").exists()
    assert (base_dir / "config" / "prompts.yaml").exists()


def test_settings_import():
    """测试配置模块是否可以正常导入"""
    from config.settings import settings
    
    assert settings is not None
    assert hasattr(settings, "deepseek_api_key")
    assert hasattr(settings, "database_url")
    assert hasattr(settings, "redis_url")


def test_settings_default_values():
    """测试配置默认值"""
    from config.settings import settings
    
    assert settings.confidence_threshold_high == 0.9
    assert settings.confidence_threshold_low == 0.6
    assert settings.max_workers == 4
    assert settings.log_level == "INFO"
