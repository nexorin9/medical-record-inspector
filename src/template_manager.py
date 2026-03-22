"""
模板管理功能 - Medical Record Inspector
实现模板的增删改查功能，支持医院自定义模板库
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import asdict
import logging

# 添加 src 目录的父目录到路径
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from src.template_loader import TemplateLoader, TemplateMetadata

logger = logging.getLogger(__name__)


class TemplateManager:
    """模板管理员 - 提供完整的模板管理功能"""

    def __init__(self, template_dir: str = "templates"):
        """
        初始化模板管理员

        Args:
            template_dir: 模板目录路径
        """
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.loader = TemplateLoader(str(self.template_dir))

    def add_template(self, content: str, name: str,
                     metadata: TemplateMetadata = None) -> Dict[str, Any]:
        """
        添加新模板

        Args:
            content: 模板内容
            name: 模板名称
            metadata: 元数据

        Returns:
            操作结果字典
        """
        result = {'success': False, 'message': '', 'template': None}

        # 验证模板名称
        if not name or not name.strip():
            result['message'] = "模板名称不能为空"
            return result

        # 验证模板内容
        if not content or not content.strip():
            result['message'] = "模板内容不能为空"
            return result

        # 检查模板是否已存在
        if name in self.loader.templates:
            result['message'] = f"模板 '{name}' 已存在"
            return result

        # 添加模板
        try:
            success = self.loader.add_template(content, name, metadata)

            if success:
                template_info = self.loader.get_template(name)
                result['success'] = True
                result['message'] = f"模板 '{name}' 添加成功"
                result['template'] = {
                    'name': name,
                    'length': len(content),
                    'type': metadata.type if metadata else "通用",
                    'created': True
                }
            else:
                result['message'] = f"模板 '{name}' 添加失败"
        except Exception as e:
            result['message'] = f"添加模板时发生错误: {str(e)}"

        return result

    def delete_template(self, name: str) -> Dict[str, Any]:
        """
        删除模板

        Args:
            name: 模板名称

        Returns:
            操作结果字典
        """
        result = {'success': False, 'message': ''}

        if name not in self.loader.templates:
            result['message'] = f"模板 '{name}' 不存在"
            return result

        try:
            # 删除文件
            file_path = self.template_dir / f"{name}.txt"
            yaml_path = self.template_dir / f"{name}.yaml"

            files_deleted = []
            if file_path.exists():
                file_path.unlink()
                files_deleted.append(f"{name}.txt")

            if yaml_path.exists():
                yaml_path.unlink()
                files_deleted.append(f"{name}.yaml")

            # 从内存中删除
            del self.loader.templates[name]
            if name in self.loader.metadata:
                del self.loader.metadata[name]

            result['success'] = True
            result['message'] = f"模板 '{name}' 删除成功"
            result['deleted_files'] = files_deleted
        except Exception as e:
            result['message'] = f"删除模板时发生错误: {str(e)}"

        return result

    def update_template(self, name: str, content: Optional[str] = None,
                        metadata: Optional[TemplateMetadata] = None) -> Dict[str, Any]:
        """
        更新模板

        Args:
            name: 模板名称
            content: 新的模板内容（可选）
            metadata: 新的元数据（可选）

        Returns:
            操作结果字典
        """
        result = {'success': False, 'message': '', 'updated': []}

        if name not in self.loader.templates:
            result['message'] = f"模板 '{name}' 不存在"
            return result

        try:
            updated = []

            # 更新内容
            if content is not None:
                file_path = self.template_dir / f"{name}.txt"
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.loader.templates[name]['content'] = content
                self.loader.templates[name]['length'] = len(content)
                updated.append('content')

            # 更新元数据
            if metadata is not None:
                yaml_path = self.template_dir / f"{name}.yaml"
                with open(yaml_path, 'w', encoding='utf-8') as f:
                    import yaml
                    yaml.dump(asdict(metadata), f, allow_unicode=True)
                self.loader.metadata[name] = metadata
                updated.append('metadata')

            result['success'] = True
            result['message'] = f"模板 '{name}' 更新成功"
            result['updated'] = updated
        except Exception as e:
            result['message'] = f"更新模板时发生错误: {str(e)}"

        return result

    def list_templates(self) -> List[Dict[str, Any]]:
        """
        列出所有模板

        Returns:
            模板信息列表
        """
        return self.loader.list_templates()

    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取模板详情

        Args:
            name: 模板名称

        Returns:
            模板信息字典
        """
        return self.loader.get_template(name)

    def get_template_by_type(self, template_type: str) -> List[Dict[str, Any]]:
        """
        按类型获取模板列表

        Args:
            template_type: 模板类型

        Returns:
            匹配的模板列表
        """
        return self.loader.get_templates_by_type(template_type)

    def get_template_by_department(self, department: str) -> List[Dict[str, Any]]:
        """
        按科室获取模板列表

        Args:
            department: 科室名称

        Returns:
            匹配的模板列表
        """
        return self.loader.get_templates_by_department(department)

    def get_template_count(self) -> int:
        """
        获取模板总数

        Returns:
            模板数量
        """
        return len(self.loader.templates)

    def export_template(self, name: str, output_path: str) -> Dict[str, Any]:
        """
        导出模板到文件

        Args:
            name: 模板名称
            output_path: 输出路径

        Returns:
            操作结果字典
        """
        result = {'success': False, 'message': ''}

        template = self.loader.get_template(name)
        if not template:
            result['message'] = f"模板 '{name}' 不存在"
            return result

        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(template['content'])

            result['success'] = True
            result['message'] = f"模板 '{name}' 导出成功"
            result['output_path'] = output_path
        except Exception as e:
            result['message'] = f"导出模板时发生错误: {str(e)}"

        return result

    def import_template(self, file_path: str, name: str = None,
                        metadata: TemplateMetadata = None) -> Dict[str, Any]:
        """
        从文件导入模板

        Args:
            file_path: 输入文件路径
            name: 模板名称（可选，默认使用文件名）
            metadata: 元数据（可选）

        Returns:
            操作结果字典
        """
        result = {'success': False, 'message': ''}

        input_path = Path(file_path)
        if not input_path.exists():
            result['message'] = f"文件不存在: {file_path}"
            return result

        try:
            # 读取文件内容
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 确定模板名称
            template_name = name or input_path.stem

            # 添加模板
            result = self.add_template(content, template_name, metadata)
            if result['success']:
                result['message'] = f"模板 '{template_name}' 导入成功"

        except UnicodeDecodeError:
            result['message'] = "文件编码不正确，请使用 UTF-8 编码"
        except Exception as e:
            result['message'] = f"导入模板时发生错误: {str(e)}"

        return result

    def validate_template(self, name: str) -> Dict[str, Any]:
        """
        验证模板

        Args:
            name: 模板名称

        Returns:
            验证结果字典
        """
        result = {'valid': False, 'message': '', 'checks': {}}

        template = self.loader.get_template(name)
        if not template:
            result['message'] = f"模板 '{name}' 不存在"
            return result

        try:
            checks = {}

            # 检查内容长度
            content_length = len(template['content'])
            checks['length'] = {
                'passed': content_length > 0,
                'value': content_length,
                'min_length': 10
            }

            # 检查必需字段
            required_fields = ['姓名', '性别', '年龄', '主诉', '现病史', '诊断', '诊疗经过']
            missing_fields = [f for f in required_fields if f not in template['content']]

            checks['required_fields'] = {
                'passed': len(missing_fields) == 0,
                'missing': missing_fields,
                'total_required': len(required_fields)
            }

            # 检查基本结构
            sections = ['主诉', '现病史', '既往史', '体格检查', '辅助检查', '诊断', '诊疗经过']
            found_sections = [s for s in sections if s in template['content']]

            checks['basic_structure'] = {
                'passed': len(found_sections) >= 3,
                'found': found_sections,
                'total_sections': len(sections)
            }

            # 综合判断
            all_passed = (checks['length']['passed'] and
                         checks['required_fields']['passed'] and
                         checks['basic_structure']['passed'])

            result['valid'] = all_passed
            result['message'] = "模板验证通过" if all_passed else "模板验证未通过"
            result['checks'] = checks

        except Exception as e:
            result['message'] = f"验证模板时发生错误: {str(e)}"

        return result


def create_template_manager(template_dir: str = "templates") -> TemplateManager:
    """创建模板管理员"""
    return TemplateManager(template_dir)


if __name__ == "__main__":
    # 简单测试
    logging.basicConfig(level=logging.INFO)

    print("=== Template Manager 测试 ===\n")

    # 创建管理员
    manager = create_template_manager()

    # 测试添加模板
    print("1. 测试添加模板:")
    new_template = """患者基本信息
姓名：李四
性别：女
年龄：32岁

主诉
头痛头晕3天。

现病史
患者3天前无明显诱因出现头痛。

既往史
否认高血压史。

诊断
血管性头痛。

诊疗经过
给予对症治疗。
"""
    result = manager.add_template(new_template, "neurology_template")
    print(f"   {result['message']}")

    # 测试列出模板
    print("\n2. 测试列出模板:")
    templates = manager.list_templates()
    print(f"   共有 {len(templates)} 个模板")
    for t in templates:
        print(f"   - {t['name']} ({t['type']})")

    # 测试获取模板
    print("\n3. 测试获取模板:")
    template = manager.get_template("neurology_template")
    if template:
        print(f"   模板长度: {template['length']} 字符")

    # 测试验证模板
    print("\n4. 测试验证模板:")
    validation = manager.validate_template("neurology_template")
    print(f"   验证结果: {validation['message']}")
    print(f"   长度检查: {validation['checks']['length']}")
    print(f"   字段检查: {validation['checks']['required_fields']}")

    # 测试更新模板
    print("\n5. 测试更新模板:")
    update_result = manager.update_template("neurology_template", content=new_template + "\n补充内容")
    print(f"   {update_result['message']}")
    print(f"   更新字段: {update_result['updated']}")

    # 测试删除模板
    print("\n6. 测试删除模板:")
    delete_result = manager.delete_template("neurology_template")
    print(f"   {delete_result['message']}")

    # 测试导出模板
    print("\n7. 测试导出模板:")
    export_result = manager.export_template("example_good_case", "data/exported_template.txt")
    print(f"   {export_result['message']}")

    # 测试导入模板
    print("\n8. 测试导入模板:")
    import_result = manager.import_template("data/exported_template.txt", "imported_template")
    print(f"   {import_result['message']}")
