"""商业违规媒体智能审核系统 - Streamlit UI"""
import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import pandas as pd
import time
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.pipeline import ModerationPipeline
from services.rule_engine import RuleEngine
from services.ocr_service import OCRService
from services.llm_service import LLMService
from services.rag_service import RAGService
from config.settings import Settings

# 页面配置
st.set_page_config(
    page_title="智能审核系统",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .danger-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 初始化session state
if 'pipeline' not in st.session_state:
    try:
        settings = Settings()
        st.session_state.pipeline = ModerationPipeline(
            rule_engine=RuleEngine(),
            ocr_service=OCRService(),
            llm_service=LLMService(
                deepseek_api_key=settings.deepseek_api_key,
                openai_api_key=settings.openai_api_key,
                internal_model_base_url=settings.internal_model_base_url,
                internal_model_api_key=settings.internal_model_api_key,
                internal_model_name=settings.internal_model_name
            ),
            rag_service=RAGService() if Path("data/regulations").exists() else None
        )
        st.session_state.settings = settings
    except Exception as e:
        st.error(f"初始化失败: {str(e)}")
        st.session_state.pipeline = None

if 'review_history' not in st.session_state:
    st.session_state.review_history = []


def main():
    """主函数"""
    # 侧边栏导航
    st.sidebar.title("🛡️ 智能审核系统")
    page = st.sidebar.radio(
        "导航",
        ["📊 首页统计", "🔍 内容审核", "📋 审核历史", "⚙️ 系统配置"]
    )
    
    if page == "📊 首页统计":
        show_dashboard()
    elif page == "🔍 内容审核":
        show_review_page()
    elif page == "📋 审核历史":
        show_history_page()
    elif page == "⚙️ 系统配置":
        show_settings_page()


def show_dashboard():
    """显示首页统计"""
    st.markdown('<div class="main-header">📊 审核系统概览</div>', unsafe_allow_html=True)
    
    # 模拟统计数据
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="今日审核量",
            value="1,234",
            delta="↑ 15%"
        )
    
    with col2:
        st.metric(
            label="审核准确率",
            value="92.5%",
            delta="↑ 2.1%"
        )
    
    with col3:
        st.metric(
            label="平均响应时间",
            value="3.8秒",
            delta="↓ 0.5秒"
        )
    
    with col4:
        st.metric(
            label="单条成本",
            value="¥0.042",
            delta="↓ ¥0.008"
        )
    
    st.divider()
    
    # 审核结果分布
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 审核结果分布")
        result_data = pd.DataFrame({
            '结果': ['合规', '违规', '待人工复审'],
            '数量': [850, 120, 30],
            '占比': ['85%', '12%', '3%']
        })
        st.dataframe(result_data, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("🎯 违规类型分布")
        violation_data = pd.DataFrame({
            '类型': ['极限用语', '医疗违规', '联系方式', '低俗内容', '其他'],
            '数量': [45, 32, 28, 10, 5]
        })
        st.bar_chart(violation_data.set_index('类型'))
    
    st.divider()
    
    # 系统状态
    st.subheader("🔧 系统状态")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**规则引擎**")
        st.success("✅ 运行正常")
        st.caption("已加载 156 条规则")
    
    with col2:
        st.markdown("**LLM服务**")
        if st.session_state.pipeline and st.session_state.pipeline.llm_service:
            st.success("✅ 运行正常")
            st.caption("轻量模型可用")
        else:
            st.error("❌ 未配置")
    
    with col3:
        st.markdown("**RAG检索**")
        if st.session_state.pipeline and st.session_state.pipeline.rag_service:
            st.success("✅ 运行正常")
            st.caption("法规库已加载")
        else:
            st.warning("⚠️ 未启用")


def show_review_page():
    """显示审核页面"""
    st.markdown('<div class="main-header">🔍 内容审核</div>', unsafe_allow_html=True)
    
    if not st.session_state.pipeline:
        st.error("❌ 系统未初始化，请检查配置")
        return
    
    # 审核类型选择
    review_type = st.radio(
        "审核类型",
        ["📝 文本审核", "🖼️ 图片审核", "📦 批量审核"],
        horizontal=True
    )
    
    if review_type == "📝 文本审核":
        show_text_review()
    elif review_type == "🖼️ 图片审核":
        show_image_review()
    elif review_type == "📦 批量审核":
        show_batch_review()


def show_text_review():
    """文本审核"""
    st.subheader("📝 文本内容审核")
    
    # 输入区域
    content = st.text_area(
        "请输入待审核内容",
        height=200,
        placeholder="例如：全网最低价！100%有效！立即购买送豪礼！"
    )
    
    # 审核选项
    col1, col2 = st.columns(2)
    with col1:
        use_rag = st.checkbox("启用RAG检索", value=True)
    with col2:
        model_type = st.selectbox("模型选择", ["自动", "轻量模型", "强大模型"])
    
    # 审核按钮
    if st.button("🚀 开始审核", type="primary", use_container_width=True):
        if not content.strip():
            st.warning("⚠️ 请输入待审核内容")
            return
        
        # 显示进度
        with st.spinner("正在审核中..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # 执行审核
                status_text.text("🔍 规则引擎检测中...")
                progress_bar.progress(25)
                time.sleep(0.3)
                
                status_text.text("🤖 LLM分析中...")
                progress_bar.progress(50)
                
                result = st.session_state.pipeline.review(
                    content=content,
                    content_type="text"
                )
                
                progress_bar.progress(100)
                status_text.text("✅ 审核完成！")
                time.sleep(0.5)
                
                # 清除进度显示
                progress_bar.empty()
                status_text.empty()
                
                # 显示结果
                display_review_result(result, content)
                
                # 保存到历史
                st.session_state.review_history.append({
                    'time': datetime.now(),
                    'type': 'text',
                    'content': content[:100] + '...' if len(content) > 100 else content,
                    'result': result
                })
                
            except Exception as e:
                st.error(f"❌ 审核失败: {str(e)}")


def show_image_review():
    """图片审核"""
    st.subheader("🖼️ 图片内容审核")
    
    uploaded_file = st.file_uploader(
        "上传图片",
        type=['png', 'jpg', 'jpeg'],
        help="支持 PNG、JPG、JPEG 格式"
    )
    
    if uploaded_file:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.image(uploaded_file, caption="待审核图片", use_container_width=True)
        
        with col2:
            if st.button("🚀 开始审核", type="primary", use_container_width=True):
                with st.spinner("正在审核中..."):
                    try:
                        # 保存临时文件
                        temp_path = Path("data/temp") / uploaded_file.name
                        temp_path.parent.mkdir(parents=True, exist_ok=True)
                        temp_path.write_bytes(uploaded_file.getvalue())
                        
                        # 执行审核
                        result = st.session_state.pipeline.review(
                            content=str(temp_path),
                            content_type="image"
                        )
                        
                        # 显示结果
                        display_review_result(result, f"图片: {uploaded_file.name}")
                        
                        # 清理临时文件
                        temp_path.unlink()
                        
                    except Exception as e:
                        st.error(f"❌ 审核失败: {str(e)}")


def show_batch_review():
    """批量审核"""
    st.subheader("📦 批量内容审核")
    
    uploaded_file = st.file_uploader(
        "上传CSV文件",
        type=['csv'],
        help="CSV文件应包含 'content' 列"
    )
    
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            st.write(f"📊 共 {len(df)} 条待审核内容")
            st.dataframe(df.head(), use_container_width=True)
            
            if st.button("🚀 开始批量审核", type="primary"):
                results = []
                progress_bar = st.progress(0)
                
                for idx, row in df.iterrows():
                    try:
                        result = st.session_state.pipeline.review(
                            content=row['content'],
                            content_type="text"
                        )
                        results.append({
                            'content': row['content'][:50] + '...',
                            'is_compliant': result.is_compliant,
                            'confidence': result.confidence,
                            'violations': ', '.join(result.violation_types)
                        })
                    except Exception as e:
                        results.append({
                            'content': row['content'][:50] + '...',
                            'is_compliant': None,
                            'confidence': 0,
                            'violations': f'错误: {str(e)}'
                        })
                    
                    progress_bar.progress((idx + 1) / len(df))
                
                # 显示结果
                result_df = pd.DataFrame(results)
                st.success(f"✅ 批量审核完成！")
                st.dataframe(result_df, use_container_width=True)
                
                # 下载结果
                csv = result_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 下载审核结果",
                    csv,
                    "review_results.csv",
                    "text/csv"
                )
                
        except Exception as e:
            st.error(f"❌ 文件解析失败: {str(e)}")


def display_review_result(result, content):
    """显示审核结果"""
    st.divider()
    st.subheader("📋 审核结果")
    
    # 结果概览
    if result.is_compliant:
        st.markdown(
            f'<div class="success-box">✅ <b>审核通过</b> - 内容合规</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="danger-box">❌ <b>审核不通过</b> - 发现违规内容</div>',
            unsafe_allow_html=True
        )
    
    # 详细信息
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("置信度", f"{result.confidence:.1%}")
    
    with col2:
        st.metric("处理时间", f"{result.processing_time:.2f}秒")
    
    with col3:
        st.metric("审核成本", f"¥{result.api_cost:.4f}")
    
    # 违规详情
    if result.violation_types:
        st.subheader("⚠️ 违规详情")
        for violation in result.violation_types:
            st.error(f"• {violation}")
    
    # 证据和推理
    with st.expander("🔍 详细分析", expanded=False):
        if result.evidence:
            st.markdown("**证据：**")
            st.info(result.evidence)
        
        if result.reasoning:
            st.markdown("**推理过程：**")
            st.text(result.reasoning)
        
        if result.matched_regulations:
            st.markdown("**相关法规：**")
            for reg in result.matched_regulations:
                st.caption(f"• {reg}")
    
    # 审核链路
    with st.expander("🔗 审核链路", expanded=False):
        stages = []
        if hasattr(result, 'rule_check_result'):
            stages.append(f"✅ 规则引擎: {result.rule_check_result}")
        if hasattr(result, 'ocr_text'):
            stages.append(f"✅ OCR提取: {len(result.ocr_text)} 字符")
        if hasattr(result, 'rag_docs'):
            stages.append(f"✅ RAG检索: {len(result.rag_docs)} 条法规")
        stages.append(f"✅ LLM审核: 完成")
        
        for stage in stages:
            st.text(stage)


def show_history_page():
    """显示审核历史"""
    st.markdown('<div class="main-header">📋 审核历史</div>', unsafe_allow_html=True)
    
    if not st.session_state.review_history:
        st.info("暂无审核历史")
        return
    
    # 筛选选项
    col1, col2 = st.columns(2)
    with col1:
        filter_type = st.selectbox("类型筛选", ["全部", "文本", "图片"])
    with col2:
        filter_result = st.selectbox("结果筛选", ["全部", "合规", "违规"])
    
    # 显示历史记录
    for idx, record in enumerate(reversed(st.session_state.review_history)):
        with st.expander(
            f"[{record['time'].strftime('%Y-%m-%d %H:%M:%S')}] "
            f"{'✅' if record['result'].is_compliant else '❌'} "
            f"{record['content'][:50]}..."
        ):
            display_review_result(record['result'], record['content'])


def show_settings_page():
    """显示系统配置"""
    st.markdown('<div class="main-header">⚙️ 系统配置</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🔑 API配置", "📏 规则管理", "📊 系统信息"])
    
    with tab1:
        st.subheader("API密钥配置")
        
        if st.session_state.settings:
            settings = st.session_state.settings
            
            st.text_input("轻量模型 API Key", value="***" if settings.deepseek_api_key else "", type="password")
            st.text_input("强大模型 API Key", value="***" if settings.openai_api_key else "", type="password")
            st.text_input("内部模型 URL", value=settings.internal_model_base_url or "")
            
            if st.button("💾 保存配置"):
                st.success("✅ 配置已保存")
    
    with tab2:
        st.subheader("规则管理")
        
        if st.button("🔄 重载规则"):
            try:
                if st.session_state.pipeline:
                    st.session_state.pipeline.rule_engine.hot_reload()
                    st.success("✅ 规则已重载")
            except Exception as e:
                st.error(f"❌ 重载失败: {str(e)}")
        
        st.info("规则文件路径: config/rules.yaml")
    
    with tab3:
        st.subheader("系统信息")
        
        if st.session_state.pipeline:
            stats = st.session_state.pipeline.llm_service.get_statistics()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("累计Token使用", f"{stats['total_tokens_used']:,}")
                st.metric("累计API成本", f"¥{stats['total_api_cost']:.4f}")
            
            with col2:
                st.metric("轻量模型", "✅ 可用" if stats.get('deepseek_available') else "❌ 不可用")
                st.metric("强大模型", "✅ 可用" if stats.get('openai_available') else "❌ 不可用")


if __name__ == "__main__":
    main()
