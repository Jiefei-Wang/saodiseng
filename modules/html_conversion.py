
import re
import html

import asyncio
import aiohttp
from .pdf_coversion import process_pdf_url, async_process_pdf_url




def fetch_url(url):
    """
    同步获取URL内容（调用异步版本）
    """
    return asyncio.run(_fetch_single_url(url))


async def _fetch_single_url(url):
    """
    获取单个URL的异步实现
    """
    async with aiohttp.ClientSession() as session:
        return await async_fetch_url(session, url)


async def async_fetch_url(session, url):
    if url.endswith('.pdf'):
        print(f"Processing PDF URL: {url}")
        # 使用异步PDF处理函数
        return await async_process_pdf_url(url)
    try:
        async with session.get(url, headers={"User-Agent": "saodiseng (saodiseng@gmail.com)"}) as response:
            html_content = await response.text()
            return html_to_markdown(html_content)
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

async def async_get_web_contents(urls): 
    async with aiohttp.ClientSession() as session:
        tasks = [async_fetch_url(session, url) for url in urls]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        return responses


def get_web_contents(urls):
    return asyncio.run(async_get_web_contents(urls))


def html_to_markdown(html_content):
    """
    Convert HTML to clean markdown text, removing images and preserving structure.
    
    Args:
        html_content (str): Raw HTML content
        
    Returns:
        str: Cleaned markdown text
    """
    try:
        from bs4 import BeautifulSoup
        return _html_to_markdown_bs4(html_content)
    except ImportError:
        return _html_to_markdown_regex(html_content)


def _html_to_markdown_bs4(html_content):
    """Convert HTML to markdown using BeautifulSoup (preferred method)."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove unwanted elements
    for element in soup(['script', 'style', 'img', 'figure', 'sup', 'span.mw-editsection']):
        element.decompose()
    
    # Find the main content area (Wikipedia specific)
    content = soup.find('div', {'id': 'mw-content-text'})
    if not content:
        content = soup
    
    markdown_text = ""
    
    # Process elements
    for element in content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol']):
        if element.name.startswith('h'):
            # Headers
            level = int(element.name[1])
            text = element.get_text().strip()
            if text and not any(skip in text for skip in ['编辑', '[编辑]', '坐标']):
                markdown_text += f"{'#' * level} {text}\n\n"
        
        elif element.name == 'p':
            # Paragraphs
            text = element.get_text().strip()
            if text:
                markdown_text += f"{text}\n\n"
        
        elif element.name in ['ul', 'ol']:
            # Lists
            for li in element.find_all('li', recursive=False):
                text = li.get_text().strip()
                if text:
                    markdown_text += f"- {text}\n"
            markdown_text += "\n"
    
    # Clean up extra whitespace
    markdown_text = re.sub(r'\n{3,}', '\n\n', markdown_text)
    return markdown_text.strip()


def _html_to_markdown_regex(html_content):
    """Convert HTML to markdown using regex (fallback method)."""
    # Remove script and style elements
    html_content = re.sub(r'<script.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    html_content = re.sub(r'<style.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove images and figures
    html_content = re.sub(r'<img[^>]*>', '', html_content, flags=re.IGNORECASE)
    html_content = re.sub(r'<figure[^>]*>.*?</figure>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove unwanted elements
    html_content = re.sub(r'<sup[^>]*>.*?</sup>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # Convert headers
    for i in range(1, 7):
        html_content = re.sub(f'<h{i}[^>]*>(.*?)</h{i}>', f'\n{"#" * i} \\1\n\n', html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # Convert paragraphs
    html_content = re.sub(r'<p[^>]*>(.*?)</p>', r'\n\1\n\n', html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # Convert lists
    html_content = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1\n', html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove all remaining HTML tags
    html_content = re.sub(r'<[^>]+>', '', html_content)
    
    # Unescape HTML entities
    html_content = html.unescape(html_content)
    
    # Clean up whitespace
    html_content = re.sub(r'\n{3,}', '\n\n', html_content)
    html_content = re.sub(r'[ \t]+', ' ', html_content)
    html_content = re.sub(r'\n ', '\n', html_content)
    
    return html_content.strip()
