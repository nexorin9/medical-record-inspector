"""
Medical Record Interpreter - 主入口
"""

__version__ = "0.1.0"
__author__ = "ChaosForge Agent"

from src.inspector import create_inspector, MedicalRecordInspector
from src.template_loader import get_template_loader
from src.embedder import get_embedder
from src.config import get_config

__all__ = [
    'create_inspector',
    'MedicalRecordInspector',
    'get_template_loader',
    'get_embedder',
    'get_config',
    '__version__'
]
