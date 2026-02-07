import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory

class ConversationalOracle:
    def __init__(self, vector_db_path="./chroma_db"):
        self.persist_directory = vector_db_path # <--- This is the fix
        
        print(f"🧠 Loading Knowledge Base from {self.persist_directory}...")
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
        
        if not os.path.exists(self.persist_directory):
            print(f"❌ Error: No database found at {self.persist_directory}")
            return
            
        self.vectordb = Chroma(
            persist_directory=self.persist_directory, 
            embedding_function=self.embeddings,
            collection_name="webex_chats"
        )
        
        print("🤖 Loading Llama 3 Model...")
        self.llm = Ollama(model="llama3")
        
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        self.qa_chain = self.create_chain()

    def create_chain(self):
        return ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vectordb.as_retriever(search_kwargs={"k": 5}),
            memory=self.memory,
            verbose=False
        )

    def ask(self, query):
        if not hasattr(self, 'qa_chain'):
            return "Error: Database connection failed."
        result = self.qa_chain.invoke({"question": query})
        return result["answer"]
