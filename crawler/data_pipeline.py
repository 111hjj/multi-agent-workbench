"""
数据管道 - 爬虫数据清洗和向量化
"""
from typing import List, Dict, Any, Optional
import sqlite3
import hashlib
import os
from datetime import datetime


class DataPipeline:
    """数据管道 - 处理爬虫数据"""
    
    def __init__(self, db_path: str = "./data/crawler.db"):
        """初始化数据管道"""
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crawled_pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT,
                content TEXT,
                summary TEXT,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                hash TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crawl_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                crawled_at TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def is_crawled(self, url: str) -> bool:
        """检查URL是否已爬取"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM crawled_pages WHERE url = ?', (url,))
        result = cursor.fetchone()
        
        conn.close()
        return result is not None
    
    def save_page(self, url: str, title: str, content: str, summary: Optional[str] = None):
        """保存爬取的页面"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO crawled_pages 
                (url, title, content, summary, hash, crawled_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (url, title, content, summary, content_hash, datetime.now()))
            
            conn.commit()
            print(f"保存页面: {url}")
        except Exception as e:
            print(f"保存页面失败: {e}")
        finally:
            conn.close()
    
    def add_to_queue(self, urls: List[str]):
        """添加URL到爬取队列"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for url in urls:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO crawl_queue (url, status)
                    VALUES (?, 'pending')
                ''', (url,))
            except Exception as e:
                print(f"添加URL到队列失败 {url}: {e}")
        
        conn.commit()
        conn.close()
    
    def get_pending_urls(self, limit: int = 10) -> List[str]:
        """获取待爬取的URL"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT url FROM crawl_queue 
            WHERE status = 'pending' 
            LIMIT ?
        ''', (limit,))
        
        urls = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return urls
    
    def mark_crawled(self, url: str):
        """标记URL为已爬取"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE crawl_queue 
            SET status = 'completed', crawled_at = ?
            WHERE url = ?
        ''', (datetime.now(), url))
        
        conn.commit()
        conn.close()
    
    async def process_and_index(self, url: str, content: str):
        """处理内容并索引到向量数据库"""
        try:
            from rag.indexer import DocumentIndexer
            
            indexer = DocumentIndexer()
            
            chunks = indexer._chunk_text(content)
            
            await indexer._index_chunks(chunks, url)
            
            self.save_page(url, "", content)
            
        except Exception as e:
            print(f"处理和索引失败: {e}")
