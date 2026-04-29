"""
混合检索器 - 支持向量检索 + BM25检索 + 重排序
"""
from typing import List, Dict, Any, Optional
import os
import pickle


class HybridRetriever:
    """混合检索器 - 向量检索 + BM25检索 + 重排序"""
    
    def __init__(self, top_k: int = 5):
        """
        初始化混合检索器
        
        Args:
            top_k: 返回结果数量
        """
        self.top_k = top_k
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.bm25_index = None
        self.bm25_docs = []
        self.reranker = None
        self.use_reranker = False
        self.reranker_initialized = False
    
    def _init_reranker(self):
        """初始化重排序模型（延迟加载）"""
        if self.reranker_initialized:
            return
        
        self.reranker_initialized = True
        
        try:
            import os
            os.environ['TRANSFORMERS_NO_ADVISORY_WARNINGS'] = '1'
            from sentence_transformers import CrossEncoder
            import torch
            
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            self.reranker = CrossEncoder('BAAI/bge-reranker-base', device=device)
            self.use_reranker = True
            print("重排序模型加载成功: BAAI/bge-reranker-base")
        except Exception as e:
            print(f"重排序模型加载失败，将跳过重排序步骤: {str(e)[:100]}")
            self.reranker = None
            self.use_reranker = False
    
    async def retrieve(self, query: str) -> List[Dict[str, Any]]:
        """
        执行混合检索
        
        Args:
            query: 查询文本
            
        Returns:
            检索结果列表
        """
        try:
            vector_results = await self._vector_search(query)
            bm25_results = await self._bm25_search(query)
            
            merged = self._merge_results(vector_results, bm25_results)
            
            if self.use_reranker and merged and self.reranker:
                try:
                    reranked = self._rerank(query, merged)
                    return reranked[:self.top_k]
                except Exception as e:
                    print(f"重排序失败，使用未重排序结果: {e}")
            
            return merged[:self.top_k]
            
        except Exception as e:
            print(f"检索失败: {e}")
            return []
    
    async def _vector_search(self, query: str) -> List[Dict[str, Any]]:
        """向量检索"""
        try:
            from qdrant_client import QdrantClient
            
            client = QdrantClient(url=self.qdrant_url)
            
            try:
                import requests
                ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
                model_name = os.getenv("OLLAMA_MODEL", "deepseek-r1:8b")
                
                response = requests.post(
                    f"{ollama_url}/api/embeddings",
                    json={
                        "model": model_name,
                        "prompt": query
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    query_vector = response.json().get("embedding", [])
                else:
                    print(f"Ollama嵌入失败: {response.status_code}")
                    return []
                    
            except Exception as e:
                print(f"使用Ollama生成嵌入失败: {str(e)[:50]}")
                return []
            
            if not query_vector:
                return []
            
            try:
                results = client.search(
                    collection_name="documents",
                    query_vector=query_vector,
                    limit=self.top_k * 2
                )
                
                formatted_results = []
                for result in results:
                    formatted_results.append({
                        "id": str(result.id),
                        "score": result.score,
                        "text": result.payload.get("text", ""),
                        "metadata": result.payload.get("metadata", {})
                    })
                
                return formatted_results
            except Exception as e:
                print(f"Qdrant检索失败: {e}")
                return []
            
        except Exception as e:
            print(f"向量检索失败: {e}")
            return []
    
    async def _bm25_search(self, query: str) -> List[Dict[str, Any]]:
        """BM25检索"""
        if not self.bm25_index:
            return []
        
        try:
            import jieba
            
            query_tokens = list(jieba.cut(query))
            scores = self.bm25_index.get_scores(query_tokens)
            
            results = []
            for i, score in enumerate(scores):
                if score > 0:
                    doc = self.bm25_docs[i]
                    results.append({
                        "id": f"bm25_{i}",
                        "score": float(score),
                        "text": doc.get("text", ""),
                        "metadata": doc.get("metadata", {})
                    })
            
            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:self.top_k * 2]
            
        except Exception as e:
            print(f"BM25检索失败: {e}")
            return []
    
    def _merge_results(self, vector_results: List[Dict[str, Any]], bm25_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合并向量检索和BM25检索结果"""
        merged = {}
        
        for result in vector_results:
            key = result["text"]
            if key not in merged:
                merged[key] = {**result, "combined_score": result["score"] * 0.6}
            else:
                merged[key]["combined_score"] += result["score"] * 0.6
        
        for result in bm25_results:
            key = result["text"]
            if key not in merged:
                merged[key] = {**result, "combined_score": result["score"] * 0.4}
            else:
                merged[key]["combined_score"] += result["score"] * 0.4
        
        merged_list = list(merged.values())
        merged_list.sort(key=lambda x: x["combined_score"], reverse=True)
        
        return merged_list
    
    def _rerank(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """使用重排序模型重新排序"""
        if not self.reranker:
            return results
        
        try:
            pairs = [[query, result["text"]] for result in results]
            scores = self.reranker.predict(pairs)
            
            for i, result in enumerate(results):
                result["rerank_score"] = float(scores[i])
            
            results.sort(key=lambda x: x["rerank_score"], reverse=True)
            return results
            
        except Exception as e:
            print(f"重排序失败: {e}")
            return results
    
    def load_bm25_index(self, file_path: str) -> bool:
        """加载BM25索引"""
        try:
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
                self.bm25_index = data['index']
                self.bm25_docs = data['docs']
            print(f"BM25索引已从 {file_path} 加载")
            return True
        except Exception as e:
            print(f"加载BM25索引失败: {e}")
            return False
    
    def build_bm25_index(self, documents: List[Dict[str, Any]], save_path: Optional[str] = None) -> bool:
        """构建BM25索引"""
        try:
            from rank_bm25 import BM25Okapi
            import jieba
            
            tokenized_docs = [list(jieba.cut(doc.get("text", ""))) for doc in documents]
            self.bm25_index = BM25Okapi(tokenized_docs)
            self.bm25_docs = documents
            
            if save_path:
                with open(save_path, 'wb') as f:
                    pickle.dump({
                        'index': self.bm25_index,
                        'docs': self.bm25_docs
                    }, f)
                print(f"BM25索引已保存到 {save_path}")
            
            return True
        except Exception as e:
            print(f"构建BM25索引失败: {e}")
            return False