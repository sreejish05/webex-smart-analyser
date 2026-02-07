import streamlit as st
import pandas as pd
import os
import shutil
import gc
import uuid
import plotly.express as px
from webex_harvester import WebexHarvester
from analytics_engine import ChatAnalyst
from qa_extractor import SmartQAExtractor
from librarian import ChatLibrarian
from oracle import ConversationalOracle

st.set_page_config(page_title="Webex Intelligence", page_icon="🤖", layout="wide")

# --- STATE ---
if "messages" not in st.session_state: st.session_state.messages = [] 
if "data_loaded" not in st.session_state: st.session_state.data_loaded = False
if "current_room_id" not in st.session_state: st.session_state.current_room_id = None
if "harvester" not in st.session_state: st.session_state.harvester = None
if "oracle" not in st.session_state: st.session_state.oracle = None
if "db_path" not in st.session_state: st.session_state.db_path = None 

# --- HELPER FUNCTIONS ---
def cleanup_old_db():
    """Aggressively delete the PREVIOUS database folder to save space"""
    old_path = st.session_state.db_path
    if old_path and os.path.exists(old_path):
        try:
            shutil.rmtree(old_path)
            print(f"🧹 Cleaned up old DB: {old_path}")
        except Exception as e:
            print(f"⚠️ Could not delete old DB (might be locked): {e}")

@st.cache_data(show_spinner=False)
def load_webex_data(_harvester, room_id, room_title, target_year, label):
    msgs = _harvester.get_messages(room_id, room_title, target_year=target_year)
    safe_title = "".join([c for c in room_title if c.isalnum() or c in (' ', '-', '_')]).strip()
    json_path = f"data/{safe_title}_{label}.json"
    _harvester.save_data(room_title, msgs, label)
    return msgs, json_path

def init_oracle(json_path):
    # 1. Cleanup Session & Memory
    if st.session_state.oracle:
        del st.session_state.oracle
        st.session_state.oracle = None
    gc.collect()

    # 2. DELETE OLD FOLDER (Save Space)
    cleanup_old_db()

    # 3. Create NEW Unique Path (Avoid Lock)
    unique_id = uuid.uuid4().hex[:8]
    new_db_path = f"./chroma_db_{unique_id}"
    st.session_state.db_path = new_db_path 

    # 4. Index & Start
    librarian = ChatLibrarian(json_path, vector_db_path=new_db_path)
    librarian.index_data()
    return ConversationalOracle(vector_db_path=new_db_path)

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔐 Connection")
    st.markdown("👉 [Get your Webex Token here](https://developer.webex.com/docs/getting-started)")
    api_key = st.text_input("Webex API Key", type="password")
    
    if api_key:
        if st.session_state.harvester is None:
            st.session_state.harvester = WebexHarvester(api_key)
        
        with st.spinner("Fetching Rooms..."):
            if "room_list" not in st.session_state:
                st.session_state.room_list = st.session_state.harvester.list_rooms()
        
        room_map = {r['title']: r for r in st.session_state.room_list}
        selected_room_name = st.selectbox("Select Room", options=list(room_map.keys()))

        st.divider()
        st.subheader("📅 Date Scope")
        filter_option = st.radio("Download Scope", ["All History", "Specific Year"])
        
        target_year = None
        label = "All"
        if filter_option == "Specific Year":
            target_year = st.number_input("Enter Year", min_value=2010, max_value=2030, value=2025, step=1)
            label = str(target_year)
        st.divider()

        if st.button("🚀 Load Room Data"):
            selected_room = room_map[selected_room_name]
            st.session_state.current_room_id = selected_room['id']
            st.session_state.current_room_title = selected_room['title']
            st.session_state.target_year = target_year
            st.session_state.label = label
            
            st.session_state.data_loaded = False 
            st.session_state.messages = [] 
            st.rerun()

# --- MAIN PAGE ---
st.title("🤖 Webex Intelligent Agent")

if not api_key:
    st.info("👈 Please enter your Webex API Key in the sidebar to begin.")
    st.stop()

if "current_room_title" in st.session_state:
    st.markdown(f"### Active Room: **{st.session_state.current_room_title}**")
    st.caption(f"Scope: {st.session_state.label}")
    
    if not st.session_state.data_loaded:
        with st.status("⚙️ Processing Data...", expanded=True) as status:
            st.write(f"📥 Downloading Chat History ({st.session_state.label})...")
            msgs, json_path = load_webex_data(
                st.session_state.harvester, 
                st.session_state.current_room_id, 
                st.session_state.current_room_title,
                st.session_state.target_year, 
                st.session_state.label
            )
            st.session_state.json_path = json_path
            
            st.write("🧠 Indexing for AI (The Librarian)...")
            st.session_state.oracle = init_oracle(json_path)
            
            status.update(label="✅ Data Loaded & Indexed!", state="complete", expanded=False)
            st.session_state.data_loaded = True
            st.rerun()

    if st.session_state.data_loaded:
        tab1, tab2, tab3 = st.tabs(["📜 Chat Viewer", "📊 Analytics", "💬 Chat with Data"])

        with tab1:
            st.subheader("Raw Message History")
            analyst = ChatAnalyst(st.session_state.json_path)
            chat_df = analyst.df
            
            if chat_df.empty:
                st.warning(f"No messages found for the year {st.session_state.label}.")
            else:
                search_term = st.text_input("🔍 Search Messages:", "")
                display_df = chat_df[chat_df['text'].str.contains(search_term, case=False, na=False)] if search_term else chat_df
                
                st.dataframe(
                    display_df[['created', 'senderName', 'text']], 
                    column_config={"created": "Date", "senderName": "User", "text": "Message"},
                    use_container_width=True, height=400
                )
                st.caption(f"Showing {len(display_df)} messages.")

        with tab2:
            st.subheader("📈 Project Insights")
            if analyst.df.empty:
                st.warning("No data to analyze.")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**🏆 Top Contributors**")
                    top_users = analyst.df['senderName'].value_counts().head(10)
                    st.plotly_chart(px.bar(top_users, orientation='h', labels={'value': 'Messages', 'index': 'User'}), use_container_width=True)
                with col2:
                    st.markdown("**📅 Activity Timeline**")
                    activity = analyst.df['date'].value_counts().sort_index()
                    st.plotly_chart(px.line(activity, labels={'value': 'Messages', 'index': 'Date'}), use_container_width=True)

                st.divider()
                st.subheader("🧠 Q&A Extraction")
                if st.button("Generate Q&A Excel Report"):
                    with st.spinner("Mining Questions & Answers using AI..."):
                        extractor = SmartQAExtractor(st.session_state.json_path)
                        qa_data = extractor.extract_qa()
                        saved_path = extractor.save_to_excel(qa_data) # Saves to excel_reports/
                        
                        if qa_data:
                            qa_df = pd.DataFrame(qa_data)
                            st.success(f"✅ Extracted {len(qa_df)} Q&A pairs!")
                            st.info(f"File saved locally at: `{saved_path}`")
                            st.dataframe(qa_df, use_container_width=True, height=500)
                            st.download_button("📥 Download CSV Report", qa_df.to_csv(index=False).encode('utf-8'), "qa_report.csv", "text/csv")
                        else:
                            st.warning("No Q&A threads found.")

        with tab3:
            st.subheader("🔮 Chat with your Data")
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            if prompt := st.chat_input("Ask a question about this room..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        if st.session_state.oracle:
                            response = st.session_state.oracle.ask(prompt)
                            st.markdown(response)
                        else:
                            st.error("Oracle not initialized.")
                            response = "Error: Oracle not ready."
                
                st.session_state.messages.append({"role": "assistant", "content": response})
else:
    st.info("Select a room and click 'Load Room Data' to start.")
