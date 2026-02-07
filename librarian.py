import json
import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

class ChatLibrarian:
    def __init__(self, json_path, vector_db_path="./chroma_db"):
        self.json_path = json_path
        self.persist_directory = vector_db_path # <--- This is the fix
        
        print("🧠 Initializing Embedding Model (nomic-embed-text)...")
        self.embedding_model = OllamaEmbeddings(model="nomic-embed-text")

    def load_and_process_data(self):
        print(f"📂 Loading chat data from {self.json_path}...")
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        messages = data.get('messages', [])
        documents = []

        for msg in messages:
            if not msg.get('text'): continue

            sender = msg.get('senderName', 'Unknown')
            date = msg.get('created', '')[:10]
            text = msg.get('text', '').strip()
            
            context_prefix = "REPLY TO THREAD: " if msg.get('is_reply') else ""
            page_content = f"[{date}] {sender}: {context_prefix}{text}"
            
            metadata = {
                "sender": sender,
                "date": date,
                "room": data.get('meta', {}).get('room_name', 'Unknown'),
                "is_reply": msg.get('is_reply', False)
            }
            
            documents.append(Document(page_content=page_content, metadata=metadata))

        return documents

    def index_data(self):
        docs = self.load_and_process_data()
        
        if not docs:
            print("❌ No valid text messages found to index.")
            return

        print(f"📚 Indexing {len(docs)} conversation snippets...")
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        splits = text_splitter.split_documents(docs)
        
        # Save to the specific unique folder
        Chroma.from_documents(
            documents=splits, 
            embedding=self.embedding_model, 
            persist_directory=self.persist_directory,
            collection_name="webex_chats"
        )
        
        print(f"✅ Success! Saved chunks to: {self.persist_directory}")
