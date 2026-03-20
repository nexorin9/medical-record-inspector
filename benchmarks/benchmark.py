"""
性能基准测试 - Medical Record Inspector
评估系统在不同规模下的表现
"""

import os
import sys
import time
import logging
from typing import List, Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.inspector import MedicalRecordInspector, create_inspector
from src.embedder import get_embedder
from src.similarity import get_similarity_calculator
from src.batch_processor import BatchProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_test_record() -> str:
    """获取测试病历文本"""
    return """患者基本信息
姓名：张三
性别：男
年龄：45岁
住院号：202410001

主诉
反复咳嗽、咳痰3年，加重伴发热3天。

现病史
患者3年前无明显诱因开始出现咳嗽、咳痰，多为白色泡沫痰，冬季加重。
3天前受凉后症状加重，咳嗽加剧，咳黄色脓痰，体温最高达38.5℃，
伴有胸闷、气促。近期未系统诊疗。

既往史
- 高血压病史5年，规律服药控制良好
- 2型糖尿病病史3年，口服降糖药
- 无手术史、外伤史
- 无药物过敏史

个人史
- 吸烟史：20年，每日10支，已戒烟1年
- 饮酒史：偶有饮酒
- 职业：公司职员
- 饮食习惯：偏咸

家族史
- 父亲：高血压病史
- 母亲：2型糖尿病
- 无家族遗传病

体格检查
T：38.2℃  P：88次/分  R：22次/分  BP：135/85mmHg
双肺呼吸音粗，可闻及散在干湿啰音。

辅助检查
胸部CT：双肺纹理增粗，右下肺斑片状阴影。
血常规：WBC 12.5×10^9/L，N 85%。

初步诊断
1. 社区获得性肺炎
2. 高血压病
3. 2型糖尿病

诊疗经过
- 入院诊断：同初步诊断
- 治疗方案：头孢曲松2.0g ivgtt bid，氨溴索30mg tid
- 治疗效果：体温降至正常，症状缓解

出院诊断
1. 社区获得性肺炎 已治愈
2. 高血压病 控制良好
3. 2型糖尿病 控制良好

出院医嘱
1. 继续服用抗生素7天
2. 定期复查胸片
3. 控制血压、血糖
4. 戒烟限酒，规律作息
"""


class BenchmarkRunner:
    """基准测试运行器"""

    def __init__(self):
        self.results: Dict[str, Any] = {}
        self.inspector: MedicalRecordInspector = None

    def setup(self):
        """初始化测试环境"""
        logger.info("初始化测试环境...")
        self.inspector = create_inspector()
        # 预加载模型（避免冷启动影响结果）
        _ = get_embedder()
        logger.info("测试环境初始化完成")

    def benchmark_single_detection(self, record: str) -> float:
        """测试单病历检测耗时"""
        start = time.time()
        result = self.inspector.analyze(record)
        elapsed = time.time() - start
        return elapsed

    def benchmark_batch_detection(self, records: List[str]) -> float:
        """测试批量检测耗时"""
        start = time.time()
        results = self.inspector.analyze_batch(records)
        elapsed = time.time() - start
        return elapsed

    def benchmark_memory_usage(self, record: str, iterations: int = 10) -> Dict[str, float]:
        """测试内存占用"""
        import tracemalloc
        tracemalloc.start()

        for _ in range(iterations):
            _ = self.inspector.analyze(record)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        return {
            "current_mb": current / 1024 / 1024,
            "peak_mb": peak / 1024 / 1024
        }

    def run_all_benchmarks(self):
        """运行所有基准测试"""
        logger.info("开始运行基准测试...")

        # 测试数据
        test_record = get_test_record()
        test_records = [test_record] * 5

        # 1. 单病历检测耗时
        logger.info("测试 1: 单病历检测耗时")
        times = []
        for i in range(5):
            elapsed = self.benchmark_single_detection(test_record)
            times.append(elapsed)
            logger.info(f"  第 {i+1} 次: {elapsed:.3f}s")
        self.results["single_detection_avg"] = sum(times) / len(times)
        self.results["single_detection_min"] = min(times)
        self.results["single_detection_max"] = max(times)
        logger.info(f"  平均耗时: {self.results['single_detection_avg']:.3f}s")

        # 2. 批量处理吞吐量
        logger.info("测试 2: 批量处理吞吐量")
        elapsed = self.benchmark_batch_detection(test_records)
        throughput = len(test_records) / elapsed
        self.results["batch_detection_time"] = elapsed
        self.results["throughput_records_per_sec"] = throughput
        logger.info(f"  5 个病历耗时: {elapsed:.3f}s")
        logger.info(f"  吞吐量: {throughput:.2f} 记录/秒")

        # 3. 内存占用
        logger.info("测试 3: 内存占用")
        memory = self.benchmark_memory_usage(test_record)
        self.results["memory_current_mb"] = memory["current_mb"]
        self.results["memory_peak_mb"] = memory["peak_mb"]
        logger.info(f"  当前内存: {memory['current_mb']:.2f} MB")
        logger.info(f"  峰值内存: {memory['peak_mb']:.2f} MB")

        logger.info("基准测试完成")

    def generate_report(self, output_path: str = "benchmarks/RESULTS.md"):
        """生成性能报告"""
        report = """# 性能基准测试报告

## 测试环境

- Python 版本: {python_version}
- 模型: {model_name}

## 测试结果

### 单病历检测耗时

| 指标 | 值 |
|------|------|
| 平均耗时 | {avg_time:.3f} 秒 |
| 最小耗时 | {min_time:.3f} 秒 |
| 最大耗时 | {max_time:.3f} 秒 |

### 批量处理吞吐量

| 指标 | 值 |
|------|------|
| 批量大小 | 5 记录 |
| 总耗时 | {batch_time:.3f} 秒 |
| 吞吐量 | {throughput:.2f} 记录/秒 |

### 内存占用

| 指标 | 值 |
|------|------|
| 当前内存 | {current_mem:.2f} MB |
| 峰值内存 | {peak_mem:.2f} MB |

## 结论

""".format(
            python_version=sys.version.split()[0],
            model_name=get_embedder().model_name,
            avg_time=self.results.get("single_detection_avg", 0),
            min_time=self.results.get("single_detection_min", 0),
            max_time=self.results.get("single_detection_max", 0),
            batch_time=self.results.get("batch_detection_time", 0),
            throughput=self.results.get("throughput_records_per_sec", 0),
            current_mem=self.results.get("memory_current_mb", 0),
            peak_mem=self.results.get("memory_peak_mb", 0),
        )

        # 添加结论
        avg_time = self.results.get("single_detection_avg", 0)
        if avg_time < 5:
            report += "- **结论**: 系统性能优秀，单病历检测耗时在 5 秒以内。\n"
        elif avg_time < 15:
            report += "- **结论**: 系统性能良好，单病历检测耗时在 15 秒以内。\n"
        else:
            report += "- **结论**: 系统性能一般，建议优化模型加载或使用更轻量的模型。\n"

        # 保存报告
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"报告已保存到: {output_path}")

        return report


def main():
    """主函数"""
    print("=" * 60)
    print("Medical Record Inspector - 性能基准测试")
    print("=" * 60)
    print()

    runner = BenchmarkRunner()
    runner.setup()
    runner.run_all_benchmarks()
    report = runner.generate_report()

    print()
    print("=" * 60)
    print("测试完成！详细报告已生成到 benchmarks/RESULTS.md")
    print("=" * 60)


if __name__ == '__main__':
    main()
