"""Community Forum API routes — ticketing-style Q&A with point awards."""
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

import deps

router = APIRouter(prefix="/forum", tags=["Forum"])


# ─── Request / Response models ───

class CreatePostRequest(BaseModel):
    title: str
    content: str
    tags: List[str] = []


class CreateCommentRequest(BaseModel):
    content: str


class ClosePostRequest(BaseModel):
    best_answer_id: Optional[str] = None
    active_collaborator_ids: List[str] = []


class VoteRequest(BaseModel):
    vote_type: str  # "up" or "down"


# ─── Helpers ───

async def _enrich_author(doc: dict) -> dict:
    """Add author_name from users collection."""
    if doc.get("author_id"):
        user = await deps.db.users.find_one(
            {"id": doc["author_id"]}, {"_id": 0, "name": 1, "email": 1, "role": 1}
        )
        if user:
            doc["author_name"] = user.get("name") or user.get("email", "Unknown")
            doc["author_role"] = user.get("role", "member")
    return doc


async def _enrich_comment_votes(comment: dict, current_user_id: str = None) -> dict:
    """Add vote data to a comment: upvotes, downvotes, voters, user's vote."""
    db = deps.db
    votes = await db.forum_votes.find(
        {"comment_id": comment["id"]}, {"_id": 0}
    ).to_list(length=500)

    up_voters = []
    down_voters = []
    my_vote = None

    for v in votes:
        voter_name = v.get("voter_name", "Unknown")
        entry = {"user_id": v["user_id"], "name": voter_name}
        if v["vote_type"] == "up":
            up_voters.append(entry)
        else:
            down_voters.append(entry)
        if current_user_id and v["user_id"] == current_user_id:
            my_vote = v["vote_type"]

    comment["upvotes"] = len(up_voters)
    comment["downvotes"] = len(down_voters)
    comment["score"] = len(up_voters) - len(down_voters)
    comment["up_voters"] = up_voters
    comment["down_voters"] = down_voters
    comment["my_vote"] = my_vote
    return comment


async def _award_forum_points(user_id: str, points: int, source: str, metadata: dict = None):
    """Award points to a user for forum activity."""
    db = deps.db
    # Get current balance
    stats = await db.rewards_stats.find_one({"user_id": user_id}, {"_id": 0})
    current_balance = (stats or {}).get("lifetime_points", 0)
    spent = (stats or {}).get("spent_points", 0)
    new_balance = current_balance + points

    # Log the points
    log_entry = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "points": points,
        "balance_after": new_balance - spent,
        "type": "earned",
        "source": source,
        "metadata": metadata or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.rewards_point_logs.insert_one(log_entry)

    # Update stats
    await db.rewards_stats.update_one(
        {"user_id": user_id},
        {
            "$inc": {"lifetime_points": points, "monthly_points": points},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
        },
        upsert=True,
    )


# ─── Endpoints ───

@router.get("/posts")
async def list_posts(
    status: Optional[str] = Query(None, description="Filter: open, closed"),
    tag: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: dict = Depends(deps.get_current_user),
):
    """List forum posts with optional filters."""
    db = deps.db
    query = {}
    if status:
        query["status"] = status
    if tag:
        query["tags"] = tag
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"content": {"$regex": search, "$options": "i"}},
        ]

    total = await db.forum_posts.count_documents(query)
    cursor = (
        db.forum_posts.find(query, {"_id": 0})
        .sort("created_at", -1)
        .skip((page - 1) * page_size)
        .limit(page_size)
    )
    posts = await cursor.to_list(length=page_size)

    # Enrich with author info
    for p in posts:
        await _enrich_author(p)

    return {"posts": posts, "total": total, "page": page, "page_size": page_size}


@router.post("/posts")
async def create_post(
    body: CreatePostRequest,
    user: dict = Depends(deps.get_current_user),
):
    """Create a new forum post (ticket)."""
    db = deps.db
    post_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    post = {
        "id": post_id,
        "title": body.title.strip(),
        "content": body.content.strip(),
        "author_id": user["id"],
        "tags": body.tags,
        "status": "open",
        "best_answer_id": None,
        "active_collaborator_ids": [],
        "comment_count": 0,
        "views": 0,
        "created_at": now,
        "updated_at": now,
    }
    await db.forum_posts.insert_one(post)
    post.pop("_id", None)

    await _enrich_author(post)
    return post


@router.get("/posts/{post_id}")
async def get_post(
    post_id: str,
    user: dict = Depends(deps.get_current_user),
):
    """Get a single post with all its comments."""
    db = deps.db
    post = await db.forum_posts.find_one({"id": post_id}, {"_id": 0})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Increment view count
    await db.forum_posts.update_one({"id": post_id}, {"$inc": {"views": 1}})
    post["views"] = post.get("views", 0) + 1

    # Enrich post author
    await _enrich_author(post)

    # Get comments
    comments = await db.forum_comments.find(
        {"post_id": post_id}, {"_id": 0}
    ).sort("created_at", 1).to_list(length=500)

    for c in comments:
        await _enrich_author(c)
        await _enrich_comment_votes(c, user["id"])

    post["comments"] = comments
    return post


@router.post("/posts/{post_id}/comments")
async def create_comment(
    post_id: str,
    body: CreateCommentRequest,
    user: dict = Depends(deps.get_current_user),
):
    """Add a comment to a post."""
    db = deps.db
    post = await db.forum_posts.find_one({"id": post_id}, {"_id": 0, "id": 1, "status": 1})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.get("status") == "closed":
        raise HTTPException(status_code=400, detail="Cannot comment on a closed post")

    comment_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    comment = {
        "id": comment_id,
        "post_id": post_id,
        "author_id": user["id"],
        "content": body.content.strip(),
        "is_best_answer": False,
        "created_at": now,
        "updated_at": now,
    }
    await db.forum_comments.insert_one(comment)
    comment.pop("_id", None)

    # Increment comment count
    await db.forum_posts.update_one({"id": post_id}, {"$inc": {"comment_count": 1}})

    await _enrich_author(comment)
    return comment


@router.put("/posts/{post_id}/best-answer/{comment_id}")
async def mark_best_answer(
    post_id: str,
    comment_id: str,
    user: dict = Depends(deps.get_current_user),
):
    """Mark a comment as best answer. Only the OP or admins can do this."""
    db = deps.db
    post = await db.forum_posts.find_one({"id": post_id}, {"_id": 0})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    is_op = post["author_id"] == user["id"]
    is_admin = user.get("role") in ("master_admin", "super_admin", "basic_admin")
    if not is_op and not is_admin:
        raise HTTPException(status_code=403, detail="Only the OP or admins can mark best answer")

    comment = await db.forum_comments.find_one({"id": comment_id, "post_id": post_id}, {"_id": 0})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Unmark previous best answer
    await db.forum_comments.update_many(
        {"post_id": post_id, "is_best_answer": True},
        {"$set": {"is_best_answer": False}},
    )

    # Mark new best answer
    await db.forum_comments.update_one(
        {"id": comment_id},
        {"$set": {"is_best_answer": True}},
    )

    # Update post
    await db.forum_posts.update_one(
        {"id": post_id},
        {"$set": {"best_answer_id": comment_id, "updated_at": datetime.now(timezone.utc).isoformat()}},
    )

    return {"message": "Best answer marked", "comment_id": comment_id}


@router.put("/posts/{post_id}/close")
async def close_post(
    post_id: str,
    body: ClosePostRequest,
    user: dict = Depends(deps.get_current_user),
):
    """Close/solve a post. Only the OP or admins can close.
    Awards points:
    - Best Answer author: 50 points
    - Active Collaborators: 15 points each
    """
    db = deps.db
    post = await db.forum_posts.find_one({"id": post_id}, {"_id": 0})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.get("status") == "closed":
        raise HTTPException(status_code=400, detail="Post is already closed")

    is_op = post["author_id"] == user["id"]
    is_admin = user.get("role") in ("master_admin", "super_admin", "basic_admin")
    if not is_op and not is_admin:
        raise HTTPException(status_code=403, detail="Only the OP or admins can close this post")

    now = datetime.now(timezone.utc).isoformat()
    update = {
        "$set": {
            "status": "closed",
            "closed_by": user["id"],
            "closed_at": now,
            "updated_at": now,
            "active_collaborator_ids": body.active_collaborator_ids,
        }
    }

    # If best_answer_id provided, mark it
    best_answer_id = body.best_answer_id or post.get("best_answer_id")
    points_awarded = []

    if best_answer_id:
        # Mark the best answer
        await db.forum_comments.update_many(
            {"post_id": post_id, "is_best_answer": True},
            {"$set": {"is_best_answer": False}},
        )
        await db.forum_comments.update_one(
            {"id": best_answer_id},
            {"$set": {"is_best_answer": True}},
        )
        update["$set"]["best_answer_id"] = best_answer_id

        # Award points to best answer author
        ba_comment = await db.forum_comments.find_one({"id": best_answer_id}, {"_id": 0, "author_id": 1})
        if ba_comment and ba_comment["author_id"] != post["author_id"]:
            await _award_forum_points(
                ba_comment["author_id"], 50, "forum_best_answer",
                {"post_id": post_id, "comment_id": best_answer_id},
            )
            ba_user = await db.users.find_one({"id": ba_comment["author_id"]}, {"_id": 0, "name": 1})
            points_awarded.append({
                "user_id": ba_comment["author_id"],
                "name": (ba_user or {}).get("name", "Unknown"),
                "points": 50,
                "reason": "Best Answer",
            })

    # Award points to active collaborators
    for collab_id in body.active_collaborator_ids:
        # Don't double-award the best answer author
        if best_answer_id:
            ba_comment = await db.forum_comments.find_one({"id": best_answer_id}, {"_id": 0, "author_id": 1})
            if ba_comment and collab_id == ba_comment["author_id"]:
                continue
        # Don't award the OP
        if collab_id == post["author_id"]:
            continue

        await _award_forum_points(
            collab_id, 15, "forum_active_collaborator",
            {"post_id": post_id},
        )
        collab_user = await db.users.find_one({"id": collab_id}, {"_id": 0, "name": 1})
        points_awarded.append({
            "user_id": collab_id,
            "name": (collab_user or {}).get("name", "Unknown"),
            "points": 15,
            "reason": "Active Collaborator",
        })

    await db.forum_posts.update_one({"id": post_id}, update)

    return {
        "message": "Post closed successfully",
        "post_id": post_id,
        "points_awarded": points_awarded,
    }


@router.get("/stats")
async def get_forum_stats(user: dict = Depends(deps.get_current_user)):
    """Get forum-wide statistics."""
    db = deps.db
    total_posts = await db.forum_posts.count_documents({})
    open_posts = await db.forum_posts.count_documents({"status": "open"})
    closed_posts = await db.forum_posts.count_documents({"status": "closed"})
    total_comments = await db.forum_comments.count_documents({})

    # Top contributors — combine best answers + upvotes received
    # 1. Best answers per user
    ba_pipeline = [
        {"$match": {"is_best_answer": True}},
        {"$group": {"_id": "$author_id", "best_answers": {"$sum": 1}}},
    ]
    ba_raw = await db.forum_comments.aggregate(ba_pipeline).to_list(length=100)
    ba_map = {e["_id"]: e["best_answers"] for e in ba_raw}

    # 2. Upvotes received per user (votes on their comments)
    vote_pipeline = [
        {"$match": {"vote_type": "up"}},
        {"$group": {"_id": "$comment_author_id", "upvotes": {"$sum": 1}}},
    ]
    vote_raw = await db.forum_votes.aggregate(vote_pipeline).to_list(length=100)
    vote_map = {e["_id"]: e["upvotes"] for e in vote_raw}

    # 3. Comments per user
    comment_pipeline = [
        {"$group": {"_id": "$author_id", "comments": {"$sum": 1}}},
    ]
    comment_raw = await db.forum_comments.aggregate(comment_pipeline).to_list(length=100)
    comment_map = {e["_id"]: e["comments"] for e in comment_raw}

    # Merge all user IDs
    all_user_ids = set(ba_map.keys()) | set(vote_map.keys()) | set(comment_map.keys())
    contributors = []
    for uid in all_user_ids:
        ba = ba_map.get(uid, 0)
        up = vote_map.get(uid, 0)
        cm = comment_map.get(uid, 0)
        # Reputation: 10 pts per best answer + 1 pt per upvote + 0.5 per comment
        reputation = (ba * 10) + up + int(cm * 0.5)
        contributors.append({
            "user_id": uid,
            "best_answers": ba,
            "upvotes_received": up,
            "comments_count": cm,
            "reputation": reputation,
        })

    # Sort by reputation desc, take top 10
    contributors.sort(key=lambda x: x["reputation"], reverse=True)
    top_contributors = contributors[:10]

    # Enrich with names
    for c in top_contributors:
        u = await db.users.find_one({"id": c["user_id"]}, {"_id": 0, "name": 1, "email": 1})
        c["name"] = (u or {}).get("name") or (u or {}).get("email", "Unknown")

    return {
        "total_posts": total_posts,
        "open_posts": open_posts,
        "closed_posts": closed_posts,
        "total_comments": total_comments,
        "top_contributors": top_contributors,
    }


@router.get("/search-similar")
async def search_similar_posts(
    q: str = Query(..., min_length=3),
    limit: int = Query(5, ge=1, le=10),
    user: dict = Depends(deps.get_current_user),
):
    """AJAX search for similar posts based on title query."""
    db = deps.db
    # Split query into words for better matching
    words = q.strip().split()
    # Build regex that matches any word
    regex_pattern = "|".join([w for w in words if len(w) >= 2])
    if not regex_pattern:
        return {"results": []}

    cursor = db.forum_posts.find(
        {"title": {"$regex": regex_pattern, "$options": "i"}},
        {"_id": 0, "id": 1, "title": 1, "status": 1, "comment_count": 1, "best_answer_id": 1, "created_at": 1},
    ).sort("created_at", -1).limit(limit)
    results = await cursor.to_list(length=limit)
    return {"results": results, "query": q}


@router.post("/comments/{comment_id}/vote")
async def vote_comment(
    comment_id: str,
    body: VoteRequest,
    user: dict = Depends(deps.get_current_user),
):
    """Upvote or downvote a comment. Toggle: same vote removes it, different vote switches."""
    db = deps.db
    if body.vote_type not in ("up", "down"):
        raise HTTPException(status_code=400, detail="vote_type must be 'up' or 'down'")

    comment = await db.forum_comments.find_one({"id": comment_id}, {"_id": 0, "id": 1, "author_id": 1})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Can't vote on your own comment
    if comment["author_id"] == user["id"]:
        raise HTTPException(status_code=400, detail="Cannot vote on your own comment")

    # Get voter name
    voter_user = await db.users.find_one({"id": user["id"]}, {"_id": 0, "name": 1, "email": 1})
    voter_name = (voter_user or {}).get("name") or (voter_user or {}).get("email", "Unknown")

    existing = await db.forum_votes.find_one(
        {"comment_id": comment_id, "user_id": user["id"]}, {"_id": 0}
    )

    if existing:
        if existing["vote_type"] == body.vote_type:
            # Same vote = remove (toggle off)
            await db.forum_votes.delete_one({"comment_id": comment_id, "user_id": user["id"]})
            return {"action": "removed", "vote_type": body.vote_type}
        else:
            # Different vote = switch
            await db.forum_votes.update_one(
                {"comment_id": comment_id, "user_id": user["id"]},
                {"$set": {"vote_type": body.vote_type, "voter_name": voter_name, "updated_at": datetime.now(timezone.utc).isoformat()}},
            )
            return {"action": "switched", "vote_type": body.vote_type}
    else:
        # New vote
        vote_doc = {
            "id": str(uuid.uuid4()),
            "comment_id": comment_id,
            "comment_author_id": comment["author_id"],
            "user_id": user["id"],
            "voter_name": voter_name,
            "vote_type": body.vote_type,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.forum_votes.insert_one(vote_doc)
        return {"action": "created", "vote_type": body.vote_type}


@router.get("/comments/{comment_id}/voters")
async def get_comment_voters(
    comment_id: str,
    user: dict = Depends(deps.get_current_user),
):
    """Get list of who voted on a comment."""
    db = deps.db
    votes = await db.forum_votes.find(
        {"comment_id": comment_id}, {"_id": 0, "user_id": 1, "voter_name": 1, "vote_type": 1, "created_at": 1}
    ).to_list(length=500)

    return {"comment_id": comment_id, "votes": votes}


@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: str,
    user: dict = Depends(deps.get_current_user),
):
    """Delete a post. Only the OP or admins can delete."""
    db = deps.db
    post = await db.forum_posts.find_one({"id": post_id}, {"_id": 0})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    is_op = post["author_id"] == user["id"]
    is_admin = user.get("role") in ("master_admin", "super_admin", "basic_admin")
    if not is_op and not is_admin:
        raise HTTPException(status_code=403, detail="Only the OP or admins can delete this post")

    await db.forum_comments.delete_many({"post_id": post_id})
    await db.forum_posts.delete_one({"id": post_id})

    return {"message": "Post deleted", "post_id": post_id}
