import os
import pandas as pd
from typing import List, Dict, Any, Optional, Literal
import hashlib
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema import Document
from langchain_community.vectorstores import FAISS, Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_ollama import OllamaLLM
import langchain_ollama
from transformers import pipeline

RAGType = Literal["no_rag", "simple_vector", "contextual_compression", "hybrid"]


def initialize_rag_architecture(rag_type: RAGType, model_name: str) -> Optional[Any]:
    """Initialize the specified RAG architecture."""
    if rag_type == "no_rag":
        return None
    
    # Create directories if they don't exist
    ensure_directories()
    
    # Get data hash to check if we need to reprocess
    data_hash = get_data_hash()
    rag_dir = os.path.join(RAG_DATA_DIR, rag_type)
    hash_file = os.path.join(rag_dir, "data_hash.txt")
    
    needs_processing = True
    if os.path.exists(hash_file):
        with open(hash_file, 'r') as f:
            stored_hash = f.read().strip()
            if stored_hash == data_hash:
                needs_processing = False
    
    # Initialize embeddings
    embeddings = OllamaEmbeddings(model=model_name)
    
    if rag_type == "simple_vector":
        vector_db_path = os.path.join(rag_dir, "faiss_index")
        
        if not needs_processing and os.path.exists(vector_db_path):
            print("Loading existing FAISS index...")
            return FAISS.load_local(vector_db_path, embeddings)
        
        print("Creating new FAISS index...")
        documents = load_and_process_csv()
        vector_db = FAISS.from_documents(documents, embeddings)
        vector_db.save_local(vector_db_path)
        
        # Save hash
        with open(hash_file, 'w') as f:
            f.write(data_hash)
            
        return vector_db
    
    elif rag_type == "contextual_compression":
        vector_db_path = os.path.join(rag_dir, "chroma_db")
        
        if not needs_processing and os.path.exists(vector_db_path):
            print("Loading existing Chroma database...")
            vector_db = Chroma(persist_directory=vector_db_path, embedding_function=embeddings)
            llm = OllamaLLM(model=model_name)
            compressor = LLMChainExtractor.from_llm(llm)
            retriever = vector_db.as_retriever()
            compression_retriever = ContextualCompressionRetriever(
                base_retriever=retriever,
                base_compressor=compressor
            )
            return compression_retriever
            
        print("Creating new Chroma database...")
        documents = load_and_process_csv()
        vector_db = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory=vector_db_path
        )
        
        # Save hash
        with open(hash_file, 'w') as f:
            f.write(data_hash)
            
        # Create compression retriever
        llm = OllamaLLM(model=model_name)
        compressor = LLMChainExtractor.from_llm(llm)
        retriever = vector_db.as_retriever()
        compression_retriever = ContextualCompressionRetriever(
            base_retriever=retriever,
            base_compressor=compressor
        )
        return compression_retriever
        
    elif rag_type == "hybrid":
        vector_db_path = os.path.join(rag_dir, "hybrid_db")
        
        if not needs_processing and os.path.exists(vector_db_path):
            print("Loading existing hybrid database...")
            # For hybrid, we use HuggingFace embeddings for better performance
            hf_embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-mpnet-base-v2"
            )
            vector_db = FAISS.load_local(vector_db_path, hf_embeddings)
            return vector_db.as_retriever(search_kwargs={"k": 5})
            
        print("Creating new hybrid database...")
        # For hybrid, we use HuggingFace embeddings for better performance
        hf_embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2"
        )
        documents = load_and_process_csv()
        vector_db = FAISS.from_documents(documents, hf_embeddings)
        vector_db.save_local(vector_db_path)
        
        # Save hash
        with open(hash_file, 'w') as f:
            f.write(data_hash)
            
        return vector_db.as_retriever(search_kwargs={"k": 5})
    
    return None
