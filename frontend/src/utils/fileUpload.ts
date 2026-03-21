/**
 * 文件上传工具函数测试
 * 为 InputSection.tsx 中的文件上传逻辑提供单元测试
 */

// 支持的文件类型
const SUPPORTED_FILE_TYPES = [
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/pdf',
];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

/**
 * 验证文件类型
 */
export function isValidFileType(fileType: string, fileName: string): boolean {
  // 检查 MIME 类型
  if (SUPPORTED_FILE_TYPES.includes(fileType)) {
    return true;
  }

  // 检查文件扩展名（处理 MIME 类型不准确的情况）
  const ext = fileName.split('.').pop()?.toLowerCase();
  if (ext === 'docx' || ext === 'pdf') {
    return true;
  }

  return false;
}

/**
 * 验证文件大小
 */
export function isValidFileSize(fileSize: number): boolean {
  return fileSize <= MAX_FILE_SIZE;
}

/**
 * 获取文件扩展名
 */
export function getFileExtension(fileName: string): string | null {
  return fileName.split('.').pop()?.toLowerCase() || null;
}

/**
 * 格式化文件大小
 */
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  } else if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  } else {
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  }
}
