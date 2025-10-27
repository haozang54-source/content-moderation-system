"""Task 1.5: 多OCR引擎集成 - 单元测试"""
import pytest
from services.ocr_service import OCRService, OCRResult


@pytest.fixture
def ocr_service():
    """创建OCR服务实例"""
    return OCRService()


def test_ocr_service_initialization(ocr_service):
    """测试OCR服务初始化"""
    assert ocr_service is not None


def test_merge_ocr_results_single(ocr_service):
    """测试单个结果融合"""
    results = [
        OCRResult(text="测试文本", confidence=0.9, engine="paddle")
    ]
    merged = ocr_service.merge_ocr_results(results)
    assert merged == "测试文本"


def test_merge_ocr_results_multiple(ocr_service):
    """测试多个结果融合"""
    results = [
        OCRResult(text="文本A", confidence=0.7, engine="paddle"),
        OCRResult(text="文本B", confidence=0.9, engine="tesseract"),
        OCRResult(text="文本C", confidence=0.6, engine="cloud")
    ]
    merged = ocr_service.merge_ocr_results(results)
    # 应该选择置信度最高的
    assert merged == "文本B"


def test_merge_ocr_results_empty(ocr_service):
    """测试空结果融合"""
    results = []
    merged = ocr_service.merge_ocr_results(results)
    assert merged == ""


def test_merge_ocr_results_low_confidence(ocr_service):
    """测试低置信度结果过滤"""
    results = [
        OCRResult(text="文本A", confidence=0.3, engine="paddle"),
        OCRResult(text="文本B", confidence=0.4, engine="tesseract")
    ]
    merged = ocr_service.merge_ocr_results(results)
    # 所有结果置信度都低于0.5，应返回空
    assert merged == ""


def test_preprocess_image(ocr_service):
    """测试图像预处理"""
    image_path = "test.jpg"
    processed_path = ocr_service.preprocess_image(image_path)
    assert processed_path is not None


def test_get_statistics(ocr_service):
    """测试统计信息"""
    stats = ocr_service.get_statistics()
    assert "paddle_available" in stats
    assert "tesseract_available" in stats
    assert "cloud_available" in stats


@pytest.mark.asyncio
async def test_extract_text_multi_engine_mock(ocr_service):
    """测试多引擎提取（mock）"""
    # 由于没有实际图片，这里只测试方法存在性
    assert hasattr(ocr_service, 'extract_text_multi_engine')
    assert callable(ocr_service.extract_text_multi_engine)
