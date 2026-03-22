"""
Standard Case Generator for Medical Record Inspector.

Generates high-quality standard case templates for quality assessment.
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime


class StandardCaseGenerator:
    """标准病历生成器"""

    def __init__(self, output_dir: str = "data/standard_cases"):
        self.output_dir = output_dir
        self.cases = []

    def generate_outpatient_template(
        self,
        department: str,
        case_type: str = "门诊"
    ) -> Dict:
        """生成门诊标准病历"""
        templates = {
            "内科": {
                "template_id": f"OUT-内科-{datetime.now().strftime('%Y%m%d')}-001",
                "department": department,
                "case_type": case_type,
                "main_complaint": "反复咳嗽、咳痰3年，加重1周",
                "present_illness": "患者3年前受凉后出现咳嗽、咳脓痰，量中等，无咯血、胸痛。此后每于冬季受凉后复发，经抗感染治疗可缓解。1周前再次受凉后咳嗽、咳痰加重，痰量增多，为白色泡沫痰，无发热、胸痛。自服感冒药后症状稍缓解。",
                "past_history": "高血压病史5年，规律服药控制良好。否认糖尿病、冠心病史。无手术外伤史。无药物过敏史。",
                "physical_exam": "T 36.5℃，P 80次/分，R 18次/分，BP 130/85mmHg。神志清楚，发育正常。双肺呼吸音清，未闻及干湿性啰音。心率80次/分，律齐。腹软，无压痛。神经系统检查无异常。",
                "auxiliary_exams": "血常规：WBC 6.5×10^9/L，N 65%，L 30%。胸片：双肺纹理稍增粗，未见明显异常。",
                "diagnosis": "慢性支气管炎急性发作期",
                "prescription": "1. 阿莫西林胶囊 0.5g 口服 tid × 7天\n2. 氨溴索口服液 10ml 口服 bid × 7天\n3. 多喝温水，注意休息",
                "notes": "门诊随访，若症状加重及时复诊"
            },
            "外科": {
                "template_id": f"OUT-外科-{datetime.now().strftime('%Y%m%d')}-001",
                "department": department,
                "case_type": case_type,
                "main_complaint": "右上腹隐痛1月，加重3天",
                "present_illness": "患者1月前无明显诱因出现右上腹隐痛，呈持续性，未予诊治。3天前疼痛加重，呈胀痛，伴恶心、无呕吐、发热。遂来我院就诊。",
                "past_history": "否认高血压、糖尿病史。否认肝炎、结核史。有胆囊切除术史（2020年）。无药物过敏史。",
                "physical_exam": "T 37.2℃，P 78次/分，R 16次/分，BP 120/75mmHg。皮肤黏膜无黄染。右上腹轻压痛，墨菲氏征阴性。肝脾未触及。移动性浊音阴性。",
                "auxiliary_exams": "腹部B超：胆囊窝区少量液体暗区，肝功能正常。血常规：WBC 8.2×10^9/L。",
                "diagnosis": "胆囊炎术后改变，右侧季肋部软组织痛",
                "prescription": "1. 匹维溴铵片 50mg 口服 tid × 7天\n2. 避免油腻饮食，低脂饮食\n3. 规律进食，忌暴饮暴食",
                "notes": "建议1月后复诊，必要时完善MRCP检查"
            },
            "妇科": {
                "template_id": f"OUT-妇科-{datetime.now().strftime('%Y%m%d')}-001",
                "department": department,
                "case_type": case_type,
                "main_complaint": "经量增多伴经期延长3月",
                "present_illness": "患者3月前无明显诱因出现月经经量增多，较前增加约1倍，伴经期延长至6-7天，无痛经、无接触性出血。未诊治。近1月出现乏力、头晕。",
                "past_history": "平素月经规律，LMP 2024-01-15。G2P1，剖宫产1次。否认高血压、糖尿病史。无药物过敏史。",
                "physical_exam": "T 36.8℃，P 82次/分，R 18次/分，BP 115/70mmHg。贫血貌。心肺未见异常。妇科检查：外阴产型，阴道畅，黏膜光滑，宫颈光滑，子宫前位，大小正常，质中，无压痛，双附件未触及异常。",
                "auxiliary_exams": "血常规：Hb 95g/L，WBC 6.8×10^9/L。盆腔B超：子宫前位，大小5.0×4.5×3.5cm，内膜厚0.8cm，双卵巢未见明显异常。",
                "diagnosis": "异常子宫出血，缺铁性贫血",
                "prescription": "1. 硫酸亚铁片 0.3g 口服 tid × 3月\n2. 氨甲环酸片 0.5g 口服 bid × 5天（经期使用）\n3. 加强营养，多吃富含铁食物",
                "notes": "建议3月后复诊，必要时行宫腔镜检查"
            }
        }
        return templates.get(department, templates["内科"])

    def generate_inpatient_template(
        self,
        department: str,
        case_type: str = "住院"
    ) -> Dict:
        """生成住院标准病历"""
        templates = {
            "内科": {
                "template_id": f"IN-内科-{datetime.now().strftime('%Y%m%d')}-001",
                "department": department,
                "case_type": case_type,
                "main_complaint": "胸闷、气促2月，加重1周",
                "present_illness": "患者2月前出现胸闷、气促，活动后加重，休息后可缓解。1周前上述症状加重，不能平卧，伴有夜间阵发性呼吸困难。口服利尿剂效果不佳。",
                "past_history": "高血压病史10年，最高180/110mmHg。冠心病史5年，曾行冠脉造影提示前降支狭窄70%。否认糖尿病史。",
                "physical_exam": "T 36.6℃，P 92次/分，R 22次/分，BP 150/90mmHg。半卧位。双肺底可闻及湿性啰音。心界向左下扩大，心率92次/分，律齐，心尖区可闻及3/6级收缩期杂音。",
                "auxiliary_exams": "BNP 450pg/mL。心电图：左室高电压，ST-T改变。心脏彩超：LVEF 45%，左心室扩大。",
                "diagnosis": "慢性心力衰竭急性加重，高血压病3级，冠心病",
                "prescription": "1. 呋塞米 20mg 静脉注射 qd\n2. 螺内酯 20mg 口服 qd\n3. 美托洛尔缓释片 47.5mg 口服 qd\n4. 阿司匹林 100mg 口服 qd\n5. 限盐限水，记录出入量",
                "notes": "患者病情较重，建议住院治疗，心内科护理常规"
            },
            "外科": {
                "template_id": f"IN-外科-{datetime.now().strftime('%Y%m%d')}-001",
                "department": department,
                "case_type": case_type,
                "main_complaint": "腹痛伴呕吐2天",
                "present_illness": "患者2天前出现阵发性腹部绞痛，伴呕吐胃内容物数次，无血性呕吐物。停止排气排便。既往有腹部手术史。",
                "past_history": "2020年行阑尾切除术。否认高血压、糖尿病史。无药物过敏史。",
                "physical_exam": "T 37.8℃，P 98次/分，R 20次/分，BP 130/80mmHg。腹部膨隆，可见肠型，肠鸣音活跃。腹部压痛，无明显反跳痛。",
                "auxiliary_exams": "立位腹平片：可见液气平面，肠管扩张。血常规：WBC 12.5×10^9/L。",
                "diagnosis": "粘连性肠梗阻",
                "prescription": "1. 禁食水，胃肠减压\n2. 抗感染治疗：头孢曲松 1g 静脉滴注 bid\n3. 补液：生理盐水 1000ml 静脉滴注 qd\n4. 密切观察病情变化",
                "notes": "患者有肠梗阻表现，需警惕肠绞窄可能，必要时行急诊手术"
            },
            "妇科": {
                "template_id": f"IN-妇科-{datetime.now().strftime('%Y%m%d')}-001",
                "department": department,
                "case_type": case_type,
                "main_complaint": "停经38周，腹痛2小时",
                "present_illness": "患者停经38周，今晨出现规律下腹坠痛，约5-6分钟一次，每次持续30秒，伴阴道少量流液。急诊入院。",
                "past_history": "平素月经规律。G2P1，2023年剖宫产1次。否认高血压、糖尿病史。",
                "physical_exam": "T 36.7℃，P 80次/分，R 18次/分，BP 120/75mmHg。宫高32cm，腹围95cm，LOA。宫缩规律，2分钟一次，每次40秒。宫口开大2cm。",
                "auxiliary_exams": "胎儿心音140-150次/分。骨盆测量正常。B超：胎儿双顶径9.2cm，股骨长7.0cm，羊水指数12cm。",
                "diagnosis": "G2P1 妊娠38周 LOA 待产，胎膜早破",
                "prescription": "1. 左侧卧位，吸氧\n2. 勤听胎音，观察宫缩及破水情况\n3. 备皮，留置尿管\n4. 急查血常规、凝血功能、肝肾功能\n5. 做好剖宫产准备",
                "notes": "患者已临产，破水已1小时，产程进展顺利，建议待产，必要时行剖宫产术"
            }
        }
        return templates.get(department, templates["内科"])

    def generate_emergency_template(
        self,
        department: str,
        case_type: str = "急诊"
    ) -> Dict:
        """生成急诊标准病历"""
        templates = {
            "内科": {
                "template_id": f"EM-内科-{datetime.now().strftime('%Y%m%d')}-001",
                "department": department,
                "case_type": case_type,
                "main_complaint": "胸痛1小时",
                "present_illness": "患者1小时前无明显诱因出现心前区压榨性疼痛，疼痛放射至左肩部，伴大汗、恶心、呕吐，无人陪伴来我院急诊。",
                "past_history": "高血压病史8年。冠心病史3年，未规律治疗。否认糖尿病史。",
                "physical_exam": "T 36.5℃，P 110次/分，R 24次/分，BP 170/100mmHg。急性病容，大汗淋漓。双肺呼吸音清。心率110次/分，律齐，心音低钝。",
                "auxiliary_exams": "心电图：V1-V4导联ST段抬高0.2-0.3mV。肌钙蛋白I 0.5ng/mL。",
                "diagnosis": "急性前壁ST段抬高型心肌梗死",
                "prescription": "1. 立即嚼服阿司匹林肠溶片 300mg\n2. 波立维 300mg 口服\n3. 低分子肝素 4000U 皮下注射\n4. 吗啡 3mg 静脉推注（必要时）\n5. 急诊PCI准备",
                "notes": "患者为急性心梗，需要立即行再灌注治疗，建议急诊PCI或溶栓"
            },
            "外科": {
                "template_id": f"EM-外科-{datetime.now().strftime('%Y%m%d')}-001",
                "department": department,
                "case_type": case_type,
                "main_complaint": "右下腹痛6小时",
                "present_illness": "患者6小时前出现右下腹疼痛，呈持续性，伴恶心、呕吐2次，无发热。疼痛逐渐加重。",
                "past_history": "否认高血压、糖尿病史。无手术史。无药物过敏史。",
                "physical_exam": "T 38.2℃，P 96次/分，R 20次/分，BP 125/78mmHg。右下腹麦氏点压痛、反跳痛明显，肌卫（+）。",
                "auxiliary_exams": "血常规：WBC 14.5×10^9/L，N 85%。尿常规：未见明显异常。右下腹B超：阑尾增粗，直径1.2cm。",
                "diagnosis": "急性化脓性阑尾炎",
                "prescription": "1. 禁食水\n2. 抗感染：头孢曲松 1g 静脉滴注 bid\n3. 术前准备：备皮、皮试\n4. 急诊阑尾切除术",
                "notes": "患者诊断明确，建议急诊手术，术前禁食6小时"
            },
            "妇科": {
                "template_id": f"EM-妇科-{datetime.now().strftime('%Y%m%d')}-001",
                "department": department,
                "case_type": case_type,
                "main_complaint": "停经7周，右下腹痛伴阴道流血2小时",
                "present_illness": "患者停经7周，2小时前出现右下腹剧烈疼痛，伴阴道少量流血，色暗红，头晕、心悸。遂来急诊。",
                "past_history": "G2P0，无妊娠并发症史。否认高血压、糖尿病史。",
                "physical_exam": "T 36.5℃，P 102次/分，R 22次/分，BP 90/60mmHg。贫血貌。下腹压痛、反跳痛。妇科检查：宫颈举痛（+），后穹隆饱满。",
                "auxiliary_exams": "尿妊娠试验（+）。血HCG 3000mIU/mL。阴道B超：右附件区不均质包块，直径3.5cm，盆腔大量积液。",
                "diagnosis": "右侧输卵管妊娠破裂",
                "prescription": "1. 立即建立静脉通道，补液\n2. 配血备血\n3. 急查血常规、凝血功能、生化\n4. 急诊剖腹探查准备",
                "notes": "患者为输卵管妊娠破裂，失血性休克表现，需急诊手术"
            }
        }
        return templates.get(department, templates["内科"])

    def generate_all_standard_cases(self) -> List[Dict]:
        """生成所有标准病历"""
        cases = []

        # 门诊病历
        for dept in ["内科", "外科", "妇科"]:
            cases.append(self.generate_outpatient_template(dept))

        # 住院病历
        for dept in ["内科", "外科", "妇科"]:
            cases.append(self.generate_inpatient_template(dept))

        # 急诊病历
        for dept in ["内科", "外科", "妇科"]:
            cases.append(self.generate_emergency_template(dept))

        return cases

    def save_cases(self, cases: List[Dict] = None) -> List[str]:
        """保存标准病历到文件"""
        if cases is None:
            cases = self.generate_all_standard_cases()

        saved_files = []
        os.makedirs(self.output_dir, exist_ok=True)

        for case in cases:
            filename = f"{case['template_id']}.json"
            filepath = os.path.join(self.output_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(case, f, ensure_ascii=False, indent=2)
            saved_files.append(filepath)

        return saved_files

    def load_cases(self) -> List[Dict]:
        """从文件加载标准病历"""
        cases = []
        os.makedirs(self.output_dir, exist_ok=True)

        for filename in os.listdir(self.output_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.output_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    cases.append(json.load(f))

        return cases


def generate_standard_case() -> Dict:
    """
    生成单个标准病历的便捷函数。

    Returns:
        dict: 标准病历字典
    """
    generator = StandardCaseGenerator()
    cases = generator.generate_all_standard_cases()
    return cases[0]  # 返回第一个病历


def get_all_standard_cases() -> List[Dict]:
    """
    获取所有标准病历。

    Returns:
        list: 标准病历列表
    """
    generator = StandardCaseGenerator()
    return generator.generate_all_standard_cases()


if __name__ == "__main__":
    # 生成并保存所有标准病历
    generator = StandardCaseGenerator()
    cases = generator.generate_all_standard_cases()

    print(f"生成 {len(cases)} 个标准病历")

    # 保存到文件
    saved = generator.save_cases(cases)
    print(f"保存文件: {saved}")

    # 显示第一个病历的摘要
    print(f"\n示例病历（第一个）:")
    print(f"模板ID: {cases[0]['template_id']}")
    print(f"科室: {cases[0]['department']}")
    print(f"类型: {cases[0]['case_type']}")
    print(f"主诉: {cases[0]['main_complaint']}")
