import json
import pandas as pd
import os
from langchain_community.llms import Ollama

class SmartQAExtractor:
    def __init__(self, json_path):
        self.json_path = json_path
        with open(json_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        self.messages = self.data.get('messages', [])
        
        # Initialize the AI
        print("🧠 Loading AI Model (llama3) for summarization...")
        self.llm = Ollama(model="llama3")

    def summarize_answer(self, question, raw_replies):
        prompt = f"""
        You are a technical assistant. 
        Question: "{question}"
        Below is the chat discussion thread:
        {raw_replies}
        Task: Summarize the final solution. Be concise.
        """
        try:
            response = self.llm.invoke(prompt)
            return response.strip()
        except:
            return "Error generating summary"

    def extract_qa(self):
        print(f"⛏️  Mining Q&A from {len(self.messages)} messages...")
        threads = {}
        msg_lookup = {msg['id']: msg for msg in self.messages}

        for msg in self.messages:
            pid = msg.get('parentId')
            if pid:
                if pid not in threads: threads[pid] = []
                threads[pid].append(msg)

        qa_pairs = []
        
        for parent_id, replies in threads.items():
            q_msg = msg_lookup.get(parent_id)
            if not q_msg: continue
            
            q_text = q_msg.get('text', '')
            if '?' not in q_text: continue

            replies.sort(key=lambda x: x.get('created', ''))
            conversation_text = ""
            participants = set()
            
            for r in replies:
                name = r.get('senderName', 'Unknown')
                conversation_text += f"{name}: {r.get('text', '')}\n"
                participants.add(name)

            if len(replies) > 0:
                consolidated_answer = self.summarize_answer(q_text, conversation_text)
            else:
                consolidated_answer = "No replies."

            qa_pairs.append({
                "Date": q_msg.get('created', '')[:10],
                "Question": q_text,
                "AI Consolidated Answer": consolidated_answer,
                "Participants": ", ".join(participants),
                "Raw Thread": conversation_text
            })

        return qa_pairs

    def save_to_excel(self, qa_list):
        if not qa_list:
            return None

        # --- NEW FOLDER LOGIC ---
        output_folder = "excel_reports"
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        df = pd.DataFrame(qa_list)
        base = os.path.basename(self.json_path).replace('.json', '')
        # Save inside the new folder
        output_file = os.path.join(output_folder, f"{base}_FAQ.xlsx")
        
        df.to_excel(output_file, index=False)
        print(f"✅ Saved Excel to: {output_file}")
        return output_file
