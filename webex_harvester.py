import requests
import json
import os
import time
from datetime import datetime

class WebexHarvester:
    def __init__(self, token):
        self.base_url = "https://webexapis.com/v1"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.user_map = {}

    def list_rooms(self):
        url = f"{self.base_url}/rooms"
        params = {"max": 100, "sortBy": "lastactivity"}
        all_group_rooms = []

        print(f"⏳ Scanning all your spaces...")
        while url:
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 429:
                time.sleep(int(response.headers.get("Retry-After", 5)))
                continue
            if response.status_code != 200:
                print(f"❌ Error: {response.text}")
                break

            data = response.json()
            groups = [r for r in data.get('items', []) if r.get('type') == 'group']
            all_group_rooms.extend(groups)

            link = response.headers.get("Link")
            if link and 'rel="next"' in link:
                url = link.split(";")[0].strip("<>")
                params = {}
            else:
                url = None

        all_group_rooms.sort(key=lambda x: x.get('lastActivity', ''), reverse=True)
        
        print("\n" + "="*70)
        print(f"{'#':<4} | {'Room Name':<45} | {'Last Active'}")
        print("-" * 70)
        for i, room in enumerate(all_group_rooms):
            last_active = room.get('lastActivity', '')[:10]
            print(f"{i+1:<4} | {room.get('title', 'Untitled')[:45]:<45} | {last_active}")
        print("="*70 + "\n")
        return all_group_rooms

    def resolve_user_names(self, messages):
        """
        Scans both Senders AND Mentions to resolve names.
        """
        unique_ids = set()
        
        # Collect Senders AND Mentioned People
        for msg in messages:
            if msg.get('personId'):
                unique_ids.add(msg['personId'])
            if msg.get('mentionedPeople'):
                unique_ids.update(msg['mentionedPeople'])

        # Filter out already known users
        ids_to_fetch = [uid for uid in unique_ids if uid not in self.user_map]

        if not ids_to_fetch:
            return

        print(f"🔎 Resolving names for {len(ids_to_fetch)} participants (Senders + Mentions)...")
        
        count = 0
        for person_id in ids_to_fetch:
            count += 1
            print(f"   ↳ Fetching name {count}/{len(ids_to_fetch)}", end="\r")
            try:
                res = requests.get(f"{self.base_url}/people/{person_id}", headers=self.headers)
                if res.status_code == 200:
                    p = res.json()
                    name = p.get('displayName') or p.get('nickName') or p.get('emails', ['Unknown'])[0]
                    self.user_map[person_id] = name
                elif res.status_code == 429:
                    time.sleep(2)
                else:
                    self.user_map[person_id] = "Unknown User"
            except:
                self.user_map[person_id] = "Unknown User"
        print(f"\n✅ User resolution complete.")

    def get_messages(self, room_id, room_title, target_year=None):
        url = f"{self.base_url}/messages"
        params = {"roomId": room_id, "max": 1000}
        collected_messages = []
        
        print(f"🚀 Starting download for: {room_title}")
        if target_year:
            print(f"🎯 Filter: Only fetching messages from YEAR {target_year}")

        page_count = 0
        stop_fetching = False

        while url and not stop_fetching:
            page_count += 1
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 429:
                time.sleep(int(response.headers.get("Retry-After", 5)))
                continue
            if response.status_code != 200:
                print(f"❌ Error: {response.text}")
                break

            items = response.json().get('items', [])
            if not items:
                break

            for msg in items:
                msg_date_str = msg.get('created', '')
                msg_year = int(msg_date_str[:4])

                if target_year:
                    if msg_year > target_year:
                        continue
                    elif msg_year < target_year:
                        stop_fetching = True
                        break
                
                collected_messages.append(msg)

            last_date = items[-1].get('created', '')[:10]
            print(f"   ↳ Page {page_count} | Collected: {len(collected_messages)} | Current Date: {last_date}", end="\r")

            link = response.headers.get("Link")
            if link and 'rel="next"' in link:
                url = link.split(";")[0].strip("<>")
                params = {}
            else:
                url = None

        print(f"\n✅ Finished! collected {len(collected_messages)} messages.")
        self.resolve_user_names(collected_messages)
        return collected_messages

    def save_data(self, room_title, messages, year_label="All"):
        if not os.path.exists("data"):
            os.makedirs("data")

        print("⚙️  Enriching messages (Adding flags & resolving mentions)...")
        for msg in messages:
            # 1. Sender Name
            pid = msg.get('personId')
            msg['senderName'] = self.user_map.get(pid, "Unknown User")
            
            # 2. Mentioned Names (New!)
            # Replaces ["id_1", "id_2"] with ["Name 1", "Name 2"]
            mentions = msg.get('mentionedPeople', [])
            msg['mentionedNames'] = [self.user_map.get(uid, "Unknown") for uid in mentions]

            # 3. Computed Flags (New!)
            msg['is_reply'] = True if msg.get('parentId') else False
            msg['has_attachments'] = True if msg.get('files') else False

        # Prepare File
        safe_title = "".join([c for c in room_title if c.isalnum() or c in (' ', '-', '_')]).strip()
        filename = f"data/{safe_title}_{year_label}.json"

        final_data = {
            "meta": {
                "room_name": room_title,
                "export_date": datetime.now().isoformat(),
                "filter_year": year_label,
                "message_count": len(messages)
            },
            "users": self.user_map,
            "messages": messages
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(final_data, f, indent=4, ensure_ascii=False)
        
        print(f"💾 Saved enriched data to: {filename}")

# --- Main Execution ---
if __name__ == "__main__":
    print("🔑 Enter your Webex Access Token:")
    token = input("Token: ").strip()
    if not token: exit()

    harvester = WebexHarvester(token)
    rooms = harvester.list_rooms()

    if rooms:
        try:
            sel = int(input("👉 Select Room Number: ")) - 1
            if 0 <= sel < len(rooms):
                room = rooms[sel]
                print("\n1. Download ALL history")
                print("2. Download for specific YEAR")
                opt = input("👉 Select Option: ").strip()
                
                target_year = None
                label = "All"
                if opt == "2":
                    target_year = int(input("👉 Enter Year: ").strip())
                    label = str(target_year)

                msgs = harvester.get_messages(room['id'], room['title'], target_year)
                harvester.save_data(room['title'], msgs, label)
            else:
                print("❌ Invalid selection.")
        except ValueError:
            print("❌ Input error.")
