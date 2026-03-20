"""
Unit tests for test case generators.
"""

import pytest
from pydantic import ValidationError

from generators.test_cases import TestCaseGenerator


class TestTestCaseGenerator:
    """TestCaseGenerator 类测试"""

    def test_init(self):
        """测试初始化"""
        generator = TestCaseGenerator()
        assert generator is not None

    def test_generate_incomplete_case(self):
        """测试生成缺失字段病历"""
        generator = TestCaseGenerator()
        case = generator.generate_incomplete_case()

        assert case["department"] == "内科"
        assert case["case_type"] == "门诊"
        assert case["main_complaint"] == "咳嗽"
        # 缺少一些必填字段
        assert "past_history" not in case

    def test_generate_inconsistent_case(self):
        """测试生成逻辑矛盾病历"""
        generator = TestCaseGenerator()
        case = generator.generate_inconsistent_case()

        assert case["department"] == "外科"
        assert case["diagnosis"] == "急性化脓性阑尾炎"
        # 包含禁忌药物
        assert "华法林" in case["prescription"]

    def test_generate_delayed_case(self):
        """测试生成处理延迟病历"""
        generator = TestCaseGenerator()
        case = generator.generate_delayed_case()

        assert case["department"] == "内科"
        assert case["case_type"] == "急诊"
        assert case["diagnosis"] == "急性心肌梗死"

    def test_generate_nonstandard_case(self):
        """测试生成格式不规范病历"""
        generator = TestCaseGenerator()
        case = generator.generate_nonstandard_case()

        assert case["department"] == "妇科"
        # 内容含有口语化表达（不规范）
        assert "肚子疼" in case["present_illness"]
        assert "就是" in case["present_illness"]  # 口语化词汇

    def test_generate_severe_missing_case(self):
        """测试生成严重缺失病历"""
        generator = TestCaseGenerator()
        case = generator.generate_severe_missing_case()

        # 大部分字段为空
        assert case["present_illness"] == ""
        assert case["diagnosis"] == ""

    def test_generate_non_response_case(self):
        """测试生成未执行检查就写诊断病历"""
        generator = TestCaseGenerator()
        case = generator.generate_non_response_case()

        assert case["diagnosis"] == "缺铁性贫血"
        # 辅助检查为空
        assert case["auxiliary_exams"] == ""

    def test_generate_incorrect_treatment_case(self):
        """测试生成治疗方案与诊断不匹配病历"""
        generator = TestCaseGenerator()
        case = generator.generate_incorrect_treatment_case()

        assert case["diagnosis"] == "细菌性肺炎"
        # 包含过敏药物
        assert "青霉素" in case["prescription"]
        assert "过敏" in case["past_history"]

    def test_generate_short_content_case(self):
        """测试生成内容过短病历"""
        generator = TestCaseGenerator()
        case = generator.generate_short_content_case()

        # 所有字段都很短
        assert len(case["main_complaint"]) <= 5
        assert len(case["present_illness"]) <= 5

    def test_generate_all_test_cases(self):
        """测试生成所有测试用例"""
        generator = TestCaseGenerator()
        cases = generator.generate_all_test_cases()

        assert len(cases) >= 8

    def test_save_test_cases(self, tmp_path):
        """测试保存测试用例"""
        generator = TestCaseGenerator(output_dir=str(tmp_path))
        cases = generator.generate_all_test_cases()

        saved = generator.save_test_cases(cases)

        assert len(saved) > 0
        # 检查文件是否存在
        for filepath in saved:
            assert tmp_path.joinpath(filepath.split('/')[-1]).exists()


class TestIssueDetection:
    """问题检测测试"""

    def test_incomplete_case_missing_fields(self):
        """测试缺失字段病历的字段缺失"""
        generator = TestCaseGenerator()
        case = generator.generate_incomplete_case()

        required_fields = [
            "main_complaint", "present_illness", "past_history",
            "physical_exam", "auxiliary_exams", "diagnosis", "prescription"
        ]

        missing_count = 0
        for field in required_fields:
            if field not in case:
                missing_count += 1

        assert missing_count >= 3

    def test_inconsistent_case_has_conflict(self):
        """测试逻辑矛盾病历的冲突"""
        generator = TestCaseGenerator()
        case = generator.generate_inconsistent_case()

        # 有肝功能不全但使用了华法林
        assert "肝功能不全" in case["past_history"]
        assert "华法林" in case["prescription"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
