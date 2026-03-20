"""Test case generators for Medical Record Inspector."""

import json
from datetime import datetime
from typing import Dict, List
import os


class TestCaseGenerator:
    """测试用例生成器"""

    def __init__(self, output_dir: str = "data/test_cases"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_incomplete_case(self) -> Dict:
        """生成缺少字段的病历"""
        return {
            "patient_id": "T001",
            "visit_id": "TV001",
            "department": "内科",
            "case_type": "门诊",
            "main_complaint": "咳嗽",
            "present_illness": "咳嗽几天",
            # 缺少字段：past_history, physical_exam, auxiliary_exams
            "diagnosis": "感冒",
            "prescription": "多喝水"
        }

    def generate_inconsistent_case(self) -> Dict:
        """生成逻辑矛盾的病历"""
        return {
            "patient_id": "T002",
            "visit_id": "TV002",
            "department": "外科",
            "case_type": "门诊",
            "main_complaint": "右下腹痛6小时",
            "present_illness": "患者6小时前出现右下腹疼痛，为钝痛，无恶心呕吐。疼痛轻度，可忍受。",
            "past_history": "有严重肝功能不全病史",
            "physical_exam": "右下腹压痛明显，反跳痛（+）",
            "auxiliary_exams": "血常规：WBC 8.0×10^9/L，中性粒细胞 60%",
            "diagnosis": "急性化脓性阑尾炎",
            "prescription": "1. 华法林 5mg 口服 qd\n2. 阿司匹林 100mg 口服 qd\n3. 布洛芬 400mg 口服 prn"
        }

    def generate_delayed_case(self) -> Dict:
        """生成处理延迟的病历"""
        return {
            "patient_id": "T003",
            "visit_id": "TV003",
            "department": "内科",
            "case_type": "急诊",
            "main_complaint": "胸痛2小时",
            "present_illness": "患者2小时前出现心前区压榨性疼痛，疼痛放射至左肩，伴大汗。自行服用硝酸甘油后症状稍缓解。",
            "past_history": "高血压病史10年",
            "physical_exam": "T 36.5℃, P 80次/分, R 18次/分, BP 140/90mmHg。心肺未见明显异常。",
            # 缺少必要的辅助检查或检查时间在诊断之后
            "diagnosis": "急性心肌梗死",
            "prescription": "1. 阿司匹林 300mg 口服\n2. 比索洛尔 5mg 口服 qd"
        }

    def generate_nonstandard_case(self) -> Dict:
        """生成格式不规范的病历"""
        return {
            "patient_id": "T004",
            "visit_id": "TV004",
            "department": "妇科",
            "case_type": "门诊",
            "main_complaint": "肚子疼",
            "present_illness": "就是肚子疼，疼了几天了。",
            "past_history": "就是以前也疼过",
            "physical_exam": "看看",
            "auxiliary_exams": "做个检查",
            "diagnosis": "肚子疼原因待查",
            "prescription": "吃点止疼药吧"
        }

    def generate_severe_missing_case(self) -> Dict:
        """生成严重缺失的病历（用于严重测试）"""
        return {
            "patient_id": "T005",
            "visit_id": "TV005",
            "department": "外科",
            "case_type": "住院",
            "main_complaint": "腹痛",
            "present_illness": "",
            "past_history": "",
            "physical_exam": "",
            "auxiliary_exams": "",
            "diagnosis": "",
            "prescription": ""
        }

    def generate_non_response_case(self) -> Dict:
        """生成未执行检查就写诊断的病历"""
        return {
            "patient_id": "T006",
            "visit_id": "TV006",
            "department": "内科",
            "case_type": "门诊",
            "main_complaint": "乏力、头晕1月",
            "present_illness": "患者1月前无明显诱因出现乏力、头晕，无发热、咳嗽。",
            "past_history": "否认高血压、糖尿病史",
            "physical_exam": "T 36.5℃, P 78次/分。面色苍白。",
            "auxiliary_exams": "",  # 缺少必要的检查
            "diagnosis": "缺铁性贫血",  # 未通过检查确认就诊断
            "prescription": "1. 硫酸亚铁片 0.3g 口服 tid\n2. 维生素C 0.1g 口服 tid"
        }

    def generate_incorrect_treatment_case(self) -> Dict:
        """生成治疗方案与诊断不匹配的病历"""
        return {
            "patient_id": "T007",
            "visit_id": "TV007",
            "department": "内科",
            "case_type": "门诊",
            "main_complaint": "咳嗽、咳痰3天",
            "present_illness": "患者3天前受凉后出现咳嗽、咳白痰，无发热。",
            "past_history": "有青霉素过敏史",
            "physical_exam": "双肺呼吸音清",
            "auxiliary_exams": "血常规：WBC 6.5×10^9/L",
            "diagnosis": "细菌性肺炎",
            "prescription": "1. 青霉素钠 800万单位 静脉滴注 bid"  # 违反禁忌症
        }

    def generate_short_content_case(self) -> Dict:
        """生成内容过短的病历"""
        return {
            "patient_id": "T008",
            "visit_id": "TV008",
            "department": "外科",
            "case_type": "门诊",
            "main_complaint": "疼",
            "present_illness": "疼",
            "past_history": "无",
            "physical_exam": "正常",
            "auxiliary_exams": "无",
            "diagnosis": "痛",
            "prescription": "吃药"
        }

    def generate_all_test_cases(self) -> List[Dict]:
        """生成所有类型的测试用例"""
        return [
            {"name": "incomplete_case", "case": self.generate_incomplete_case()},
            {"name": "inconsistent_case", "case": self.generate_inconsistent_case()},
            {"name": "delayed_case", "case": self.generate_delayed_case()},
            {"name": "nonstandard_case", "case": self.generate_nonstandard_case()},
            {"name": "severe_missing_case", "case": self.generate_severe_missing_case()},
            {"name": "non_response_case", "case": self.generate_non_response_case()},
            {"name": "incorrect_treatment_case", "case": self.generate_incorrect_treatment_case()},
            {"name": "short_content_case", "case": self.generate_short_content_case()},
        ]

    def save_test_cases(self, cases: List[Dict] = None) -> List[str]:
        """保存测试用例到文件"""
        if cases is None:
            cases = self.generate_all_test_cases()

        saved_files = []
        os.makedirs(self.output_dir, exist_ok=True)

        for item in cases:
            name = item.get("name", "unknown")
            case_data = item.get("case", {})
            filename = f"{name}.json"
            filepath = os.path.join(self.output_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(case_data, f, ensure_ascii=False, indent=2)
            saved_files.append(filepath)

        return saved_files

    def load_test_cases(self) -> List[Dict]:
        """从文件加载测试用例"""
        cases = []
        os.makedirs(self.output_dir, exist_ok=True)

        for filename in os.listdir(self.output_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.output_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    case_data = json.load(f)
                    case_data["__filename__"] = filename
                    cases.append(case_data)

        return cases


def generate_all_test_cases() -> List[Dict]:
    """生成所有测试用例的便捷函数"""
    generator = TestCaseGenerator()
    return generator.generate_all_test_cases()


if __name__ == "__main__":
    generator = TestCaseGenerator()
    cases = generator.generate_all_test_cases()

    print(f"生成 {len(cases)} 个测试用例")

    # 保存到文件
    saved = generator.save_test_cases(cases)
    print(f"保存文件: {saved}")

    # 显示第2个测试用例
    print(f"\n示例测试用例（逻辑矛盾）:")
    print(f"主诉：{cases[1]['case']['main_complaint']}")
    print(f"诊断：{cases[1]['case']['diagnosis']}")
    print(f"治疗：{cases[1]['case']['prescription']}")
