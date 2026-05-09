"""轻量级 Embedding RAG（基于 TF-IDF + Cosine Similarity）

不依赖外部深度学习库，只用 numpy 实现。
预计算知识库 embedding，查询时实时计算相似度。
"""

import os
import json
import math
import re
from typing import List, Dict, Tuple

import numpy as np

_KB_EMBEDDINGS = None
_KB_CHUNKS = None


def _tokenize(text: str) -> List[str]:
    """简单分词：小写 + 非字母数字分割"""
    return re.findall(r'[a-z0-9_]+', text.lower())


def _build_tfidf(docs: List[List[str]]) -> Tuple[np.ndarray, Dict[str, int], Dict[int, str]]:
    """构建 TF-IDF 矩阵
    
    Returns:
        (doc_vectors, term_to_idx, idx_to_term)
    """
    # 构建词表
    term_to_idx = {}
    idx = 0
    for doc in docs:
        for term in set(doc):
            if term not in term_to_idx:
                term_to_idx[term] = idx
                idx += 1
    
    n_docs = len(docs)
    n_terms = len(term_to_idx)
    
    # 计算 DF (document frequency)
    df = np.zeros(n_terms)
    for doc in docs:
        for term in set(doc):
            df[term_to_idx[term]] += 1
    
    # IDF = log(N / DF)
    idf = np.log(n_docs / (df + 1e-10))
    
    # 计算 TF-IDF 向量
    vectors = np.zeros((n_docs, n_terms))
    for i, doc in enumerate(docs):
        term_counts = {}
        for term in doc:
            term_counts[term] = term_counts.get(term, 0) + 1
        for term, count in term_counts.items():
            tf = count / len(doc) if doc else 0
            vectors[i, term_to_idx[term]] = tf * idf[term_to_idx[term]]
    
    # L2 归一化
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    vectors = vectors / (norms + 1e-10)
    
    idx_to_term = {v: k for k, v in term_to_idx.items()}
    return vectors, term_to_idx, idx_to_term


def _load_kb_with_embeddings() -> Tuple[List[Dict], np.ndarray, Dict[str, int]]:
    """加载知识库并预计算 embedding"""
    global _KB_EMBEDDINGS, _KB_CHUNKS
    
    if _KB_EMBEDDINGS is not None and _KB_CHUNKS is not None:
        return _KB_CHUNKS, _KB_EMBEDDINGS, {}
    
    # 加载知识库（复用 lecroy_llm_agent.py 的加载逻辑）
    possible_paths = [
        os.path.join(os.path.dirname(__file__), '..', '..', 'lecroy_script_agent', 'knowledge_base', 'manual_chunks.json'),
        os.path.join(os.path.dirname(__file__), '..', 'lecroy_script_agent', 'knowledge_base', 'manual_chunks.json'),
        'lecroy_script_agent/knowledge_base/manual_chunks.json',
    ]
    
    kb = []
    for p in possible_paths:
        try:
            with open(p, 'r', encoding='utf-8') as f:
                kb = json.load(f)
            break
        except (FileNotFoundError, json.JSONDecodeError):
            continue
    
    if not kb:
        _KB_CHUNKS = []
        _KB_EMBEDDINGS = np.array([])
        return [], np.array([]), {}
    
    # 构建 TF-IDF
    docs = [_tokenize(chunk.get('content', '')) for chunk in kb]
    vectors, term_to_idx, _ = _build_tfidf(docs)
    
    _KB_CHUNKS = kb
    _KB_EMBEDDINGS = vectors
    
    return kb, vectors, term_to_idx


def retrieve_with_embedding(query: str, top_k: int = 3) -> List[Dict]:
    """基于 TF-IDF embedding 检索最相关的 chunk"""
    kb, embeddings, term_to_idx = _load_kb_with_embeddings()
    
    if not kb or embeddings.size == 0:
        return []
    
    # 编码查询
    query_tokens = _tokenize(query)
    query_vec = np.zeros(embeddings.shape[1])
    for term in query_tokens:
        if term in term_to_idx:
            query_vec[term_to_idx[term]] += 1
    
    # L2 归一化
    query_norm = np.linalg.norm(query_vec)
    if query_norm > 0:
        query_vec = query_vec / query_norm
    
    # 计算余弦相似度
    scores = embeddings @ query_vec
    
    # 取 top_k
    top_indices = np.argsort(scores)[-top_k:][::-1]
    return [kb[i] for i in top_indices if scores[i] > 0.01]


def hybrid_retrieve(query: str, top_k: int = 3) -> List[Dict]:
    """混合检索：关键词匹配 + Embedding 语义检索"""
    from backend.agents.lecroy_llm_agent import _retrieve_manual_chunks
    
    # 关键词检索
    keyword_results = _retrieve_manual_chunks(query, top_k=top_k)
    keyword_ids = {id(c) for c in keyword_results}
    
    # Embedding 检索
    emb_results = retrieve_with_embedding(query, top_k=top_k)
    
    # 去重合并（embedding 结果排前面）
    merged = []
    seen = set()
    for chunk in emb_results + keyword_results:
        cid = id(chunk)
        if cid not in seen:
            seen.add(cid)
            merged.append(chunk)
    
    return merged[:top_k]
