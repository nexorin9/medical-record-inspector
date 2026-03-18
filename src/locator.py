"""
缺陷定位模块 - Medical Record Inspector
实现段落级相似度分析，定位病历中与模板差异最大的部分
"""

import re
from typing import List, Dict, Tuple, Optional
import numpy as np
import logging

from src.embedder import get_embedder
from src.similarity import get_similarity_calculator

logger = logging.getLogger(__name__)


class Locator:
    """缺陷定位器 - 识别病历中与模板差异最大的段落"""

    def __init__(self, chunk_size: int = 5, min_chunk_length: int = 50):
        self.chunk_size = chunk_size
        self.min_chunk_length = min_chunk_length

    def split_into_paragraphs(self, text: str) -> List[str]:
        """按段落分割文本"""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        return paragraphs

    def split_into_chunks(self, text: str) -> List[str]:
        """按句子分块"""
        sentences = re.split(r'[。！？]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence)
            if current_length + sentence_length > self.min_chunk_length and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    def calculate_chunk_similarity(self, chunk: str, reference_chunks: List[str]) -> float:
        """计算单个分块与参考分块的相似度"""
        embedder = get_embedder()
        query_embedding = embedder.embed(chunk)
        ref_embeddings = [embedder.embed(rc) for rc in reference_chunks]
        calculator = get_similarity_calculator()
        similarities = calculator.cosine_similarity_batch(query_embedding, ref_embeddings)
        return max(similarities) if similarities else 0.0

    def locate_defects(self, text: str, reference_text: str) -> Dict:
        """定位文本中的缺陷"""
        text_paragraphs = self.split_into_paragraphs(text)
        ref_paragraphs = self.split_into_paragraphs(reference_text)

        paragraph_scores = []
        for i, para in enumerate(text_paragraphs):
            if i < len(ref_paragraphs):
                ref_para = ref_paragraphs[i]
            else:
                ref_para = ' '.join(ref_paragraphs)

            score = self.calculate_chunk_similarity(para, [ref_para])
            paragraph_scores.append({
                'index': i,
                'text': para[:100] + '...' if len(para) > 100 else para,
                'similarity': score,
                'length': len(para)
            })

        paragraph_scores.sort(key=lambda x: x['similarity'])

        defect_threshold = 0.6
        defects = [p for p in paragraph_scores if p['similarity'] < defect_threshold]

        return {
            'total_paragraphs': len(text_paragraphs),
            'paragraph_scores': paragraph_scores,
            'defects': defects,
            'defect_count': len(defects),
            'defect_ratio': len(defects) / len(text_paragraphs) if text_paragraphs else 0
        }

    def calculate_chunk_embedding_similarity(self, text: str, reference_text: str) -> List[Dict]:
        """计算分块级别的嵌入相似度"""
        text_chunks = self.split_into_chunks(text)
        ref_chunks = self.split_into_chunks(reference_text)

        if not text_chunks:
            return []

        embedder = get_embedder()
        ref_embeddings = [embedder.embed(rc) for rc in ref_chunks]

        results = []
        for i, tc in enumerate(text_chunks):
            tc_embedding = embedder.embed(tc)
            calculator = get_similarity_calculator()
            similarities = calculator.cosine_similarity_batch(tc_embedding, ref_embeddings)

            results.append({
                'index': i,
                'text': tc[:100] + '...' if len(tc) > 100 else tc,
                'max_similarity': float(max(similarities)),
                'avg_similarity': float(np.mean(similarities)),
                'min_similarity': float(min(similarities))
            })

        return results

    def generate_defect_map(self, text: str, reference_text: str) -> Dict:
        """生成缺陷热力图"""
        para_analysis = self.locate_defects(text, reference_text)
        chunk_analysis = self.calculate_chunk_embedding_similarity(text, reference_text)

        heat_map = []
        for i, chunk in enumerate(chunk_analysis):
            is_anomaly = chunk['avg_similarity'] < 0.6
            heat_map.append({
                'order': i,
                'text': chunk['text'][:50] + '...' if len(chunk['text']) > 50 else chunk['text'],
                'similarity': chunk['avg_similarity'],
                'anomaly': is_anomaly,
                'color': 'red' if is_anomaly else 'green'
            })

        return {
            'paragraph_level': para_analysis,
            'chunk_level': chunk_analysis,
            'heat_map': heat_map
        }


def create_locator() -> Locator:
    """创建默认缺陷定位器"""
    return Locator(chunk_size=5, min_chunk_length=50)
