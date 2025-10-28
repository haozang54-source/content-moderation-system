"""启动Streamlit UI"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    os.system(f"streamlit run {project_root}/ui/app.py --server.port 8501")
