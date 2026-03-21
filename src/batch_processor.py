"""
批量处理优化 - Medical Record Inspector
实现批处理优化，包括向量化处理和进度显示
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import logging

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

logger = logging.getLogger(__name__)


class BatchProcessor:
    """批量处理器 - 优化批量处理性能"""

    def __init__(self, max_workers: int = 4, batch_size: int = 10):
        """
        初始化批量处理器

        Args:
            max_workers: 最大工作线程数
            batch_size: 批处理大小
        """
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.results = []
        self.errors = []

    def process_files(self, directory: str, process_func: Callable,
                      file_extensions: List[str] = None) -> Dict[str, Any]:
        """
        批量处理目录下的文件

        Args:
            directory: 目录路径
            process_func: 处理函数
            file_extensions: 文件扩展名过滤

        Returns:
            处理结果字典
        """
        start_time = time.time()

        # 获取文件列表
        dir_path = Path(directory)
        if not dir_path.exists():
            return {'success': False, 'message': f"目录不存在: {directory}"}

        if file_extensions:
            files = []
            for ext in file_extensions:
                files.extend(dir_path.glob(f'*{ext}'))
            files = list(set(files))  # 去重
        else:
            files = list(dir_path.glob('*'))

        # 过滤掉目录
        files = [f for f in files if f.is_file()]

        # 处理文件
        results = []
        errors = []

        # 使用进度条
        if TQDM_AVAILABLE:
            progress_bar = tqdm(total=len(files), desc="处理文件")
        else:
            progress_bar = None

        for file_path in files:
            try:
                result = process_func(str(file_path))
                results.append({
                    'file': str(file_path),
                    'success': True,
                    'result': result
                })
            except Exception as e:
                errors.append({
                    'file': str(file_path),
                    'error': str(e)
                })
                logger.error(f"处理文件失败 {file_path}: {e}")

            if progress_bar:
                progress_bar.update(1)

        if progress_bar:
            progress_bar.close()

        elapsed_time = time.time() - start_time

        return {
            'success': True,
            'total_files': len(files),
            'successful': len(results),
            'failed': len(errors),
            'elapsed_time': elapsed_time,
            'results': results,
            'errors': errors
        }

    def process_texts(self, texts: List[str], process_func: Callable,
                      show_progress: bool = True) -> Dict[str, Any]:
        """
        批量处理文本列表

        Args:
            texts: 文本列表
            process_func: 处理函数
            show_progress: 是否显示进度条

        Returns:
            处理结果字典
        """
        start_time = time.time()

        results = []
        errors = []

        if show_progress and TQDM_AVAILABLE:
            progress_bar = tqdm(total=len(texts), desc="处理文本")
        else:
            progress_bar = None

        for i, text in enumerate(texts):
            try:
                result = process_func(text)
                results.append({
                    'index': i,
                    'success': True,
                    'result': result
                })
            except Exception as e:
                errors.append({
                    'index': i,
                    'error': str(e)
                })
                logger.error(f"处理文本失败 (index={i}): {e}")

            if progress_bar:
                progress_bar.update(1)

        if progress_bar:
            progress_bar.close()

        elapsed_time = time.time() - start_time

        return {
            'success': True,
            'total_texts': len(texts),
            'successful': len(results),
            'failed': len(errors),
            'elapsed_time': elapsed_time,
            'results': results,
            'errors': errors
        }

    def process_with_batching(self, items: List[Any], process_func: Callable,
                               batch_size: int = None,
                               show_progress: bool = True) -> Dict[str, Any]:
        """
        按批处理项目

        Args:
            items: 项目列表
            process_func: 处理函数（接受单个项目或项目列表）
            batch_size: 批大小
            show_progress: 是否显示进度条

        Returns:
            处理结果字典
        """
        batch_size = batch_size or self.batch_size

        start_time = time.time()
        results = []
        errors = []

        batches = []
        for i in range(0, len(items), batch_size):
            batches.append(items[i:i + batch_size])

        if show_progress and TQDM_AVAILABLE:
            progress_bar = tqdm(total=len(batches), desc="处理批次")
        else:
            progress_bar = None

        for batch in batches:
            try:
                if len(batch) == 1:
                    result = process_func(batch[0])
                    results.append({
                        'success': True,
                        'result': result
                    })
                else:
                    # 如果处理函数支持批量处理
                    result = process_func(batch)
                    # 展平结果
                    if isinstance(result, list):
                        for i, r in enumerate(result):
                            results.append({
                                'success': True,
                                'result': r
                            })
                    else:
                        results.append({
                            'success': True,
                            'result': result
                        })
            except Exception as e:
                errors.append({
                    'error': str(e),
                    'items_count': len(batch)
                })
                logger.error(f"处理批次失败: {e}")

            if progress_bar:
                progress_bar.update(1)

        if progress_bar:
            progress_bar.close()

        elapsed_time = time.time() - start_time

        return {
            'success': True,
            'total_items': len(items),
            'batches_processed': len(batches),
            'successful': len(results),
            'failed': len(errors),
            'elapsed_time': elapsed_time,
            'results': results,
            'errors': errors
        }

    def process_parallel(self, items: List[Any], process_func: Callable,
                         max_workers: int = None) -> Dict[str, Any]:
        """
        并行处理项目（使用线程池）

        Args:
            items: 项目列表
            process_func: 处理函数
            max_workers: 最大工作线程数

        Returns:
            处理结果字典
        """
        max_workers = max_workers or self.max_workers

        start_time = time.time()
        results = []
        errors = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_item = {
                executor.submit(process_func, item): item
                for item in items
            }

            # 收集结果
            for future in as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    result = future.result()
                    results.append({
                        'success': True,
                        'result': result
                    })
                except Exception as e:
                    errors.append({
                        'error': str(e)
                    })
                    logger.error(f"处理项目失败: {e}")

        elapsed_time = time.time() - start_time

        return {
            'success': True,
            'total_items': len(items),
            'batches_processed': len(items),  # 每个项作为一个批次
            'successful': len(results),
            'failed': len(errors),
            'elapsed_time': elapsed_time,
            'results': results,
            'errors': errors
        }

    def get_statistics(self, results: List[Dict]) -> Dict[str, Any]:
        """
        获取处理结果统计信息

        Args:
            results: 处理结果列表

        Returns:
            统计信息字典
        """
        successful = [r for r in results if r.get('success')]
        failed = [r for r in results if not r.get('success')]

        stats = {
            'total': len(results),
            'successful': len(successful),
            'failed': len(failed),
            'success_rate': len(successful) / max(len(results), 1)
        }

        # 如果有耗时信息
        if results and 'elapsed_time' in results[0]:
            times = [r.get('elapsed_time', 0) for r in successful]
            if times:
                stats['avg_time'] = sum(times) / len(times)
                stats['min_time'] = min(times)
                stats['max_time'] = max(times)

        return stats


def create_batch_processor(max_workers: int = 4,
                           batch_size: int = 10) -> BatchProcessor:
    """创建批量处理器"""
    return BatchProcessor(max_workers=max_workers, batch_size=batch_size)


if __name__ == "__main__":
    # 简单测试
    logging.basicConfig(level=logging.INFO)

    print("=== Batch Processor 测试 ===\n")

    # 测试文件处理
    print("1. 测试文件处理:")
    processor = create_batch_processor()

    # 创建测试目录和文件
    test_dir = "data/test_batch"
    os.makedirs(test_dir, exist_ok=True)

    # 创建测试文件
    test_files = []
    for i in range(5):
        file_path = os.path.join(test_dir, f"test_{i}.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"这是测试文件 {i}")
        test_files.append(file_path)

    # 定义处理函数
    def process_file(file_path: str) -> Dict:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {'filename': os.path.basename(file_path), 'length': len(content)}

    # 处理文件
    result = processor.process_files(test_dir, process_file)
    print(f"   总文件数: {result['total_files']}")
    print(f"   成功: {result['successful']}")
    print(f"   失败: {result['failed']}")
    print(f"   耗时: {result['elapsed_time']:.3f} 秒")

    # 清理测试目录
    import shutil
    shutil.rmtree(test_dir)

    # 测试文本处理
    print("\n2. 测试文本处理:")
    texts = [
        "这是第一个测试文本",
        "这是第二个测试文本",
        "这是第三个测试文本",
    ]

    def process_text(text: str) -> Dict:
        return {'length': len(text), 'words': len(text.split())}

    result = processor.process_texts(texts, process_text)
    print(f"   总文本数: {result['total_texts']}")
    print(f"   成功: {result['successful']}")
    print(f"   耗时: {result['elapsed_time']:.3f} 秒")

    # 测试批处理
    print("\n3. 测试批处理:")
    items = list(range(20))

    def process_item(item) -> int:
        return item * 2

    result = processor.process_with_batching(items, process_item, batch_size=5)
    print(f"   总项数: {result['total_items']}")
    print(f"   批次数: {result['batches_processed']}")
    print(f"   成功: {result['successful']}")

    # 测试并行处理
    print("\n4. 测试并行处理:")
    items = list(range(10))

    def slow_process(item) -> int:
        time.sleep(0.01)  # 模拟耗时操作
        return item * 3

    result = processor.process_parallel(items, slow_process, max_workers=4)
    print(f"   总项数: {result['total_items']}")
    print(f"   耗时: {result['elapsed_time']:.3f} 秒")

    # 测试统计信息
    print("\n5. 测试统计信息:")
    stats = processor.get_statistics(result['results'])
    print(f"   成功率: {stats['success_rate']:.2%}")
    print(f"   平均耗时: {stats.get('avg_time', 0):.4f} 秒")
