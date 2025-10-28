"""Task 2.5: Streamlit UI搭建 - 单元测试"""
import pytest
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestStreamlitUI:
    """测试Streamlit UI"""
    
    def test_ui_file_exists(self):
        """测试UI文件存在"""
        ui_file = project_root / "ui" / "app.py"
        assert ui_file.exists(), "UI文件不存在"
        assert ui_file.stat().st_size > 0, "UI文件为空"
    
    def test_ui_imports(self):
        """测试UI导入"""
        try:
            import streamlit
            assert streamlit is not None
        except ImportError:
            pytest.skip("Streamlit未安装")
    
    def test_ui_structure(self):
        """测试UI文件结构"""
        ui_file = project_root / "ui" / "app.py"
        content = ui_file.read_text(encoding='utf-8')
        
        # 检查关键函数
        assert "def main()" in content, "缺少main函数"
        assert "def show_dashboard()" in content, "缺少首页函数"
        assert "def show_review_page()" in content, "缺少审核页面函数"
        assert "def show_history_page()" in content, "缺少历史页面函数"
        assert "def show_settings_page()" in content, "缺少设置页面函数"
    
    def test_ui_pages(self):
        """测试UI页面定义"""
        ui_file = project_root / "ui" / "app.py"
        content = ui_file.read_text(encoding='utf-8')
        
        # 检查页面导航
        assert "首页统计" in content, "缺少首页统计页面"
        assert "内容审核" in content, "缺少内容审核页面"
        assert "审核历史" in content, "缺少审核历史页面"
        assert "系统配置" in content, "缺少系统配置页面"
    
    def test_review_types(self):
        """测试审核类型"""
        ui_file = project_root / "ui" / "app.py"
        content = ui_file.read_text(encoding='utf-8')
        
        # 检查审核类型
        assert "文本审核" in content, "缺少文本审核"
        assert "图片审核" in content, "缺少图片审核"
        assert "批量审核" in content, "缺少批量审核"
    
    def test_ui_components(self):
        """测试UI组件"""
        ui_file = project_root / "ui" / "app.py"
        content = ui_file.read_text(encoding='utf-8')
        
        # 检查Streamlit组件
        assert "st.metric" in content, "缺少指标组件"
        assert "st.dataframe" in content, "缺少数据表格组件"
        assert "st.button" in content, "缺少按钮组件"
        assert "st.text_area" in content, "缺少文本输入组件"
        assert "st.file_uploader" in content, "缺少文件上传组件"
    
    def test_result_display(self):
        """测试结果显示"""
        ui_file = project_root / "ui" / "app.py"
        content = ui_file.read_text(encoding='utf-8')
        
        # 检查结果显示函数
        assert "def display_review_result" in content, "缺少结果显示函数"
        assert "置信度" in content, "缺少置信度显示"
        assert "处理时间" in content, "缺少处理时间显示"
        assert "审核成本" in content, "缺少成本显示"
    
    def test_run_script_exists(self):
        """测试启动脚本存在"""
        run_script = project_root / "run_ui.py"
        assert run_script.exists(), "启动脚本不存在"
        
        content = run_script.read_text(encoding='utf-8')
        assert "streamlit run" in content, "启动脚本缺少streamlit命令"
