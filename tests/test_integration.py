"""
集成测试 - Medical Record Inspector
端到端测试完整检测流程
"""

import pytest
import sys
import os
from pathlib import Path
import json
import tempfile
import shutil

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 添加 tests 目录到路径
sys.path.insert(0, str(Path(__file__).parent))


class TestCLISingleDetection:
    """测试 CLI 单个病历检测"""

    def test_cli_single_basic(self):
        """测试 CLI 基本单病历检测"""
        from src.cli import cmd_single, load_record_file

        # 测试加载文件
        sample_path = Path(__file__).parent.parent / "data" / "samples" / "sample.txt"
        if sample_path.exists():
            text = load_record_file(str(sample_path))
            assert len(text) > 0
            assert "张三" in text

    def test_cli_single_with_inspector(self):
        """测试 CLI 单病历检测与 Inspector 集成"""
        from src.cli import cmd_single, setup_logging
        from src.inspector import create_inspector

        # 创建临时模板目录
        with tempfile.TemporaryDirectory() as tmpdir:
            # 复制模板到临时目录
            src_template = Path(__file__).parent.parent / "templates" / "example_good_case.txt"
            dst_template = Path(tmpdir) / "example_good_case.txt"

            if src_template.exists():
                shutil.copy(str(src_template), str(dst_template))

                # 创建 Inspector
                inspector = create_inspector(tmpdir)

                # 加载测试病历
                sample_path = Path(__file__).parent.parent / "data" / "samples" / "sample.txt"
                if sample_path.exists():
                    with open(sample_path, 'r', encoding='utf-8') as f:
                        test_text = f.read()

                    # 分析病历
                    result = inspector.analyze(test_text)

                    # 验证结果结构
                    assert 'overall_score' in result
                    assert isinstance(result['overall_score'], float)
                    assert 0 <= result['overall_score'] <= 1


class TestCLIBatchDetection:
    """测试 CLI 批量检测"""

    def test_cli_batch_load_directory(self):
        """测试 CLI 从目录批量加载病历"""
        from src.cli import load_records_from_directory

        # 测试加载 samples 目录
        samples_dir = Path(__file__).parent.parent / "data" / "samples"
        if samples_dir.exists():
            records = load_records_from_directory(str(samples_dir))
            # 至少应该加载到一个文件
            assert len(records) >= 1
            # 验证每个记录结构
            for record in records:
                assert 'filename' in record
                assert 'text' in record
                assert len(record['text']) > 0

    def test_cli_batch_analysis(self):
        """测试 CLI 批量分析"""
        from src.inspector import create_inspector

        # 创建 Inspector
        with tempfile.TemporaryDirectory() as tmpdir:
            # 复制模板
            src_template = Path(__file__).parent.parent / "templates" / "example_good_case.txt"
            if src_template.exists():
                shutil.copy(str(src_template), str(Path(tmpdir) / "example_good_case.txt"))

            inspector = create_inspector(tmpdir)

            # 创建测试病历列表
            test_records = [
                """患者基本信息
姓名：李四
性别：男
年龄：50岁

主诉
头晕头痛2天。

现病史
患者2天前无明显诱因出现头晕，伴头痛，
无恶心呕吐。

既往史
否认高血压史。
""",
                """患者基本信息
姓名：王五
性别：女
年龄：35岁

主诉
发热咳嗽1天。

现病史
患者1天前受凉后出现发热，
体温最高38度。

既往史
否认慢性疾病史。
"""
            ]

            # 批量分析
            results = inspector.analyze_batch(test_records)

            assert len(results) == 2
            for result in results:
                assert 'overall_score' in result
                assert 'defect_count' in result


class TestAPIServices:
    """测试 API 服务"""

    def test_api_health_endpoint(self):
        """测试 API /health 端点"""
        from src.api import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == "healthy"

    def test_api_list_templates_endpoint(self):
        """测试 API /templates 端点"""
        from src.api import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/templates")

        # 如果加载成功，应该返回 200
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_api_analyze_endpoint(self):
        """测试 API /analyze 端点"""
        from src.api import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # 测试病历文本
        test_record = """
患者基本信息
姓名：赵六
性别：男
年龄：40岁

主诉
胃痛3天。

现病史
患者3天前出现上腹疼痛，
伴反酸。

既往史
否认重大疾病史。
"""

        request_data = {
            "text": test_record,
            "template": None
        }

        response = client.post("/analyze", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert 'overall_score' in data
        assert isinstance(data['overall_score'], (int, float))


class TestHybridMode:
    """测试混合模式检测"""

    def test_hybrid_mode_import(self):
        """测试混合模式模块导入"""
        from src.hybrid_checker import HybridChecker
        assert HybridChecker is not None

    def test_hybrid_mode_integration(self):
        """测试混合模式与Inspector集成"""
        from src.inspector import create_inspector
        from src.hybrid_checker import HybridChecker

        with tempfile.TemporaryDirectory() as tmpdir:
            # 复制模板
            src_template = Path(__file__).parent.parent / "templates" / "example_good_case.txt"
            if src_template.exists():
                shutil.copy(str(src_template), str(Path(tmpdir) / "example_good_case.txt"))

                inspector = create_inspector(tmpdir)

                test_record = """
患者基本信息
姓名：测试患者
性别：男
年龄：30岁

主诉
身体不适。

现病史
患者近期感觉不适。

既往史
否认疾病史。
"""

                # 使用Inspector分析（内部包含混合检测逻辑）
                result = inspector.analyze(test_record)

                # 验证结果包含缺陷检测
                assert 'defects' in result
                assert 'defect_count' in result
                assert isinstance(result['defects'], list)


class TestTemplateLoaderIntegration:
    """测试模板加载器集成"""

    def test_template_loading(self):
        """测试从真实模板目录加载"""
        from src.template_loader import get_template_loader

        templates_dir = Path(__file__).parent.parent / "templates"
        if templates_dir.exists():
            loader = get_template_loader(str(templates_dir))
            templates = loader.list_templates()

            assert len(templates) >= 1
            # 验证模板结构（list_templates 返回的是元数据列表）
            for template in templates:
                assert 'name' in template
                assert 'type' in template
                assert 'department' in template
                assert 'score' in template

    def test_template_metadata(self):
        """测试模板元数据"""
        from src.template_loader import get_template_loader

        templates_dir = Path(__file__).parent.parent / "templates"
        if templates_dir.exists():
            loader = get_template_loader(str(templates_dir))

            # 获取单个模板以验证内容
            templates = loader.list_templates()
            first_template = templates[0]

            # 验证元数据字段
            assert 'name' in first_template
            assert 'type' in first_template
            assert 'department' in first_template

            # 验证 get_template 包含 content
            template_detail = loader.get_template(first_template['name'])
            assert template_detail is not None
            assert 'content' in template_detail
            assert 'path' in template_detail
            assert 'length' in template_detail

            # 验证内容不为空
            assert len(template_detail['content']) > 0


class TestEmbedderIntegration:
    """测试嵌入模块集成"""

    def test_embedder_basic(self):
        """测试基本嵌入功能"""
        from src.embedder import get_embedder

        embedder = get_embedder()

        test_text = "这是一个测试病历。患者有发热症状。"
        embedding = embedder.embed(test_text)

        assert embedding is not None
        assert len(embedding) > 0

    def test_embedder_batch(self):
        """测试批量嵌入"""
        from src.embedder import get_embedder

        embedder = get_embedder()

        texts = [
            "第一段病历文本。",
            "第二段病历文本。",
            "第三段病历文本。"
        ]

        embeddings = embedder.embed_batch(texts)

        assert len(embeddings) == 3
        for emb in embeddings:
            assert len(emb) > 0


class TestSimilarityIntegration:
    """测试相似度计算集成"""

    def test_similarity_calculation(self):
        """测试余弦相似度计算"""
        from src.similarity import get_similarity_calculator

        calculator = get_similarity_calculator()

        import numpy as np
        vec1 = np.array([1, 2, 3])
        vec2 = np.array([1, 2, 3])

        similarity = calculator.cosine_similarity_single(vec1, vec2)
        assert similarity == pytest.approx(1.0, rel=1e-5)

    def test_different_texts_different_similarity(self):
        """测试不同文本应该有较低相似度"""
        from src.embedder import get_embedder
        from src.similarity import get_similarity_calculator

        embedder = get_embedder()
        calculator = get_similarity_calculator()

        text1 = "患者有发热咳嗽症状。"
        text2 = "患者有胃痛和反酸症状。"

        emb1 = embedder.embed(text1)
        emb2 = embedder.embed(text2)

        similarity = calculator.cosine_similarity_single(emb1, emb2)
        # 相似度应该在 0-1 之间
        assert 0 <= similarity <= 1


class TestLocatorIntegration:
    """测试缺陷定位集成"""

    def test_locator_basic(self):
        """测试基本定位功能"""
        from src.locator import create_locator

        locator = create_locator()

        text1 = """患者基本信息
姓名：张三
主诉：发热咳嗽3天。
现病史：患者3天前受凉后出现发热。
"""
        text2 = """患者基本信息
姓名：李四
主诉：发热咳嗽2天。
现病史：患者2天前受凉后出现发热。
"""

        # 应该能处理
        result = locator.locate_defects(text1, text2)
        assert 'paragraph_scores' in result
        assert 'total_paragraphs' in result
        assert 'defect_count' in result


class TestEndToEndWorkflow:
    """端到端工作流测试"""

    def test_full_workflow_with_templates(self):
        """测试带模板的完整工作流"""
        from src.inspector import create_inspector

        # 使用真实模板目录
        templates_dir = Path(__file__).parent.parent / "templates"

        if templates_dir.exists():
            inspector = create_inspector(str(templates_dir))

            # 加载模板
            template_count = inspector.load_templates()
            assert template_count >= 1

            # 测试病历
            test_record = """
患者基本信息
姓名：测试患者
性别：男
年龄：45岁

主诉
反复上腹部不适1个月。

现病史
患者1个月前开始出现上腹部隐痛，
呈间歇性加重。进食后疼痛加重，
伴有反酸嗳气。

既往史
高血压病史3年，规律服药控制良好。
2型糖尿病病史2年，口服降糖药。

体格检查
T 36.5，P 75，R 18，BP 125/80mmHg。
腹平软，中上腹轻压痛，无反跳痛。

辅助检查
胃镜检查：慢性浅表性胃炎。
幽门螺杆菌检测：阳性。

初步诊断
1. 慢性浅表性胃炎 HP(+)
2. 高血压病1级
3. 2型糖尿病

诊疗经过
给予奥美拉唑、阿莫西林等药物治疗。
症状有所缓解。
"""

            # 分析
            result = inspector.analyze(test_record)

            # 验证完整结果
            assert 'overall_score' in result
            assert 'template_used' in result
            assert 'defect_count' in result
            assert 'defects' in result
            assert 'paragraph_analysis' in result
            assert 'chunk_analysis' in result

            # 验证分数范围
            assert 0 <= result['overall_score'] <= 1

    def test_full_workflow_without_template(self):
        """测试不指定模板的完整工作流"""
        from src.inspector import create_inspector

        templates_dir = Path(__file__).parent.parent / "templates"

        if templates_dir.exists():
            inspector = create_inspector(str(templates_dir))

            test_record = """
患者基本信息
姓名：测试患者
性别：女
年龄：30岁

主诉
头痛一天。

现病史
患者1天前出现头痛，
无恶心呕吐。

既往史
否认疾病史。
"""

            result = inspector.analyze(test_record)

            # 即使没有最佳模板，也应该返回结果
            assert 'overall_score' in result
            assert 'template_used' in result
            assert 'defect_count' in result


class TestReportGeneration:
    """测试报告生成"""

    def test_report_generation(self):
        """测试报告生成功能"""
        from src.inspector import create_inspector

        templates_dir = Path(__file__).parent.parent / "templates"

        if templates_dir.exists():
            inspector = create_inspector(str(templates_dir))

            test_record = """
患者基本信息
姓名：测试患者
性别：男
年龄：40岁

主诉
胸痛3小时。

现病史
患者3小时前突发胸痛，
伴冷汗。

既往史
冠心病史5年。
"""

            # 分析
            result = inspector.analyze(test_record)

            # 生成报告
            report = inspector.generate_report(result)

            # 验证报告结构
            assert 'analysis' in report
            assert 'summary' in report
            assert 'explanations' in report

            # 验证摘要
            summary = report['summary']
            assert 'overall_score' in summary
            assert 'risk_level' in summary
            assert 'defect_count' in summary
            assert 'summary_text' in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
