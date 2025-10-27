"""OCR服务"""
import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
import hashlib


@dataclass
class OCRResult:
    """OCR识别结果"""
    text: str
    confidence: float
    engine: str


class OCRService:
    """OCR服务（多引擎并行）"""

    def __init__(self):
        """初始化OCR服务"""
        self.paddle_available = False
        self.tesseract_available = False
        self.cloud_available = False
        
        self._init_engines()

    def _init_engines(self):
        """初始化OCR引擎"""
        # 尝试初始化PaddleOCR
        try:
            from paddleocr import PaddleOCR
            self.paddle_ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
            self.paddle_available = True
        except Exception as e:
            print(f"PaddleOCR初始化失败: {e}")
            self.paddle_ocr = None

        # 尝试初始化Tesseract
        try:
            import pytesseract
            self.tesseract = pytesseract
            self.tesseract_available = True
        except Exception as e:
            print(f"Tesseract初始化失败: {e}")
            self.tesseract = None

    async def paddle_ocr_extract(self, image_path: str) -> OCRResult:
        """使用PaddleOCR提取文本
        
        Args:
            image_path: 图片路径
            
        Returns:
            OCRResult: 识别结果
        """
        if not self.paddle_available:
            return OCRResult(text="", confidence=0.0, engine="paddle")

        try:
            result = self.paddle_ocr.ocr(image_path, cls=True)
            
            if not result or not result[0]:
                return OCRResult(text="", confidence=0.0, engine="paddle")
            
            texts = []
            confidences = []
            
            for line in result[0]:
                text = line[1][0]
                conf = line[1][1]
                texts.append(text)
                confidences.append(conf)
            
            merged_text = " ".join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return OCRResult(
                text=merged_text,
                confidence=avg_confidence,
                engine="paddle"
            )
        except Exception as e:
            print(f"PaddleOCR识别失败: {e}")
            return OCRResult(text="", confidence=0.0, engine="paddle")

    async def tesseract_ocr_extract(self, image_path: str) -> OCRResult:
        """使用Tesseract提取文本
        
        Args:
            image_path: 图片路径
            
        Returns:
            OCRResult: 识别结果
        """
        if not self.tesseract_available:
            return OCRResult(text="", confidence=0.0, engine="tesseract")

        try:
            from PIL import Image
            image = Image.open(image_path)
            text = self.tesseract.image_to_string(image, lang="chi_sim+eng")
            
            # Tesseract不直接提供置信度，使用固定值
            return OCRResult(
                text=text.strip(),
                confidence=0.8,
                engine="tesseract"
            )
        except Exception as e:
            print(f"Tesseract识别失败: {e}")
            return OCRResult(text="", confidence=0.0, engine="tesseract")

    async def cloud_ocr_extract(self, image_path: str) -> OCRResult:
        """使用云OCR提取文本
        
        Args:
            image_path: 图片路径
            
        Returns:
            OCRResult: 识别结果
        """
        # 云OCR实现（需要配置API密钥）
        return OCRResult(text="", confidence=0.0, engine="cloud")

    def merge_ocr_results(self, results: List[OCRResult]) -> str:
        """融合多个OCR结果
        
        Args:
            results: OCR结果列表
            
        Returns:
            str: 融合后的文本
        """
        # 过滤掉空结果
        valid_results = [r for r in results if r.text and r.confidence > 0.5]
        
        if not valid_results:
            return ""
        
        # 如果只有一个有效结果，直接返回
        if len(valid_results) == 1:
            return valid_results[0].text
        
        # 多个结果时，选择置信度最高的
        best_result = max(valid_results, key=lambda x: x.confidence)
        return best_result.text

    async def extract_text_multi_engine(self, image_path: str) -> str:
        """使用多引擎并行提取文本
        
        Args:
            image_path: 图片路径
            
        Returns:
            str: 提取的文本
        """
        # 并行调用多个引擎
        tasks = [
            self.paddle_ocr_extract(image_path),
            self.tesseract_ocr_extract(image_path),
            self.cloud_ocr_extract(image_path)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 过滤异常结果
        valid_results = [r for r in results if isinstance(r, OCRResult)]
        
        # 融合结果
        merged_text = self.merge_ocr_results(valid_results)
        
        return merged_text

    def preprocess_image(self, image_path: str) -> str:
        """图像预处理
        
        Args:
            image_path: 图片路径
            
        Returns:
            str: 预处理后的图片路径
        """
        # 实现图像预处理（灰度化、二值化、去噪等）
        # 这里简化处理，直接返回原路径
        return image_path

    def get_statistics(self) -> Dict:
        """获取统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            "paddle_available": self.paddle_available,
            "tesseract_available": self.tesseract_available,
            "cloud_available": self.cloud_available
        }
