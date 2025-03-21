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
from transformers import pipeline
from .for_rag import initialize_rag_architecture

# Define available RAG types
RAGType = Literal["no_rag", "simple_vector", "contextual_compression", "hybrid"]

# Base directories for storing processed data
RAG_DATA_DIR = os.path.join(os.path.dirname(__file__), "../data/processed_rag_data")
CSV_FILE_PATH = os.path.join(os.path.dirname(__file__), "../data/PSMA data.csv")

def ensure_directories():
    """Ensure all necessary directories exist."""
    os.makedirs(RAG_DATA_DIR, exist_ok=True)
    for rag_type in ["simple_vector", "contextual_compression", "hybrid"]:
        os.makedirs(os.path.join(RAG_DATA_DIR, rag_type), exist_ok=True)

def get_data_hash() -> str:
    """Generate a hash of the CSV file content to detect changes."""
    if not os.path.exists(CSV_FILE_PATH):
        return "no_file"
    
    with open(CSV_FILE_PATH, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    return file_hash

def load_and_process_csv() -> List[Document]:
    """Load and process CSV file into Document objects."""
    df = pd.read_csv(CSV_FILE_PATH)
    documents = []
    
    # Convert each row to a document
    for _, row in df.iterrows():
        # Combine all fields into a single text string
        content = " ".join([f"{col}: {str(val)}" for col, val in row.items() if pd.notna(val)])
        metadata = {"source": "PSMA_data.csv"}
        documents.append(Document(page_content=content, metadata=metadata))
    
    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    split_docs = text_splitter.split_documents(documents)
    return split_docs

def get_llm_response_batched(    user_input: str, 
    system_prompt: str,model_name ,rag_type)-> str:


    




def get_ollama_response_with_rag(
    user_input: str, 
    system_prompt: str, 
    model_name: str = "/workspaces/practical_radio_ai/data/Meta-Llama-3-8B", 
    rag_type: RAGType = "no_rag"
) -> str:
    """
    Get a response from Ollama with optional RAG.
    
    Args:
        user_input: The user's query
        system_prompt: System prompt for Ollama
        model_name: Name of the Ollama model to use
        rag_type: Type of RAG architecture to use
        
    Returns:
        String response from Ollama
    """
    # Initialize Ollama

    print(f"asking system_prompt {system_prompt}") 

    print(f"asking ollama {user_input}") 
    ollama_llm = OllamaLLM(model=model_name, request_timeout=600)
    
    # Direct LLM usage without RAG
    if rag_type == "no_rag":
        print("Loading model from local directory...")
        model_pipeline = pipeline("text-generation", model=model_name)
        
        try:
            print("Generating response...")
            response = model_pipeline(user_input, max_length=100)
            print("Response generated successfully.")
            return response[0]['generated_text']
        except Exception as e:
            print(f"Model inference failed: {e}")
            return "Error: Model inference failed."
    
    # Initialize RAG architecture
    rag_component = initialize_rag_architecture(rag_type, model_name)
    
    if rag_type == "simple_vector":
        retriever = rag_component.as_retriever()
        
        # Create RAG chain
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt + "\n\nContext: {context}"),
            ("human", "{input}")
        ])
        
        chain = (
            {"context": retriever, "input": RunnablePassthrough()}
            | prompt
            | ollama_llm
            | StrOutputParser()
        )
        print("Invoking Ollama chain with extended timeout...")
        try:
            print("Invoking Ollama chain...")
            response = chain.invoke({"input": user_input})
            print("Chain completed successfully.")
            return response
        except Exception as e:
            print(f"Chain invocation failed: {e}")
            return "Error: LLM timed out or encountered an issue."
    
    elif rag_type == "contextual_compression":
        # rag_component is already a retriever
        
        # Create RAG chain
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt + "\n\nContext: {context}"),
            ("human", "{input}")
        ])
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        chain = (
            {"context": rag_component | format_docs, "input": RunnablePassthrough()}
            | prompt
            | ollama_llm
            | StrOutputParser()
        )
        print("Invoking Ollama chain with extended timeout...")
        try:
            print("Invoking Ollama chain...")
            response = chain.invoke({"input": user_input})
            print("Chain completed successfully.")
            return response
        except Exception as e:
            print(f"Chain invocation failed: {e}")
            return "Error: LLM timed out or encountered an issue."
    
    elif rag_type == "hybrid":
        # Create document chain
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt + "\n\nContext: {context}"),
            ("human", "{input}")
        ])
        
        document_chain = create_stuff_documents_chain(ollama_llm, prompt)
        
        # Create retrieval chain
        retrieval_chain = create_retrieval_chain(rag_component, document_chain)
        
        print("Invoking Ollama chain with extended timeout...")
        try:
            print("Invoking Ollama chain...")
            response = retrieval_chain.invoke({"input": user_input})
            print("Chain completed successfully.")
            return response["answer"]
        except Exception as e:
            print(f"Chain invocation failed: {e}")
            return "Error: LLM timed out or encountered an issue."
    
    # Fallback to direct LLM
    print("Invoking Ollama chain with extended timeout...")
    try:
        print("ddddirect Invoking Ollama chain...")
        response = ollama_llm.invoke(user_input)
        print("Chain completed successfully.")
        return response
    except Exception as e:
        print(f"Chain invocation failed: {e}")
        return "Error: LLM timed out or encountered an issue."

# # Example usage:
# response = get_ollama_response(
#     "What are the common findings in PSMA PET scans?",
#     "You are a helpful medical AI assistant.",
#     "llama3.3:70b",
#     "no_rag"
# )
