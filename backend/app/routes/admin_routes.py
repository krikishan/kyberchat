import datetime
import uuid
from bson import ObjectId
from flask import Blueprint, current_app, g, jsonify, request

from app import limiter
from app.ai.bulk_parser import ai_assisted_extract, build_preview
from app.auth.tokens import require_auth, require_role
from app.database.db import get_db
from app.services.audit_log import record_event
from app.services.user_service import UserCreationError, create_single_user

admin_bp = Blueprint("admin", __name__)


def _serialize_user(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "username": user.get("username", ""),
        "role": user.get("role", "user"),
        "status": user.get("status", "active"),
        "team_id": user.get("team_id"),
        "team_name": user.get("team_name"),
        "must_change_password": user.get("must_change_password", False),
        "created_at": user.get("created_at").isoformat() if user.get("created_at") else None,
        "last_login": user.get("last_login").isoformat() if user.get("last_login") else None,
    }


def _get_lead_team(db, user_id: str) -> dict | None:
    """Helper to find the team where user_id is the designated Team Lead."""
    return db.teams.find_one({"lead_id": user_id}) or db.teams.find_one({"_id": user_id})


# ---------------------------------------------------------------------------
#  Teams Management (Multi-team organization)
# ---------------------------------------------------------------------------

@admin_bp.route("/teams", methods=["GET"])
@require_auth
@require_role("admin")
def list_teams():
    """
    Developer sees all teams with their leads and member counts.
    Team Admin (Team Lead) sees their own assigned team.
    """
    db = get_db()
    current_user = g.current_user
    current_uid = str(current_user["_id"])
    is_developer = current_user.get("role") == "developer"

    if is_developer:
        team_docs = list(db.teams.find().sort("created_at", -1))
    else:
        # Team Admin: find assigned team
        team_filter = {"$or": [
            {"lead_id": current_uid},
            {"team_id": current_user.get("team_id")},
        ]}
        team_docs = list(db.teams.find(team_filter))

    # Preload all users to avoid N+1 queries
    all_users = list(db.users.find({}, {"password_hash": 0}))
    user_map = {str(u["_id"]): u for u in all_users}

    results = []
    for t in team_docs:
        tid = t["team_id"]
        lead_id = t.get("lead_id")
        lead_user = user_map.get(str(lead_id)) if lead_id else None
        
        # Members under this team
        team_members = [
            _serialize_user(u)
            for u in all_users
            if u.get("team_id") == tid and u.get("role") == "user"
        ]

        results.append({
            "team_id": tid,
            "name": t.get("name", "Untitled Team"),
            "description": t.get("description", ""),
            "lead": _serialize_user(lead_user) if lead_user else None,
            "member_count": len(team_members),
            "members": team_members,
            "created_at": t.get("created_at").isoformat() if t.get("created_at") else None,
        })

    # For Developer, also include unassigned users summary
    unassigned_members = [
        _serialize_user(u) for u in all_users
        if u.get("role") == "user" and (not u.get("team_id"))
    ] if is_developer else []

    unassigned_leads = [
        _serialize_user(u) for u in all_users
        if u.get("role") == "admin" and not any(t.get("lead_id") == str(u["_id"]) for t in team_docs)
    ] if is_developer else []

    return jsonify({
        "teams": results,
        "unassigned_members": unassigned_members,
        "unassigned_leads": unassigned_leads,
        "is_developer": is_developer,
    })


@admin_bp.route("/teams", methods=["POST"])
@require_auth
@require_role("developer")
@limiter.limit("20 per minute")
def create_team():
    """Developer only: Create a new team and optionally assign a Team Lead."""
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Team name is required."}), 400

    description = (data.get("description") or "").strip()
    lead_id = data.get("lead_id")

    db = get_db()
    # Check duplicate team name
    if db.teams.find_one({"name": {"$regex": f"^{name}$", "$options": "i"}}):
        return jsonify({"error": f"A team named '{name}' already exists."}), 400

    lead_doc = None
    if lead_id:
        try:
            lead_doc = db.users.find_one({"_id": ObjectId(lead_id), "role": "admin"})
        except Exception:
            lead_doc = db.users.find_one({"_id": lead_id, "role": "admin"})
        if not lead_doc:
            return jsonify({"error": "Specified Team Lead user not found or not an admin."}), 400

    now = datetime.datetime.utcnow()
    team_id = str(uuid.uuid4())
    team_doc = {
        "team_id": team_id,
        "name": name,
        "description": description,
        "lead_id": str(lead_doc["_id"]) if lead_doc else None,
        "created_by": str(g.current_user["_id"]),
        "created_at": now,
        "updated_at": now,
    }
    db.teams.insert_one(team_doc)

    # If lead assigned, update user's team_id and team_name
    if lead_doc:
        db.users.update_one(
            {"_id": lead_doc["_id"]},
            {"$set": {"team_id": team_id, "team_name": name, "updated_at": now}}
        )

    record_event(db, event_type="team_created", user_id=str(g.current_user["_id"]),
                 details={"team_id": team_id, "name": name, "lead_id": team_doc["lead_id"]})

    return jsonify({
        "message": f"Team '{name}' created successfully.",
        "team": {
            "team_id": team_id,
            "name": name,
            "description": description,
            "lead": _serialize_user(lead_doc) if lead_doc else None,
            "member_count": 0,
            "members": [],
        }
    }), 201


@admin_bp.route("/teams/<team_id>", methods=["PUT"])
@require_auth
@require_role("developer")
def update_team(team_id):
    """Developer only: Update team name, description, or change Team Lead."""
    data = request.get_json(silent=True) or {}
    db = get_db()
    team = db.teams.find_one({"team_id": team_id})
    if not team:
        return jsonify({"error": "Team not found."}), 404

    now = datetime.datetime.utcnow()
    updates = {"updated_at": now}

    if "name" in data:
        name = (data["name"] or "").strip()
        if not name:
            return jsonify({"error": "Team name cannot be empty."}), 400
        updates["name"] = name
        # Also update denormalized team_name on assigned users
        db.users.update_many({"team_id": team_id}, {"$set": {"team_name": name, "updated_at": now}})

    if "description" in data:
        updates["description"] = (data["description"] or "").strip()

    if "lead_id" in data:
        new_lead_id = data["lead_id"]
        if new_lead_id:
            try:
                new_lead = db.users.find_one({"_id": ObjectId(new_lead_id), "role": "admin"})
            except Exception:
                new_lead = db.users.find_one({"_id": new_lead_id, "role": "admin"})
            if not new_lead:
                return jsonify({"error": "Team Lead user not found or not an admin."}), 400

            # Remove previous lead's team reference if different
            old_lead_id = team.get("lead_id")
            if old_lead_id and old_lead_id != str(new_lead["_id"]):
                db.users.update_one({"_id": ObjectId(old_lead_id)}, {"$unset": {"team_id": "", "team_name": ""}})

            updates["lead_id"] = str(new_lead["_id"])
            db.users.update_one(
                {"_id": new_lead["_id"]},
                {"$set": {"team_id": team_id, "team_name": updates.get("name", team.get("name")), "updated_at": now}}
            )
        else:
            # Clear lead
            old_lead_id = team.get("lead_id")
            if old_lead_id:
                try:
                    db.users.update_one({"_id": ObjectId(old_lead_id)}, {"$unset": {"team_id": "", "team_name": ""}})
                except Exception:
                    pass
            updates["lead_id"] = None

    db.teams.update_one({"team_id": team_id}, {"$set": updates})
    record_event(db, event_type="team_updated", user_id=str(g.current_user["_id"]),
                 details={"team_id": team_id, "updates": list(updates.keys())})

    return jsonify({"message": "Team updated successfully."})


@admin_bp.route("/teams/<team_id>", methods=["DELETE"])
@require_auth
@require_role("developer")
def delete_team(team_id):
    """Developer only: Delete an entire team and unassign its members."""
    db = get_db()
    team = db.teams.find_one({"team_id": team_id})
    if not team:
        return jsonify({"error": "Team not found."}), 404

    # Unassign all users from this team
    db.users.update_many(
        {"team_id": team_id},
        {"$unset": {"team_id": "", "team_name": ""}, "$set": {"updated_at": datetime.datetime.utcnow()}}
    )
    # Remove team doc
    db.teams.delete_one({"team_id": team_id})

    record_event(db, event_type="team_deleted", user_id=str(g.current_user["_id"]),
                 details={"team_id": team_id, "name": team.get("name")})

    return jsonify({"message": f"Team '{team.get('name')}' deleted successfully. Members have been unassigned."})


# ---------------------------------------------------------------------------
#  Developer-only: Team Lead / Admin management
# ---------------------------------------------------------------------------

@admin_bp.route("/team-admins", methods=["POST"])
@require_auth
@require_role("developer")
@limiter.limit("10 per minute")
def create_team_admin():
    """
    Developer only: Create a Team Lead account.
    Optionally pass 'team_id' to assign them as lead of an existing team immediately.
    """
    data = request.get_json(silent=True) or {}
    team_id = data.get("team_id")
    db = get_db()

    try:
        user = create_single_user(db, current_app.config, data.get("name"), data.get("email"), role="admin", team_id=team_id)
    except UserCreationError as exc:
        return jsonify({"error": str(exc), "code": exc.code}), 400

    # If team_id given, assign as team's lead_id
    if team_id:
        db.teams.update_one({"team_id": team_id}, {"$set": {"lead_id": user["id"]}})

    record_event(db, event_type="team_admin_created", user_id=str(g.current_user["_id"]),
                 details={"new_admin_id": user["id"], "team_id": team_id})
    return jsonify({"message": "Team Lead created.", "user": user}), 201


@admin_bp.route("/team-admins", methods=["GET"])
@require_auth
@require_role("developer")
def list_team_admins():
    """List all Team Admin accounts with their assigned teams (developer only)."""
    db = get_db()
    admins = list(db.users.find({"role": "admin"}))
    return jsonify({"admins": [_serialize_user(a) for a in admins]})


@admin_bp.route("/team-admins/<admin_id>", methods=["PATCH"])
@require_auth
@require_role("developer")
def update_team_admin(admin_id):
    """Activate/deactivate a Team Admin."""
    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    if new_status not in ("active", "inactive"):
        return jsonify({"error": "status must be 'active' or 'inactive'."}), 400

    db = get_db()
    try:
        oid = ObjectId(admin_id)
    except Exception:
        return jsonify({"error": "Invalid user id."}), 400

    target = db.users.find_one({"_id": oid})
    if not target or target.get("role") != "admin":
        return jsonify({"error": "Team Admin not found."}), 404

    db.users.update_one({"_id": oid}, {"$set": {"status": new_status}, "$inc": {"session_version": 1}})
    record_event(db, event_type="admin_status_changed", user_id=str(g.current_user["_id"]),
                 details={"target_admin_id": admin_id, "new_status": new_status})
    return jsonify({"message": f"Team Admin {new_status}."})


# ---------------------------------------------------------------------------
#  Member Management (Developer & Team Lead)
# ---------------------------------------------------------------------------

@admin_bp.route("/users", methods=["POST"])
@require_auth
@require_role("admin")
@limiter.limit("30 per minute")
def add_member():
    """
    Create a regular member.
    - If caller is Team Lead (admin): Automatically assigned to the Team Lead's team!
    - If caller is Developer: Can specify team_id in request body.
    """
    data = request.get_json(silent=True) or {}
    db = get_db()
    current_user = g.current_user
    is_developer = current_user.get("role") == "developer"

    if is_developer:
        target_team_id = data.get("team_id")
    else:
        # Team Lead: find their assigned team
        lead_uid = str(current_user["_id"])
        lead_team = db.teams.find_one({"lead_id": lead_uid}) or (
            db.teams.find_one({"team_id": current_user.get("team_id")}) if current_user.get("team_id") else None
        )
        if not lead_team:
            return jsonify({"error": "You are not assigned as a Team Lead to any team. Contact the Developer."}), 403
        target_team_id = lead_team["team_id"]

    try:
        user = create_single_user(db, current_app.config, data.get("name"), data.get("email"), role="user", team_id=target_team_id)
    except UserCreationError as exc:
        return jsonify({"error": str(exc), "code": exc.code}), 400

    record_event(db, event_type="member_added", user_id=str(current_user["_id"]),
                 details={"new_user_id": user["id"], "team_id": target_team_id})

    return jsonify({"message": "Member added.", "user": user}), 201


@admin_bp.route("/users", methods=["GET"])
@require_auth
@require_role("admin")
def list_members():
    """
    List members.
    - If caller is Team Lead (admin): ONLY returns members belonging to their team!
    - If caller is Developer: returns all members (or filtered by ?team_id=...).
    """
    db = get_db()
    current_user = g.current_user
    is_developer = current_user.get("role") == "developer"
    page = max(int(request.args.get("page", 1)), 1)
    page_size = min(int(request.args.get("page_size", 50)), 100)

    query = {"role": "user"}

    if is_developer:
        team_id_filter = request.args.get("team_id")
        if team_id_filter:
            query["team_id"] = team_id_filter
    else:
        # Team Lead: scoped strictly to own team
        lead_uid = str(current_user["_id"])
        lead_team = db.teams.find_one({"lead_id": lead_uid}) or (
            db.teams.find_one({"team_id": current_user.get("team_id")}) if current_user.get("team_id") else None
        )
        if not lead_team:
            return jsonify({"users": [], "total": 0, "page": page, "team_name": None})
        query["team_id"] = lead_team["team_id"]

    users = list(db.users.find(query).skip((page - 1) * page_size).limit(page_size))
    total = db.users.count_documents(query)

    return jsonify({
        "users": [_serialize_user(u) for u in users],
        "total": total,
        "page": page,
    })


@admin_bp.route("/users/<user_id>", methods=["GET"])
@require_auth
@require_role("admin")
def get_member(user_id):
    db = get_db()
    try:
        user = db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return jsonify({"error": "Invalid user id."}), 400
    if not user:
        return jsonify({"error": "User not found."}), 404

    # If caller is Team Lead, ensure target is in their team
    current_user = g.current_user
    if current_user.get("role") != "developer":
        lead_team = db.teams.find_one({"lead_id": str(current_user["_id"])})
        if not lead_team or user.get("team_id") != lead_team.get("team_id"):
            return jsonify({"error": "Unauthorized access to member outside your team."}), 403

    return jsonify(_serialize_user(user))


@admin_bp.route("/users/<user_id>", methods=["PATCH"])
@require_auth
@require_role("admin")
def update_member(user_id):
    """Activate/deactivate a member."""
    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    if new_status not in ("active", "inactive"):
        return jsonify({"error": "status must be 'active' or 'inactive'."}), 400

    db = get_db()
    try:
        oid = ObjectId(user_id)
    except Exception:
        return jsonify({"error": "Invalid user id."}), 400

    target = db.users.find_one({"_id": oid})
    if not target or target.get("role") != "user":
        return jsonify({"error": "User not found."}), 404

    current_user = g.current_user
    if current_user.get("role") != "developer":
        lead_team = db.teams.find_one({"lead_id": str(current_user["_id"])})
        if not lead_team or target.get("team_id") != lead_team.get("team_id"):
            return jsonify({"error": "You can only modify members of your own team."}), 403

    db.users.update_one({"_id": oid}, {"$set": {"status": new_status}, "$inc": {"session_version": 1}})
    record_event(db, event_type="user_status_changed", user_id=str(g.current_user["_id"]),
                 details={"target_user_id": user_id, "new_status": new_status})
    return jsonify({"message": f"Member {new_status}."})


# ---------------------------------------------------------------------------
#  Account Deletion (Developer can delete any user; Team Lead only own members)
# ---------------------------------------------------------------------------

@admin_bp.route("/users/<user_id>", methods=["DELETE"])
@require_auth
@require_role("admin")
def delete_user(user_id):
    """
    Delete an account.
    - Developer: Can delete any account (Team Lead, Team Member) except Developer self.
    - Team Lead: Can ONLY delete Team Members ('user' role) belonging to their own team.
    """
    db = get_db()
    current_user = g.current_user
    current_uid = str(current_user["_id"])
    is_developer = current_user.get("role") == "developer"

    try:
        oid = ObjectId(user_id)
    except Exception:
        return jsonify({"error": "Invalid user ID format."}), 400

    target = db.users.find_one({"_id": oid})
    if not target:
        return jsonify({"error": "User account not found."}), 404

    target_role = target.get("role", "user")

    # Protection 1: Never delete self
    if str(target["_id"]) == current_uid:
        return jsonify({"error": "You cannot delete your own account."}), 400

    # Protection 2: Never delete a developer
    if target_role == "developer":
        return jsonify({"error": "Developer accounts cannot be deleted."}), 403

    # Protection 3: Team Lead permissions check
    if not is_developer:
        # Team Lead can only delete 'user' role
        if target_role != "user":
            return jsonify({"error": "Team Leads are only permitted to delete team members."}), 403

        # Must belong to Team Lead's team
        lead_team = db.teams.find_one({"lead_id": current_uid})
        if not lead_team or target.get("team_id") != lead_team.get("team_id"):
            return jsonify({"error": "You can only delete members belonging to your own team."}), 403

    # Execution:
    # 1. If target was a Team Lead of any team, clear lead_id on that team
    db.teams.update_many({"lead_id": str(target["_id"])}, {"$set": {"lead_id": None}})

    # 2. Delete user cryptographic key directory records
    db.user_keys.delete_many({"user_id": str(target["_id"])})

    # 3. Pull user from all group member lists
    db.groups.update_many({}, {"$pull": {"members": str(target["_id"])}})

    # 4. Delete user document from users collection
    db.users.delete_one({"_id": oid})

    record_event(db, event_type="user_deleted", user_id=current_uid,
                 details={
                     "deleted_user_id": user_id,
                     "deleted_role": target_role,
                     "deleted_name": target.get("name"),
                     "deleted_username": target.get("username"),
                     "deleted_by_role": current_user.get("role"),
                 })

    return jsonify({
        "message": f"Account '{target.get('name')}' (@{target.get('username')}) has been permanently deleted.",
        "deleted_user_id": user_id,
    })


# ---------------------------------------------------------------------------
#  Bulk Member Import
# ---------------------------------------------------------------------------

@admin_bp.route("/users/bulk/preview", methods=["POST"])
@require_auth
@require_role("admin")
@limiter.limit("10 per minute")
def bulk_preview():
    """Body: {"raw_text": "user1@x.com\\nuser2@x.com ..."}"""
    data = request.get_json(silent=True) or {}
    raw_text = data.get("raw_text", "")
    db = get_db()

    groq_client = getattr(current_app, "groq_client", None)
    candidates = ai_assisted_extract(raw_text, groq_client)

    try:
        preview = build_preview(db, candidates, current_app.config["BULK_ADD_MAX_BATCH"])
    except UserCreationError as exc:
        return jsonify({"error": str(exc), "code": exc.code}), 400

    return jsonify(preview)


@admin_bp.route("/users/bulk/confirm", methods=["POST"])
@require_auth
@require_role("admin")
@limiter.limit("5 per minute")
def bulk_confirm():
    data = request.get_json(silent=True) or {}
    emails = data.get("emails") or []
    names = data.get("names") or {}
    db = get_db()
    current_user = g.current_user
    is_developer = current_user.get("role") == "developer"

    if len(emails) > current_app.config["BULK_ADD_MAX_BATCH"]:
        return jsonify({"error": f"Batch too large: max {current_app.config['BULK_ADD_MAX_BATCH']}."}), 400

    if is_developer:
        target_team_id = data.get("team_id")
    else:
        lead_team = db.teams.find_one({"lead_id": str(current_user["_id"])})
        target_team_id = lead_team.get("team_id") if lead_team else None

    created, failed = [], []
    for email in emails:
        name = names.get(email, email.split("@")[0])
        try:
            user = create_single_user(db, current_app.config, name, email, role="user", team_id=target_team_id)
            created.append(user)
        except UserCreationError as exc:
            failed.append({"email": email, "error": str(exc), "code": exc.code})

    record_event(db, event_type="bulk_user_creation", user_id=str(current_user["_id"]),
                 details={"created_count": len(created), "failed_count": len(failed), "team_id": target_team_id})

    return jsonify({"created": created, "failed": failed}), 201 if created else 200
