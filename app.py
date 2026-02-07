import os
import shutil
import time
import pandas as pd
from webex_harvester import WebexHarvester
from librarian import ChatLibrarian
from oracle import ConversationalOracle
from qa_extractor import SmartQAExtractor
from analytics_engine import ChatAnalyst # <--- Import Analyst

def clear_brain():
    """Wipes the existing vector database to ensure a clean slate."""
    db_path = "./chroma_db"
    if os.path.exists(db_path):
        shutil.rmtree(db_path)
        time.sleep(1)

def print_advanced_qa_stats(qa_list):
    """Calculates who asked/answered the most based on the Q&A extraction."""
    if not qa_list:
        return

    df = pd.DataFrame(qa_list)
    print("\n" + "="*50)
    print("🧠 Q&A INTELLIGENCE REPORT")
    print("="*50)
    
    # 1. Who asks the most?
    if 'Asked By' in df.columns:
        print("❓ Top Question Askers:")
        print(df['Asked By'].value_counts().head(3).to_string())
        print("-" * 30)

    # 2. Who answers the most? (Requires parsing the names)
    # The 'Participants' column often lists everyone. The 'Answered By' logic 
    # might need to be inferred or we just use 'Participants' for now.
    # In the Excel extractor, we saved "Participants". Let's use that as a proxy for engagement.
    if 'Participants' in df.columns:
        # Split comma-separated names and explode to count individuals
        all_participants = df['Participants'].str.split(', ').explode()
        print("💡 Top Problem Solvers (Participants in Q&A Threads):")
        print(all_participants.value_counts().head(3).to_string())
    
    print("="*50)

def main_workflow():
    print("\n" + "="*50)
    print("🚀 WEBEX INTELLIGENT AGENT")
    print("==================================================")

    # --- STEP 1: AUTHENTICATION ---
    token = os.getenv("WEBEX_ACCESS_TOKEN")
    if not token:
        print("🔑 Please enter your Webex Access Token:")
        token = input("Token: ").strip()
    
    if not token:
        print("❌ Token required. Exiting.")
        return

    # --- STEP 2: ROOM SELECTION ---
    harvester = WebexHarvester(token)
    rooms = harvester.list_rooms()

    if not rooms:
        print("❌ No rooms found.")
        return

    try:
        selection = int(input("👉 Select a room number to load: ")) - 1
        if not (0 <= selection < len(rooms)):
            print("❌ Invalid selection.")
            return
        
        selected_room = rooms[selection]
        room_title = selected_room['title']
        room_id = selected_room['id']
        
    except ValueError:
        print("❌ Invalid input.")
        return

    # --- STEP 3: DATA ACQUISITION ---
    print(f"\n📥 Phase 1: Downloading Chat History for '{room_title}'...")
    print("   [1] Download Entire History")
    print("   [2] Filter by Year")
    choice = input("   👉 Choice (default 1): ").strip()
    
    target_year = None
    label = "All"
    if choice == "2":
        target_year = int(input("   📅 Enter Year (e.g. 2024): ").strip())
        label = str(target_year)

    messages = harvester.get_messages(room_id, room_title, target_year)
    
    safe_title = "".join([c for c in room_title if c.isalnum() or c in (' ', '-', '_')]).strip()
    json_filename = f"data/{safe_title}_{label}.json"
    
    harvester.save_data(room_title, messages, label)

    # --- STEP 4: GENERAL ANALYTICS ---
    # We call the engine we built earlier
    try:
        analyst = ChatAnalyst(json_filename)
        analyst.show_basic_stats()
        analyst.get_top_talkers(top_n=3)
        # analyst.get_activity_timeline() # Optional: keep console clean
    except Exception as e:
        print(f"⚠️ Basic Analytics skipped: {e}")

    # --- STEP 5: Q&A MINING & REPORTS ---
    print(f"\n📊 Phase 2: Generating Q&A Excel & Advanced Stats...")
    try:
        extractor = SmartQAExtractor(json_filename)
        qa_data = extractor.extract_qa()
        
        # Save Excel
        extractor.save_to_excel(qa_data)
        
        # Print the Q&A Stats (Who asked/answered most)
        print_advanced_qa_stats(qa_data)
        
    except Exception as e:
        print(f"⚠️ Q&A Analysis skipped: {e}")

    # --- STEP 6: INDEXING (THE LIBRARIAN) ---
    print(f"\n🧠 Phase 3: Learning Content (Vector Indexing)...")
    clear_brain()
    
    try:
        librarian = ChatLibrarian(json_filename)
        librarian.index_data()
    except Exception as e:
        print(f"❌ Indexing failed: {e}")
        return

    # --- STEP 7: CHAT (THE ORACLE) ---
    print("\n" + "="*50)
    print(f"🔮 CHAT ACTIVE: Connected to '{room_title}'")
    print("   (Type 'switch' to change rooms, 'exit' to quit)")
    print("="*50)

    oracle = ConversationalOracle()

    while True:
        query = input("\nYou: ")
        
        if query.lower() in ['exit', 'quit', 'q']:
            print("👋 Bye!")
            exit()
            
        if query.lower() == 'switch':
            print("\n🔄 Restarting...")
            main_workflow()
            break
            
        if not query.strip():
            continue
            
        oracle.ask(query)

if __name__ == "__main__":
    if not os.path.exists("data"):
        os.makedirs("data")
        
    try:
        main_workflow()
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
