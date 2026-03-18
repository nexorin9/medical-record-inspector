"""
测试用例 - Medical Record Inspector
模块：template_loader.py - 病历模板加载模块
"""

import pytest
import os
import yaml
from pathlib import Path
import tempfile

# 添加 src 目录到路径
for p in os.sys.path:
    if 'medical-record-inspector' in p:
        break
else:
    os.sys.path.insert(0, str(Path(__file__).parent.parent))


class TestTemplateMetadata:
    """测试模板元数据"""

    def test_template_metadata_defaults(self):
        """测试模板元数据默认值"""
        from src.template_loader import TemplateMetadata

        meta = TemplateMetadata(name="test_template", type="通用")
        assert meta.name == "test_template"
        assert meta.type == "通用"
        assert meta.department == "通用"
        assert meta.year == 2024
        assert meta.score == 9.0
        assert meta.author == ""
        assert meta.description == ""

    def test_template_metadata_custom(self):
        """测试自定义模板元数据"""
        from src.template_loader import TemplateMetadata

        meta = TemplateMetadata(
            name="pneumonia_template",
            type="呼吸内科",
            department="呼吸科",
            year=2023,
            score=9.5,
            author="Dr. Li",
            description="肺炎病历标准模板"
        )
        assert meta.name == "pneumonia_template"
        assert meta.type == "呼吸内科"
        assert meta.department == "呼吸科"
        assert meta.year == 2023
        assert meta.score == 9.5
        assert meta.author == "Dr. Li"
        assert meta.description == "肺炎病历标准模板"


class TestTemplateLoader:
    """测试模板加载器"""

    def test_init_creates_template_dir(self):
        """测试初始化时创建模板目录"""
        from src.template_loader import TemplateLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = TemplateLoader(tmpdir)
            assert Path(tmpdir).exists()
            assert Path(tmpdir).is_dir()

    def test_add_template(self):
        """测试添加模板"""
        from src.template_loader import TemplateLoader, TemplateMetadata

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = TemplateLoader(tmpdir)

            content = "测试模板内容\n患者信息：姓名：张三"
            metadata = TemplateMetadata(
                name="test_template",
                type="通用",
                description="测试模板"
            )

            result = loader.add_template(content, "test_template", metadata)
            assert result is True

            # 检查模板是否在列表中（list_templates 返回字典列表）
            templates = loader.list_templates()
            template_names = [t['name'] for t in templates]
            assert "test_template" in template_names

    def test_add_template_without_metadata(self):
        """测试添加模板不带元数据"""
        from src.template_loader import TemplateLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = TemplateLoader(tmpdir)

            content = "简单测试模板"
            result = loader.add_template(content, "simple_template")
            assert result is True

    def test_get_template(self):
        """测试获取单个模板"""
        from src.template_loader import TemplateLoader, TemplateMetadata

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = TemplateLoader(tmpdir)

            content = "测试模板内容"
            metadata = TemplateMetadata(name="test", type="通用")
            loader.add_template(content, "test", metadata)

            template = loader.get_template("test")
            assert template is not None
            assert template['content'] == content
            assert 'path' in template
            assert 'length' in template

    def test_get_template_not_found(self):
        """测试获取不存在的模板"""
        from src.template_loader import TemplateLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = TemplateLoader(tmpdir)

            template = loader.get_template("non_existent")
            assert template is None

    def test_list_templates_empty(self):
        """测试空目录列表模板"""
        from src.template_loader import TemplateLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = TemplateLoader(tmpdir)
            templates = loader.list_templates()

            assert isinstance(templates, list)

    def test_delete_template(self):
        """测试删除模板"""
        from src.template_loader import TemplateLoader, TemplateMetadata

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = TemplateLoader(tmpdir)

            content = "待删除模板"
            metadata = TemplateMetadata(name="to_delete", type="通用")
            loader.add_template(content, "to_delete", metadata)

            # 确认模板存在
            assert loader.get_template("to_delete") is not None

            # 删除模板
            result = loader.delete_template("to_delete")
            assert result is True

            # 确认模板已删除
            assert loader.get_template("to_delete") is None

    def test_delete_template_not_found(self):
        """测试删除不存在的模板"""
        from src.template_loader import TemplateLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = TemplateLoader(tmpdir)

            result = loader.delete_template("non_existent")
            assert result is False

    def test_update_template_content(self):
        """测试更新模板内容"""
        from src.template_loader import TemplateLoader, TemplateMetadata

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = TemplateLoader(tmpdir)

            content = "原始内容"
            metadata = TemplateMetadata(name="updatable", type="通用")
            loader.add_template(content, "updatable", metadata)

            # 更新内容
            new_content = "更新后的内容"
            result = loader.update_template("updatable", content=new_content)

            assert result is True
            template = loader.get_template("updatable")
            assert template['content'] == new_content

    def test_update_template_metadata(self):
        """测试更新模板元数据"""
        from src.template_loader import TemplateLoader, TemplateMetadata

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = TemplateLoader(tmpdir)

            content = "测试内容"
            metadata = TemplateMetadata(name="updatable_meta", type="旧类型")
            loader.add_template(content, "updatable_meta", metadata)

            # 更新元数据
            new_metadata = TemplateMetadata(
                name="updatable_meta",
                type="新类型",
                department="新科室"
            )
            result = loader.update_template("updatable_meta", metadata=new_metadata)

            assert result is True
            template = loader.get_template("updatable_meta")
            # 模板列表应反映新元数据
            template_info = next((t for t in loader.list_templates() if t['name'] == 'updatable_meta'), None)
            assert template_info is not None
            assert template_info['type'] == "新类型"

    def test_update_template_not_found(self):
        """测试更新不存在的模板"""
        from src.template_loader import TemplateLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = TemplateLoader(tmpdir)

            result = loader.update_template("non_existent", content="content")
            assert result is False

    def test_get_templates_by_type(self):
        """测试按类型筛选模板"""
        from src.template_loader import TemplateLoader, TemplateMetadata

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = TemplateLoader(tmpdir)

            # 添加不同类型的模板
            loader.add_template("内容1", "template1", TemplateMetadata(name="t1", type="呼吸内科"))
            loader.add_template("内容2", "template2", TemplateMetadata(name="t2", type="呼吸内科"))
            loader.add_template("内容3", "template3", TemplateMetadata(name="t3", type="消化内科"))

            # 按类型筛选
            respiratory_templates = loader.get_templates_by_type("呼吸内科")
            digestive_templates = loader.get_templates_by_type("消化内科")

            assert len(respiratory_templates) == 2
            assert len(digestive_templates) == 1
            assert all(t['type'] == "呼吸内科" for t in respiratory_templates)

    def test_get_templates_by_department(self):
        """测试按科室筛选模板"""
        from src.template_loader import TemplateLoader, TemplateMetadata

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = TemplateLoader(tmpdir)

            loader.add_template("内容1", "t1", TemplateMetadata(name="t1", department="呼吸科"))
            loader.add_template("内容2", "t2", TemplateMetadata(name="t2", department="呼吸科"))
            loader.add_template("内容3", "t3", TemplateMetadata(name="t3", department="消化科"))

            respiratory = loader.get_templates_by_department("呼吸科")
            digestive = loader.get_templates_by_department("消化科")

            assert len(respiratory) == 2
            assert len(digestive) == 1

    def test_load_yaml_metadata(self):
        """测试从 YAML 文件加载元数据"""
        from src.template_loader import TemplateLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建 YAML 元数据文件（使用 UTF-8 编码）
            yaml_path = Path(tmpdir) / "yamled_template.yaml"
            yaml_path.write_text(yaml.dump({
                'name': 'yamled_template',
                'type': '_yaml_type',
                'department': '_yaml_dept',
                'year': 2022,
                'score': 8.5,
                'author': 'yaml_author',
                'description': '_yaml_desc'
            }), encoding='utf-8')

            # 创建对应的内容文件（使用 UTF-8 编码）
            content_path = Path(tmpdir) / "yamled_template.txt"
            content_path.write_text("模板内容", encoding='utf-8')

            loader = TemplateLoader(tmpdir)
            template = loader.get_template("yamled_template")

            assert template is not None
            template_info = next((t for t in loader.list_templates() if t['name'] == 'yamled_template'), None)
            assert template_info is not None
            assert template_info['type'] == '_yaml_type'
            assert template_info['year'] == 2022


class TestGetTemplateLoader:
    """测试全局模板加载器实例"""

    def test_get_template_loader_returns_instance(self):
        """测试获取全局加载器实例"""
        from src.template_loader import get_template_loader

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = get_template_loader(tmpdir)
            assert loader is not None
            assert hasattr(loader, 'list_templates')

    def test_get_template_loader_caching(self):
        """测试全局加载器缓存"""
        from src.template_loader import get_template_loader, _loader

        with tempfile.TemporaryDirectory() as tmpdir:
            # 首次调用
            loader1 = get_template_loader(tmpdir)
            # 重置全局变量
            import src.template_loader as tl_module
            tl_module._loader = None
            # 第二次调用
            loader2 = get_template_loader(tmpdir)

            # 应该返回不同的实例（因为路径可能不同）
            assert loader1 is not None
            assert loader2 is not None


class TestTemplateLoaderIntegration:
    """测试模板加载器集成场景"""

    def test_full_workflow(self):
        """测试完整工作流：添加 -> 查询 -> 更新 -> 删除"""
        from src.template_loader import TemplateLoader, TemplateMetadata

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = TemplateLoader(tmpdir)

            # 1. 添加模板
            metadata = TemplateMetadata(name="workflow_test", type="测试类型", department="测试科室")
            loader.add_template("初始内容", "workflow_test", metadata)
            assert loader.get_template("workflow_test") is not None

            # 2. 查询模板
            templates = loader.list_templates()
            template_info = next((t for t in templates if t['name'] == 'workflow_test'), None)
            assert template_info is not None
            assert template_info['type'] == "测试类型"

            # 3. 更新模板
            loader.update_template("workflow_test", content="更新后的内容")
            template = loader.get_template("workflow_test")
            assert template['content'] == "更新后的内容"

            # 4. 删除模板
            loader.delete_template("workflow_test")
            assert loader.get_template("workflow_test") is None
