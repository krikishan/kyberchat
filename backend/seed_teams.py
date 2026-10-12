import datetime
import uuid
from dotenv import load_dotenv

load_dotenv('../.env')

from app import create_app
from app.database.db import get_db

app = create_app()
with app.app_context():
    db = get_db()
    
    # 1. Check if any team exists
    existing = db.teams.find_one({"name": "Cyber Security Team"})
    sarah = db.users.find_one({"username": "sarah"})
    sarah_id = str(sarah["_id"]) if sarah else None
    
    if not existing:
        team_id = str(uuid.uuid4())
        now = datetime.datetime.utcnow()
        team_doc = {
            "team_id": team_id,
            "name": "Cyber Security Team",
            "description": "Primary post-quantum operations and cryptographic defense squad.",
            "lead_id": sarah_id,
            "created_at": now,
            "updated_at": now,
        }
        db.teams.insert_one(team_doc)
        print(f"[created] Team: Cyber Security Team (id: {team_id})")
    else:
        team_id = existing["team_id"]
        if sarah_id and not existing.get("lead_id"):
            db.teams.update_one({"team_id": team_id}, {"$set": {"lead_id": sarah_id}})
        print(f"[existing] Team: Cyber Security Team (id: {team_id})")

    # 2. Assign sarah as Team Lead
    if sarah:
        db.users.update_one({"_id": sarah["_id"]}, {"$set": {"team_id": team_id, "team_name": "Cyber Security Team"}})
        print(f"[assigned] Sarah Chen as Team Lead of Cyber Security Team")

    # 3. Assign alex and jordan as members
    for uname in ["alex", "jordan"]:
        u = db.users.find_one({"username": uname})
        if u:
            db.users.update_one({"_id": u["_id"]}, {"$set": {"team_id": team_id, "team_name": "Cyber Security Team"}})
            print(f"[assigned] {u.get('name')} as member of Cyber Security Team")

    print("\n--- Current Teams in DB ---")
    for t in db.teams.find():
        lead = db.users.find_one({"_id": t.get("lead_id")}) or db.users.find_one({"_id": t.get("lead_id")})
        lead_name = lead.get("name") if lead else "None"
        members = list(db.users.find({"team_id": t["team_id"], "role": "user"}))
        print(f"Team: {t['name']} | Lead: {lead_name} | Members count: {len(members)}")
