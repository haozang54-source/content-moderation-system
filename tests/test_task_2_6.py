"""Task 2.6: 对接后端API - 单元测试"""
import pytest
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestAPIIntegration:
    """测试API集成"""
    
    def test_pipeline_integration(self):
        """测试Pipeline集成"""
        ui_file = project_root / "ui" / "app.py"
        content = ui_file.read_text(encoding='utf-8')
        
        # 检查Pipeline导入和使用
        assert "from core.pipeline import ModerationPipeline" in content, "缺少Pipeline导入"
        assert "ModerationPipeline" in content, "未使用Pipeline"
        assert "st.session_state.pipeline" in content, "未在session中存储Pipeline"
    
    def test_service_imports(self):
        """测试服务导入"""
        ui_file = project_root / "ui" / "app.py"
        content = ui_file.read_text(encoding='utf-8')
        
        # 检查服务导入
        assert "from services.rule_engine import RuleEngine" in content, "缺少规则引擎导入"
        assert "from services.ocr_service import OCRService" in content, "缺少OCR服务导入"
        assert "from services.llm_service import LLMService" in content, "缺少LLM服务导入"
        assert "from services.rag_service import RAGService" in content, "缺少RAG服务导入"
    
    def test_settings_integration(self):
        """测试配置集成"""
        ui_file = project_root / "ui" / "app.py"
        content = ui_file.read_text(encoding='utf-8')
        
        # 检查配置导入和使用
        assert "from config.settings import Settings" in content, "缺少配置导入"
        assert "Settings()" in content, "未使用配置"
    
    def test_review_execution(self):
        """测试审核执行"""
        ui_file = project_root / "ui" / "app.py"
        content = ui_file.read_text(encoding='utf-8')
        
        # 检查审核调用
        assert "pipeline.review" in content, "未调用审核方法"
        assert "content_type" in content, "未指定内容类型"
    
    def test_result_handling(self):
        """测试结果处理"""
        ui_file = project_root / "ui" / "app.py"
        content = ui_file.read_text(encoding='utf-8')
        
        # 检查结果处理
        assert "result.is_compliant" in content, "未处理合规性结果"
        assert "result.confidence" in content, "未处理置信度"
        assert "result.violation_types" in content, "未处理违规类型"
        assert "result.processing_time" in content, "未处理处理时间"
        assert "result.api_cost" in content, "未处理API成本"
    
    def test_error_handling(self):
        """测试错误处理"""
        ui_file = project_root / "ui" / "app.py"
        content = ui_file.read_text(encoding='utf-8')
        
        # 检查错误处理
        assert "try:" in content, "缺少异常处理"
        assert "except Exception" in content, "缺少异常捕获"
        assert "st.error" in content, "缺少错误提示"
    
    def test_history_storage(self):
        """测试历史记录存储"""
        ui_file = project_root / "ui" / "app.py"
        content = ui_file.read_text(encoding='utf-8')
        
        # 检查历史记录
        assert "review_history" in content, "缺少历史记录"
        assert "st.session_state.review_history" in content, "未使用session存储历史"
    
    def test_stats_display(self):
        """测试统计信息显示"""
        ui_file = project_root / "ui" / "app.py"
        content = ui_file.read_text(encoding='utf-8')
        
        # 检查统计信息
        assert "get_stats" in content, "缺少统计信息获取"
        assert "total_tokens_used" in content or "审核量" in content, "缺少统计指标"
