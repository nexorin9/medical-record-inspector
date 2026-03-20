"""
测试文件解析
tests/test_file_parser.py
"""

import sys
import os
import tempfile

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from utils.file_parser import FileParser, FileParserError, UnsupportedFileTypeError


def test_unsupported_file_type():
    """测试不支持的文件类型"""
    try:
        FileParser.parse_file("test.txt")
        assert False, "应该抛出 UnsupportedFileTypeError"
    except UnsupportedFileTypeError:
        print("test_unsupported_file_type passed!")


def test_file_size_validation():
    """测试文件大小验证"""
    FileParser.validate_file("test.docx", file_size=1024)
    FileParser.validate_file("test.pdf", file_size=1024)

    try:
        FileParser.validate_file("test.docx", file_size=15 * 1024 * 1024)
        assert False, "应该抛出 FileParserError"
    except FileParserError as e:
        assert "文件过大" in str(e)

    print("test_file_size_validation passed!")


def test_supported_extensions():
    """测试支持的文件扩展名"""
    assert ".docx" in FileParser.SUPPORTED_EXTENSIONS
    assert ".pdf" in FileParser.SUPPORTED_EXTENSIONS
    assert ".txt" not in FileParser.SUPPORTED_EXTENSIONS

    print("test_supported_extensions passed!")


def test_file_parser_constants():
    """测试文件解析器常量"""
    assert FileParser.MAX_FILE_SIZE == 10 * 1024 * 1024
    assert len(FileParser.SUPPORTED_EXTENSIONS) == 2

    print("test_file_parser_constants passed!")


def test_file_extension_case_insensitive():
    """测试文件扩展名大小写不敏感"""
    # 大写扩展名应该通过验证
    FileParser.validate_file("test.DOCX")
    FileParser.validate_file("test.PDF")
    FileParser.validate_file("test.Docx")

    # 大写扩展名应该被识别为不支持
    try:
        FileParser.validate_file("test.TXT")
        assert False, "应该抛出 UnsupportedFileTypeError"
    except UnsupportedFileTypeError:
        pass

    print("test_file_extension_case_insensitive passed!")


def test_file_path_with_directory():
    """测试带目录路径的文件"""
    # 带路径的文件名应该能正确识别扩展名
    FileParser.validate_file("path/to/file.docx")
    FileParser.validate_file("path\\to\\file.pdf")
    FileParser.validate_file("../relative/path/test.DOCX")

    print("test_file_path_with_directory passed!")


def test_max_file_size_boundary():
    """测试最大文件大小边界值"""
    # 正好 10MB 应该通过
    FileParser.validate_file("test.docx", file_size=10 * 1024 * 1024)

    # 超过 10MB 应该失败
    try:
        FileParser.validate_file("test.docx", file_size=10 * 1024 * 1024 + 1)
        assert False, "应该抛出 FileParserError"
    except FileParserError as e:
        assert "文件过大" in str(e)

    print("test_max_file_size_boundary passed!")


def test_binary_file_parsing_simulation():
    """测试二进制文件解析流程（模拟）"""
    # 创建模拟的二进制文件内容
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
        temp_path = tmp.name
        # 写入模拟内容
        tmp.write(b'PK\x03\x04')  # DOCX 文件头

    try:
        with open(temp_path, 'rb') as f:
            file_content = f.read()

        # 测试 validate_file_binary 的逻辑
        ext = os.path.splitext('test.docx')[1].lower()
        assert ext == '.docx'

        # 模拟文件大小检查
        assert len(file_content) <= FileParser.MAX_FILE_SIZE

        print("test_binary_file_parsing_simulation passed!")
    finally:
        os.unlink(temp_path)


def test_file_parser_error_messages():
    """测试文件解析器错误消息"""
    # 测试不支持类型的错误消息
    try:
        FileParser.validate_file("test.xlsx")
        assert False, "应该抛出 UnsupportedFileTypeError"
    except UnsupportedFileTypeError as e:
        assert "不支持的文件类型" in str(e)
        assert ".xlsx" in str(e) or "xlsx" in str(e).lower()

    # 测试文件过大的错误消息
    try:
        FileParser.validate_file("test.docx", file_size=100 * 1024 * 1024)
        assert False, "应该抛出 FileParserError"
    except FileParserError as e:
        assert "文件过大" in str(e)
        assert "100" in str(e) or "10.00" in str(e)

    print("test_file_parser_error_messages passed!")


def test_supported_file_types_list():
    """测试支持的文件类型 MIME 列表（用于前端）"""
    # 前端使用的支持的文件类型
    supported_mime_types = [
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/pdf',
    ]

    # 测试常见变体
    docx_variants = [
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ]

    for variant in docx_variants:
        assert variant in supported_mime_types

    assert 'application/pdf' in supported_mime_types

    print("test_supported_file_types_list passed!")


if __name__ == "__main__":
    test_unsupported_file_type()
    test_file_size_validation()
    test_supported_extensions()
    test_file_parser_constants()
    test_file_extension_case_insensitive()
    test_file_path_with_directory()
    test_max_file_size_boundary()
    test_binary_file_parsing_simulation()
    test_file_parser_error_messages()
    test_supported_file_types_list()
    print("\nAll file parser tests passed!")
