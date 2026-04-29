"""
网页爬虫 - 支持静态和动态网页抓取
"""
from typing import List, Dict, Any, Optional
import time
import random
import os
from crawler.data_pipeline import DataPipeline


class WebCrawler:
    """网页爬虫 - 支持静态和动态网页抓取"""
    
    def __init__(self):
        """初始化爬虫"""
        self.pipeline = DataPipeline()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        ]
    
    async def crawl(self, url: str, use_selenium: bool = False) -> Dict[str, Any]:
        """
        爬取单个网页
        
        Args:
            url: 网页URL
            use_selenium: 是否使用Selenium（动态网页）
            
        Returns:
            爬取结果
        """
        try:
            if self.pipeline.is_crawled(url):
                print(f"URL已爬取，跳过: {url}")
                return {"status": "skipped", "url": url}
            
            print(f"开始爬取: {url}")
            
            if use_selenium:
                content = await self._crawl_dynamic(url)
            else:
                content = await self._crawl_static(url)
            
            await self.pipeline.process_and_index(url, content)
            
            self.pipeline.mark_crawled(url)
            
            return {
                "status": "success",
                "url": url,
                "content_length": len(content),
                "content": content[:5000]
            }
            
        except Exception as e:
            print(f"爬取失败 {url}: {e}")
            return {
                "status": "failed",
                "url": url,
                "error": str(e)
            }
    
    async def crawl_batch(self, urls: List[str], use_selenium: bool = False) -> List[Dict[str, Any]]:
        """
        批量爬取网页
        
        Args:
            urls: URL列表
            use_selenium: 是否使用Selenium
            
        Returns:
            爬取结果列表
        """
        results = []
        
        for url in urls:
            result = await self.crawl(url, use_selenium)
            results.append(result)
            
            time.sleep(random.uniform(1, 3))
        
        return results
    
    async def _crawl_static(self, url: str) -> str:
        """静态爬取"""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            }
            
            time.sleep(random.uniform(0.5, 1.5))
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            text = soup.get_text(separator='\n', strip=True)
            
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            content = '\n'.join(lines)
            
            return content
            
        except Exception as e:
            print(f"静态爬取失败: {e}")
            raise
    
    async def _crawl_dynamic(self, url: str) -> str:
        """动态爬取（使用Selenium）"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument(f'user-agent={random.choice(self.user_agents)}')
            
            driver = webdriver.Chrome(options=options)
            
            try:
                driver.get(url)
                
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                time.sleep(2)
                
                text = driver.find_element(By.TAG_NAME, "body").text
                
                return text
                
            finally:
                driver.quit()
                
        except Exception as e:
            print(f"动态爬取失败: {e}")
            raise
    
    def add_urls_to_queue(self, urls: List[str]):
        """添加URL到爬取队列"""
        self.pipeline.add_to_queue(urls)
    
    def get_pending_urls(self, limit: int = 10) -> List[str]:
        """获取待爬取的URL"""
        return self.pipeline.get_pending_urls(limit)
