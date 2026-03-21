"""
测试用例 - Medical Record Inspector
模块：extractor.py - 文本提取模块
"""

import pytest
import os
import tempfile
from pathlib import Path

# 添加 src 目录到路径
sys_path_added = False
for p in os.sys.path:
    if 'medical-record-inspector' in p:
        sys_path_added = True
        break

if not sys_path_added:
    os.sys.path.insert(0, str(Path(__file__).parent.parent))


class TestExtractTextFromTxt:
    """测试 TXT 文件文本提取"""

    def test_extract_text_from_txt_utf8(self):
        """测试 UTF-8 编码的 TXT 文件提取"""
        from src.extractor import extract_text_from_txt

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("测试病历文本\n患者姓名：张三\n诊断：肺炎")
            temp_path = f.name

        try:
            text = extract_text_from_txt(temp_path)
            assert "测试病历文本" in text
            assert "张三" in text
            assert "肺炎" in text
        finally:
            os.unlink(temp_path)

    def test_extract_text_from_txt_gbk(self):
        """测试 GBK 编码的 TXT 文件提取"""
        from src.extractor import extract_text_from_txt

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='gbk') as f:
            f.write("测试病历文本\n患者姓名：李四\n诊断：感冒")
            temp_path = f.name

        try:
            text = extract_text_from_txt(temp_path)
            assert "测试病历文本" in text
            assert "李四" in text
        finally:
            os.unlink(temp_path)

    def test_extract_text_from_txt_file_not_found(self):
        """测试不存在的文件处理"""
        from src.extractor import extract_text_from_txt

        with pytest.raises(FileNotFoundError):
            extract_text_from_txt("non_existent_file.txt")


class TestCleanText:
    """测试文本清洗功能"""

    def test_clean_text_consecutive_blank_lines(self):
        """测试去除连续空行"""
        from src.extractor import clean_text

        text = "第一段\n\n\n\n第二段\n\n\n第三段"
        cleaned = clean_text(text)
        # 应该减少连续空行
        assert "\n\n\n" not in cleaned

    def test_clean_text_extra_whitespace(self):
        """测试去除多余空白"""
        from src.extractor import clean_text

        text = "测试    文本    清洗"
        cleaned = clean_text(text)
        assert "测试 文本 清洗" in cleaned

    def test_clean_text_strip_lines(self):
        """测试去除行首行尾空白"""
        from src.extractor import clean_text

        text = "  line 1  \n  line 2  \n  line 3  "
        cleaned = clean_text(text)
        lines = cleaned.split('\n')
        for line in lines:
            assert line == line.strip() or line == ""

    def test_clean_text_remove_non_printable(self):
        """测试去除不可打印字符"""
        from src.extractor import clean_text

        text = "正常文本\x00\x01\x02不可见字符"
        cleaned = clean_text(text)
        assert "正常文本" in cleaned
        assert "\x00" not in cleaned
        assert "\x01" not in cleaned
        assert "\x02" not in cleaned


class TestStandardizeChinese:
    """测试中文标准化功能"""

    def test_fullwidth_to_halfwidth_parenthesis(self):
        """测试全角括号转半角"""
        from src.extractor import standardize_chinese

        text = "测试（括号）转换"
        standardized = standardize_chinese(text)
        assert "(" in standardized
        assert ")" in standardized

    def test_fullwidth_to_halfwidth_bracket(self):
        """测试全角方括号转半角"""
        from src.extractor import standardize_chinese

        text = "测试【方括号】转换"
        standardized = standardize_chinese(text)
        assert "[" in standardized
        assert "]" in standardized

    def test_fullwidth_to_halfwidth_colon(self):
        """测试全角冒号分号转半角"""
        from src.extractor import standardize_chinese

        text = "测试：冒号；分号"
        standardized = standardize_chinese(text)
        assert ":" in standardized
        assert ";" in standardized

    def test_english_punctuation_preserved(self):
        """测试英文标点保持不变"""
        from src.extractor import standardize_chinese

        text = "Test: text, with (parentheses) and [brackets]."
        standardized = standardize_chinese(text)
        assert text == standardized


class TestExtractTextFromPDF:
    """测试 PDF 文本提取（mock 测试）"""

    def test_extract_text_from_pdf_not_implemented(self):
        """测试 PDF 提取函数存在"""
        from src.extractor import extract_text_from_pdf

        # 由于没有真实 PDF 文件，这里只测试函数存在
        assert callable(extract_text_from_pdf)


class TestExtractTextFromDocx:
    """测试 Word 文本提取（mock 测试）"""

    def test_extract_text_from_docx_not_implemented(self):
        """测试 Word 提取函数存在"""
        from src.extractor import extract_text_from_docx

        # 由于没有真实 Word 文件，这里只测试函数存在
        assert callable(extract_text_from_docx)


class TestExtractText:
    """测试自动文件类型检测和提取"""

    def test_extract_text_txt_extension(self):
        """测试 .txt 文件自动识别"""
        from src.extractor import extract_text

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("测试文本")
            temp_path = f.name

        try:
            text = extract_text(temp_path)
            assert "测试文本" in text
        finally:
            os.unlink(temp_path)

    def test_extract_text_unknown_extension(self):
        """测试未知扩展名文件处理"""
        from src.extractor import extract_text

        with tempfile.NamedTemporaryFile(mode='w', suffix='.unknown', delete=False, encoding='utf-8') as f:
            f.write("测试未知扩展名")
            temp_path = f.name

        try:
            # 未知扩展名会尝试按 txt 处理
            text = extract_text(temp_path)
            assert "测试未知扩展名" in text
        finally:
            os.unlink(temp_path)


class TestExtractTextFromDirectory:
    """测试目录批量提取"""

    def test_extract_text_from_directory(self):
        """测试从目录批量提取文本"""
        from src.extractor import extract_text_from_directory

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试 TXT 文件
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("测试病历文本\n患者：王五", encoding='utf-8')

            # 创建一个非支持文件
            other_file = Path(tmpdir) / "other.doc"
            other_file.write_text("其他文件内容")

            results = extract_text_from_directory(tmpdir)

            assert "test.txt" in results
            assert "其他文件内容" not in results  # .doc 不支持
            assert "王五" in results["test.txt"]

    def test_extract_text_from_directory_empty(self):
        """测试空目录处理"""
        from src.extractor import extract_text_from_directory

        with tempfile.TemporaryDirectory() as tmpdir:
            results = extract_text_from_directory(tmpdir)
            assert results == {}


class TestSaveTextToFile:
    """测试文本保存功能"""

    def test_save_text_to_file(self):
        """测试文本保存到文件"""
        from src.extractor import save_text_to_file

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output" / "test.txt"
            text = "测试保存的文本\n包含多行内容"

            save_text_to_file(text, str(output_path))

            assert output_path.exists()
            saved_content = output_path.read_text(encoding='utf-8')
            assert "测试保存的文本" in saved_content
            assert "包含多行内容" in saved_content

    def test_save_text_creates_directories(self):
        """测试自动创建目录"""
        from src.extractor import save_text_to_file

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "nested" / "deep" / "file.txt"
            text = "测试嵌套目录保存"

            save_text_to_file(text, str(output_path))

            assert output_path.exists()
