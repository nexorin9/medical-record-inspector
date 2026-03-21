"""
病历模板加载模块 - Medical Record Inspector
加载和存储优质病历模板，支持批量导入和模板元数据管理
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class TemplateMetadata:
    """模板元数据"""
    name: str
    type: str = "通用"  # 科室/疾病类型
    department: str = "通用"
    year: int = 2024
    score: float = 9.0  # 质量评分
    author: str = ""
    description: str = ""


class TemplateLoader:
    """病历模板加载器"""

    def __init__(self, template_dir: str = "templates"):
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.templates: Dict[str, Dict[str, Any]] = {}
        self.metadata: Dict[str, TemplateMetadata] = {}
        self._load_all()

    def _load_all(self) -> None:
        """批量加载模板目录下所有模板"""
        for ext in ['.txt', '.md', '.docx', '.pdf']:
            for file_path in self.template_dir.glob(f'*{ext}'):
                self._load_single(file_path)

    def _load_single(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """加载单个模板文件"""
        try:
            name = file_path.stem
            logger.info(f"正在加载模板: {name}")

            # 尝试读取 YAML 元数据文件
            yaml_path = file_path.with_suffix('.yaml')
            if yaml_path.exists():
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    meta_dict = yaml.safe_load(f)
                    metadata = TemplateMetadata(**meta_dict)
            else:
                # 默认元数据
                metadata = TemplateMetadata(
                    name=name,
                    type="通用",
                    description="用户上传的病历模板"
                )

            # 读取模板内容
            if file_path.suffix == '.pdf':
                # PDF 需要额外处理
                from src.extractor import extract_text_from_pdf
                content = extract_text_from_pdf(str(file_path))
            elif file_path.suffix == '.docx':
                from src.extractor import extract_text_from_docx
                content = extract_text_from_docx(str(file_path))
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

            self.templates[name] = {
                'path': str(file_path),
                'content': content,
                'length': len(content)
            }
            self.metadata[name] = metadata

            logger.info(f"成功加载模板: {name} ({len(content)} 字符)")
            return self.templates[name]

        except Exception as e:
            logger.error(f"加载模板失败 {file_path}: {e}")
            return None

    def add_template(self, content: str, name: str, metadata: TemplateMetadata = None) -> bool:
        """添加新模板

        Args:
            content: 模板内容
            name: 模板名称
            metadata: 元数据

        Returns:
            是否成功
        """
        try:
            # 保存内容
            file_path = self.template_dir / f"{name}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # 保存元数据
            if metadata:
                yaml_path = self.template_dir / f"{name}.yaml"
                with open(yaml_path, 'w', encoding='utf-8') as f:
                    yaml.dump(asdict(metadata), f, allow_unicode=True)

            # 更新内存
            self.templates[name] = {
                'path': str(file_path),
                'content': content,
                'length': len(content)
            }
            self.metadata[name] = metadata or TemplateMetadata(name=name, type="通用")

            logger.info(f"添加模板成功: {name}")
            return True
        except Exception as e:
            logger.error(f"添加模板失败 {name}: {e}")
            return False

    def delete_template(self, name: str) -> bool:
        """删除模板

        Args:
            name: 模板名称

        Returns:
            是否成功
        """
        try:
            if name not in self.templates:
                logger.warning(f"模板不存在: {name}")
                return False

            file_path = Path(self.templates[name]['path'])
            yaml_path = file_path.with_suffix('.yaml')

            # 删除物理文件
            file_path.unlink(missing_ok=True)
            yaml_path.unlink(missing_ok=True)

            # 删除内存数据
            del self.templates[name]
            if name in self.metadata:
                del self.metadata[name]

            logger.info(f"删除模板成功: {name}")
            return True
        except Exception as e:
            logger.error(f"删除模板失败 {name}: {e}")
            return False

    def update_template(self, name: str, content: str = None,
                       metadata: TemplateMetadata = None) -> bool:
        """更新模板

        Args:
            name: 模板名称
            content: 新内容
            metadata: 新元数据

        Returns:
            是否成功
        """
        if name not in self.templates:
            logger.warning(f"模板不存在: {name}")
            return False

        try:
            file_path = Path(self.templates[name]['path'])

            # 更新内容
            if content is not None:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.templates[name]['content'] = content
                self.templates[name]['length'] = len(content)

            # 更新元数据
            if metadata is not None:
                yaml_path = file_path.with_suffix('.yaml')
                with open(yaml_path, 'w', encoding='utf-8') as f:
                    yaml.dump(asdict(metadata), f, allow_unicode=True)
                self.metadata[name] = metadata

            logger.info(f"更新模板成功: {name}")
            return True
        except Exception as e:
            logger.error(f"更新模板失败 {name}: {e}")
            return False

    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """获取单个模板

        Args:
            name: 模板名称

        Returns:
            模板数据字典
        """
        return self.templates.get(name)

    def list_templates(self) -> List[Dict[str, Any]]:
        """列出所有模板

        Returns:
            模板列表
        """
        result = []
        for name, template in self.templates.items():
            meta = self.metadata.get(name, TemplateMetadata(name=name, type="通用"))
            result.append({
                'name': name,
                'type': meta.type,
                'department': meta.department,
                'year': meta.year,
                'score': meta.score,
                'length': template['length'],
                'description': meta.description
            })
        return result

    def get_templates_by_type(self, template_type: str) -> List[Dict[str, Any]]:
        """按类型筛选模板

        Args:
            template_type: 模板类型

        Returns:
            匹配的模板列表
        """
        return [t for t in self.list_templates() if t['type'] == template_type]

    def get_templates_by_department(self, department: str) -> List[Dict[str, Any]]:
        """按科室筛选模板

        Args:
            department: 科室名称

        Returns:
            匹配的模板列表
        """
        return [t for t in self.list_templates() if t['department'] == department]


# 全局加载器实例
_loader = None


def get_template_loader(template_dir: str = "templates") -> TemplateLoader:
    """获取全局模板加载器实例

    Args:
        template_dir: 模板目录路径

    Returns:
        TemplateLoader 实例
    """
    global _loader
    if _loader is None:
        _loader = TemplateLoader(template_dir)
    return _loader


if __name__ == '__main__':
    # 简单测试
    logging.basicConfig(level=logging.INFO)

    # 创建测试用模板目录
    test_dir = Path(__file__).parent.parent / 'data' / 'templates'
    test_dir.mkdir(parents=True, exist_ok=True)

    # 创建示例模板
    example_template = """病历模板示例

患者基本信息
姓名：{患者姓名}
性别：{性别}
年龄：{年龄岁}岁
职业：{职业}

主诉
{主诉内容}

现病史
{现病史内容}

既往史
{既往史内容}

体格检查
{体格检查内容}

辅助检查
{辅助检查内容}

诊断
{诊断结果}

诊疗经过
{诊疗经过}

出院诊断
{出院诊断}
"""

    template_file = test_dir / 'example_template.txt'
    template_file.write_text(example_template, encoding='utf-8')

    # 测试加载器
    loader = get_template_loader(str(test_dir))
    templates = loader.list_templates()

    print(f"加载的模板数量: {len(templates)}")
    for t in templates:
        print(f"  - {t['name']} ({t['type']})")

    # 获取单个模板
    template = loader.get_template('example_template')
    if template:
        print(f"\n模板内容长度: {template['length']}")
