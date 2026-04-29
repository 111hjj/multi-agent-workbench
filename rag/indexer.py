"""
文档索引器 - 解析、分块、向量化文档
"""
from typing import List, Dict, Any, Optional
import os
import hashlib
import re


class DocumentIndexer:
    """文档索引器 - 解析、分块、向量化文档"""
    
    def __init__(self):
        """初始化文档索引器"""
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.chunk_size = 500
        self.chunk_overlap = 50
    
    async def index_document(self, file_path: str) -> Dict[str, Any]:
        """
        索引单个文档
        
        Args:
            file_path: 文档路径
            
        Returns:
            索引结果
        """
        try:
            print(f"DocumentIndexer: 开始索引文档 - {file_path}")
            
            text = await self._parse_document(file_path)
            
            chunks = self._chunk_text(text)
            
            await self._index_chunks(chunks, file_path)
            
            return {
                "status": "success",
                "file_path": file_path,
                "chunks_count": len(chunks)
            }
            
        except Exception as e:
            print(f"DocumentIndexer: 索引失败: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _parse_document(self, file_path: str) -> str:
        """解析文档"""
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == ".pdf":
            return await self._parse_pdf(file_path)
        elif ext in [".doc", ".docx"]:
            return await self._parse_word(file_path)
        elif ext == ".md":
            return await self._parse_markdown(file_path)
        elif ext == ".txt":
            return await self._parse_text(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {ext}")
    
    async def _parse_pdf(self, file_path: str) -> str:
        """解析PDF文档"""
        try:
            import fitz
            
            doc = fitz.open(file_path)
            text = ""
            
            for page in doc:
                text += page.get_text()
            
            doc.close()
            return text
            
        except Exception as e:
            print(f"PDF解析失败: {e}")
            return ""
    
    async def _parse_word(self, file_path: str) -> str:
        """解析Word文档"""
        try:
            from docx import Document
            
            doc = Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
            
        except Exception as e:
            print(f"Word解析失败: {e}")
            return ""
    
    async def _parse_markdown(self, file_path: str) -> str:
        """解析Markdown文档"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Markdown解析失败: {e}")
            return ""
    
    async def _parse_text(self, file_path: str) -> str:
        """解析纯文本文档"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"文本解析失败: {e}")
            return ""
    
    def _chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """混合分块：保留代码块、表格、公式"""
        chunks = []
        
        code_blocks = re.findall(r'```[\s\S]*?```', text)
        formulas = re.findall(r'\$\$[\s\S]*?\$\$|\\\[[\s\S]*?\\\]', text)
        tables = re.findall(r'(?:^\|.*\|(?:\r?\n|$))+', text, re.MULTILINE)
        
        special_blocks = []
        for block in code_blocks:
            special_blocks.append({"type": "code", "text": block})
        for formula in formulas:
            special_blocks.append({"type": "formula", "text": formula})
        for table in tables:
            special_blocks.append({"type": "table", "text": table})
        
        for block in special_blocks:
            chunks.append({
                "text": block["text"],
                "metadata": {"type": block["type"]}
            })
        
        clean_text = text
        for block in code_blocks + formulas + tables:
            clean_text = clean_text.replace(block, "")
        
        paragraphs = clean_text.split("\n\n")
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            if len(para) <= self.chunk_size:
                chunks.append({
                    "text": para,
                    "metadata": {"type": "text"}
                })
            else:
                for i in range(0, len(para), self.chunk_size - self.chunk_overlap):
                    chunk_text = para[i:i + self.chunk_size]
                    chunks.append({
                        "text": chunk_text,
                        "metadata": {"type": "text"}
                    })
        
        return chunks
    
    async def _index_chunks(self, chunks: List[Dict[str, Any]], file_path: str):
        """索引分块到向量数据库"""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams, PointStruct
            
            client = QdrantClient(url=self.qdrant_url)
            
            try:
                from sentence_transformers import SentenceTransformer
                encoder = SentenceTransformer('all-MiniLM-L6-v2')
                use_embedding = True
                print("嵌入模型加载成功: all-MiniLM-L6-v2")
            except Exception as e:
                print(f"嵌入模型加载失败，将使用简单索引: {e}")
                use_embedding = False
            
            try:
                if use_embedding:
                    client.create_collection(
                        collection_name="documents",
                        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                    )
                else:
                    client.create_collection(
                        collection_name="documents",
                        vectors_config=VectorParams(size=768, distance=Distance.COSINE)
                    )
            except:
                pass
            
            points = []
            for i, chunk in enumerate(chunks):
                if use_embedding:
                    vector = encoder.encode(chunk["text"]).tolist()
                else:
                    vector = [0.0] * 768
                
                point = PointStruct(
                    id=hashlib.sha256(f"{file_path}_{i}".encode()).hexdigest()[:16],
                    vector=vector,
                    payload={
                        "text": chunk["text"],
                        "metadata": chunk["metadata"],
                        "source": file_path
                    }
                )
                points.append(point)
            
            client.upsert(
                collection_name="documents",
                points=points
            )
            
            print(f"已索引 {len(points)} 个分块到向量数据库")
            
        except Exception as e:
            print(f"索引失败: {e}")
