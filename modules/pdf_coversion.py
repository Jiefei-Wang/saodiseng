import io
import fitz  # PyMuPDF
from PIL import Image
import easyocr
import numpy as np
import aiohttp
import asyncio

# 全局OCR读取器（避免重复初始化）
_ocr_reader = None

def get_ocr_reader():
    global _ocr_reader
    if _ocr_reader is None:
        # 初始化EasyOCR读取器，支持中文和英文
        _ocr_reader = easyocr.Reader(['ch_sim', 'en'], gpu=True)
    return _ocr_reader

def process_pdf_url(url, size_limit_mb=10):
    """
    下载PDF文件并使用OCR转换为文本（同步接口）
    
    Args:
        url (str): PDF文件的URL
        size_limit_mb (int): 文件大小限制（MB）
        
    Returns:
        str: 提取的文本内容
    """
    # 同步版本直接调用异步版本
    return asyncio.run(async_process_pdf_url(url, size_limit_mb))


async def async_process_pdf_url(url, size_limit_mb=10):
    """
    异步下载PDF文件并使用OCR转换为文本
    
    Args:
        url (str): PDF文件的URL
        size_limit_mb (int): 文件大小限制（MB）
        
    Returns:
        str: 提取的文本内容
    """
    try:
        headers = {"User-Agent": "saodiseng (saodiseng@gmail.com)"}
        
        async with aiohttp.ClientSession() as session:
            # 先发HEAD请求检查文件大小
            print(f"正在检查PDF文件: {url}")
            async with session.head(url, headers=headers, allow_redirects=True) as head_response:
                if head_response.status != 200:
                    print(f"无法访问文件，状态码: {head_response.status}")
                    return ""
                
                # 检查文件大小
                content_length = head_response.headers.get('content-length')
                if content_length:
                    size_mb = int(content_length) / (1024 * 1024)
                    print(f"文件大小: {size_mb:.2f}MB")
                    if size_mb > size_limit_mb:
                        print(f"文件太大 ({size_mb:.2f}MB)，超过限制 ({size_limit_mb}MB)")
                        return ""
                else:
                    print("无法获取文件大小信息")
            
            # 下载PDF文件
            print(f"正在下载PDF: {url}")
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    print(f"下载失败，状态码: {response.status}")
                    return ""
                
                # 读取PDF内容到内存
                pdf_content = await response.read()
                print(f"PDF下载完成，大小: {len(pdf_content) / 1024 / 1024:.2f}MB")
        
        # PDF处理部分仍然是同步的，但在线程池中运行
        return await asyncio.to_thread(_process_pdf_content, pdf_content, url)
        
    except Exception as e:
        print(f"处理PDF时出错 {url}: {e}")
        return ""


def _process_pdf_content(pdf_content, url):
    """
    处理PDF内容（用于在线程池中运行）
    """
    try:
        # 使用PyMuPDF打开PDF
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        text_content = ""
        
        # 限制处理页数（避免处理太大的文件）
        max_pages = 20
        total_pages = min(len(doc), max_pages)
        
        print(f"开始OCR处理，共 {total_pages} 页")
        
        for page_num in range(total_pages):
            page = doc[page_num]
            
            # 首先尝试提取文本（如果PDF包含文本）
            text = page.get_text()
            if isinstance(text, str) and text.strip():
                text_content += f"\n--- 第 {page_num + 1} 页 ---\n"
                text_content += text
                continue
            
            # 如果没有文本，则使用OCR
            print(f"正在OCR第 {page_num + 1} 页...")
            
            # 将PDF页面转换为图像（较低分辨率以提高速度）
            mat = fitz.Matrix(1.5, 1.5)  # 缩放因子，调低以提高速度
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # 转换为PIL图像然后转为numpy数组（EasyOCR需要）
            image = Image.open(io.BytesIO(img_data))
            image_np = np.array(image)
            
            # 使用EasyOCR进行文字识别
            reader = get_ocr_reader()
            results = reader.readtext(image_np, detail=0)
            ocr_text = '\n'.join(str(text) for text in results) if results else ''
            
            if ocr_text.strip():
                text_content += f"\n--- 第 {page_num + 1} 页 (OCR) ---\n"
                text_content += ocr_text
        
        doc.close()
        print(f"PDF处理完成，提取文本长度: {len(text_content)} 字符")
        return text_content.strip()
        
    except Exception as e:
        print(f"处理PDF内容时出错: {e}")
        return ""