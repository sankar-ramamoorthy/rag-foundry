# src/ingestion_service/core/ocr/ocr_factory.py

import os
from typing import Dict

from ingestion_service.core.ocr.ocr import OCRExtractor
from ingestion_service.core.ocr.tesseract_ocr import TesseractOCR

# Register OCR engines here
OCR_ENGINES: Dict[str, OCRExtractor] = {
    TesseractOCR.name: TesseractOCR(),
}


def get_ocr_engine(name: str = "tesseract") -> OCRExtractor:
    """
    Return an OCR engine instance by name.
    Defaults to environment variable OCR_PROVIDER or 'tesseract'.
    """
    ocr_name = name or os.getenv("OCR_PROVIDER", "tesseract")
    engine = OCR_ENGINES.get(ocr_name.lower())
    if not engine:
        raise ValueError(f"OCR engine '{ocr_name}' is not registered")
    return engine
