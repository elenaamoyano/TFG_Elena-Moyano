from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import tempfile
import shutil
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

app = FastAPI(
    title="API de Base de Conocimiento Multi-Tipo",
    description="API para gestionar múltiples bases de conocimiento vectoriales con Chroma",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CHROMA_BASE_DIR = "./chroma_db"

COLECCIONES = {
    "code": "code",
    "config": "config",
    "docker": "docker",
    "env": "env",
    "data_science_patterns": "data_science_patterns" #extra para prueba de data_science
}

vectorstores = {}

embedding_function = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)

def get_vectorstore(collection_name: str):
    """Obtiene o crea un vectorstore para una colección específica"""
    if collection_name not in COLECCIONES.values():
        raise HTTPException(status_code=400, detail=f"Colección inválida. Usa: {list(COLECCIONES.values())}")
    
    if collection_name not in vectorstores:
        persist_dir = os.path.join(CHROMA_BASE_DIR, collection_name)
        os.makedirs(persist_dir, exist_ok=True)
        
        vectorstores[collection_name] = Chroma(
            persist_directory=persist_dir,
            embedding_function=embedding_function,
            collection_name=collection_name
        )
        print(f"Colección '{collection_name}' inicializada en {persist_dir}")
    
    return vectorstores[collection_name]

@app.post("/ingest")
async def ingest_document(
    text: str = Body(..., embed=True),
    collection: str = Body(..., embed=True),
    chunk_size: int = 1000,
    chunk_overlap: int = 200
):
    """
    ENDPOINT PARA SUBIR TEXTO DIRECTO A CHROMA
    
    collection es OBLIGATORIO. Valores válidos:
    - code: .py
    - config: .conf
    - env: .env
    - docker: Dockerfile
    """
    
    if not text or len(text.strip()) == 0:
        raise HTTPException(status_code=400, detail="Texto vacío")
    
    if collection not in COLECCIONES.values():
        raise HTTPException(status_code=400, detail=f"Colección inválida. Usa: {list(COLECCIONES.values())}")
        
    doc = Document(
        page_content=text,
        metadata={
            "source": "text_input",
            "upload_time": str(datetime.now()),
            "collection": collection
        }
    )
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    chunks = text_splitter.split_documents([doc])
    
    for i, chunk in enumerate(chunks):
        chunk.metadata.update({
            "chunk_id": i,
            "total_chunks": len(chunks),
            "source": "direct_text"
        })
    
    vectorstore = get_vectorstore(collection)
    vectorstore.add_documents(chunks)
    vectorstore.persist()
    
    return {
        "message": f"Texto guardado en colección '{collection}'",
        "chunks_creados": len(chunks),
        "coleccion": collection
    }

@app.post("/query")
async def query_knowledge_base(
    query: str = Body(..., embed=True),
    collection: str = Body(..., embed=True),
    k: int = 5,
    score_threshold: Optional[float] = None
):
    """
    ENDPOINT PARA CONSULTAR UNA COLECCIÓN ESPECÍFICA
    
    collection es OBLIGATORIO. Valores válidos:
    - code, config, docker, env
    """
    
    if collection not in COLECCIONES.values():
        raise HTTPException(status_code=400, detail=f"Colección inválida. Usa: {list(COLECCIONES.values())}")
    
    try:
        vectorstore = get_vectorstore(collection)
        
        search_kwargs = {"k": k}
        if score_threshold:
            search_kwargs["score_threshold"] = score_threshold
        
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs=search_kwargs
        )
        
        docs = retriever.invoke(query)
        
        results = []
        for doc in docs:
            results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "similarity_score": doc.metadata.get("score", None)
            })
        
        return {
            "query": query,
            "collection": collection,
            "total_results": len(results),
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la búsqueda: {str(e)}")

@app.get("/collections")
async def list_collections():
    """Lista todas las colecciones disponibles y su estado"""
    active = []
    for name in vectorstores:
        try:
            docs = vectorstores[name].get()
            count = len(docs.get('ids', []))
            active.append({"name": name, "documents": count})
        except:
            active.append({"name": name, "documents": 0})
    
    return {
        "available_collections": list(COLECCIONES.values()),
        "active_collections": active,
        "description": {
            "code": "Código fuente (.py)",
            "config": "Configuración (.conf)",
            "env": "Secretos (.env)",
            "docker": "Assets (Dockerfile)"
        }
    }

@app.get("/documents")
async def list_documents(collection: str, limit: int = 100):
    """Lista documentos en una colección específica"""
    
    if collection not in COLECCIONES.values():
        raise HTTPException(status_code=400, detail=f"Colección inválida. Usa: {list(COLECCIONES.values())}")
    
    try:
        vectorstore = get_vectorstore(collection)
        all_docs = vectorstore.get(limit=limit)
        
        sources = set()
        for metadata in all_docs.get('metadatas', []):
            if metadata and 'source_file' in metadata:
                sources.add(metadata['source_file'])
        
        return {
            "collection": collection,
            "total_documents": len(all_docs.get('ids', [])),
            "unique_sources": list(sources),
            "sample_ids": all_docs.get('ids', [])[:10]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listando documentos: {str(e)}")

@app.delete("/reset")
async def reset_collection(collection: str, confirm: bool = False):
    """Elimina toda una colección (¡cuidado!)"""
    
    if collection not in COLECCIONES.values():
        raise HTTPException(status_code=400, detail=f"Colección inválida. Usa: {list(COLECCIONES.values())}")
    
    if not confirm:
        return {"message": f"Para resetear la colección '{collection}', llama con confirm=true"}
    
    try:
        global vectorstores
        
        if collection in vectorstores:
            try:
                vectorstores[collection].delete_collection()
            except:
                pass
            del vectorstores[collection]
        
        persist_dir = os.path.join(CHROMA_BASE_DIR, collection)
        if os.path.exists(persist_dir):
            shutil.rmtree(persist_dir)
        
        get_vectorstore(collection)
        
        return {"message": f"Colección '{collection}' reseteada correctamente"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reseteando: {str(e)}")


@app.delete("/delete_collection")
async def delete_collection(collection: str, confirm: bool = False):
    """Elimina una colección completamente (no la recrea)"""
    
    if collection not in COLECCIONES.values():
        raise HTTPException(status_code=400, detail=f"Colección inválida. Usa: {list(COLECCIONES.values())}")
    
    if not confirm:
        return {"message": f"Para eliminar la colección '{collection}', llama con confirm=true"}
    
    try:
        global vectorstores
        
        if collection in vectorstores:
            try:
                vectorstores[collection].delete_collection()
            except:
                pass
            del vectorstores[collection]
        
        persist_dir = os.path.join(CHROMA_BASE_DIR, collection)
        if os.path.exists(persist_dir):
            shutil.rmtree(persist_dir)
        
        return {"message": f"Colección '{collection}' eliminada correctamente"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error eliminando colección: {str(e)}")


def get_file_extension(filename: str) -> str:
    """Extrae la extensión de un nombre de archivo"""
    return os.path.splitext(filename)[1].lower()

@app.get("/health")
async def health_check():
    total_docs = 0
    collections_status = []
    
    for collection_name in COLECCIONES.values():
        try:
            if collection_name in vectorstores:
                docs = vectorstores[collection_name].get()
                count = len(docs.get('ids', []))
                total_docs += count
                collections_status.append({"collection": collection_name, "documents": count, "active": True})
            else:
                collections_status.append({"collection": collection_name, "documents": 0, "active": False})
        except:
            collections_status.append({"collection": collection_name, "documents": 0, "active": False})
    
    return {
        "status": "healthy",
        "collections": collections_status,
        "total_documents": total_docs,
        "embeddings_model": "all-MiniLM-L6-v2",
        "port": 8001,
        "base_dir": CHROMA_BASE_DIR
    }

if __name__ == "__main__":
    print(f"=" * 50)
    print(f"Iniciando API Multi-Colección (6 colecciones)")
    print(f"=" * 50)
    print(f"Chroma persistente en: {CHROMA_BASE_DIR}")
    print(f"Colecciones disponibles: {list(COLECCIONES.values())}")
    print(f"Puerto: 8001")
    print(f"=" * 50)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )