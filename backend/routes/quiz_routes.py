"""Admin Quiz Management + Member Quiz Flow for Social Growth Engine.

Admin generates quiz questions about the Hub ecosystem, reviews and approves them,
then publishes them as daily tasks for members to complete.
"""
import uuid
import json as json_mod
import logging
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

import deps
from deps import get_current_user, require_admin, require_master_admin

logger = logging.getLogger("server")

router = APIRouter(prefix="/habits/quiz", tags=["Quiz"])

PLATFORM_TOPICS = ["Rewards", "Hub", "Website", "Merin", "MOIL10"]

# ─── Models ───

class GenerateQuizRequest(BaseModel):
    count: int = 5
    topic: Optional[str] = None  # None = mix of all topics
    difficulty: int = 1  # 1-7 mapping to social growth levels

class ApproveQuizRequest(BaseModel):
    quiz_ids: List[str]

class RejectQuizRequest(BaseModel):
    quiz_ids: List[str]
    reason: Optional[str] = None

class PublishQuizRequest(BaseModel):
    quiz_ids: List[str]
    date: Optional[str] = None  # defaults to today

class AnswerQuizRequest(BaseModel):
    answer: str


class EditQuizRequest(BaseModel):
    question: Optional[str] = None
    correct_answer: Optional[str] = None
    wrong_answers: Optional[List[str]] = None
    explanation: Optional[str] = None
    platform_topic: Optional[str] = None
    task_type: Optional[str] = None
    difficulty: Optional[int] = None


# Points for correct quiz answers (minimal but meaningful)
QUIZ_CORRECT_POINTS = 2


# ─── Admin: Generate Quizzes ───

@router.post("/admin/generate")
async def admin_generate_quizzes(data: GenerateQuizRequest, user: dict = Depends(require_admin)):
    """Generate quiz questions via AI about the Hub ecosystem. Returns for admin review."""
    from services.ai_service import call_llm
    db = deps.db

    topic_desc = f"Focus on the '{data.topic}' platform." if data.topic else "Mix questions across all platforms."

    difficulty_labels = {
        1: "Very easy (basic facts, what is X?)",
        2: "Easy (features and benefits)",
        3: "Medium (how-to and usage scenarios)",
        4: "Medium-Hard (comparisons and strategy)",
        5: "Hard (advanced features and edge cases)",
        6: "Hard (integration and growth tactics)",
        7: "Expert (deep knowledge and leadership scenarios)",
    }

    system = (
        "You are creating knowledge quiz questions for a trading community's growth program. "
        "The community uses these platforms:\n"
        "- **Rewards**: The rewards store where members earn and spend points for activities\n"
        "- **Hub**: The main community hub with profit tracking, trade monitoring, forums, and analytics\n"
        "- **Website**: The public-facing website for the community\n"
        "- **Merin**: The trading product/platform that members use for actual trading\n"
        "- **MOIL10**: The specific trading product/index used in the community\n\n"
        f"Generate exactly {data.count} multiple-choice quiz questions.\n"
        f"Difficulty: {difficulty_labels.get(data.difficulty, 'Medium')}\n"
        f"{topic_desc}\n\n"
        "Return a JSON array. Each question has:\n"
        '{"question": "...", "correct_answer": "...", "wrong_answers": ["...", "...", "..."], '
        '"explanation": "Short 1-2 sentence explanation of the correct answer", '
        f'"platform_topic": "one of {PLATFORM_TOPICS}", '
        '"task_type": "one of: knowledge, engage, invite"}\n\n'
        "Make questions practical and help members understand the ecosystem better. "
        "Return ONLY the JSON array, no markdown."
    )

    prompt = (
        f"Generate {data.count} quiz questions about the trading community ecosystem.\n"
        f"Difficulty level: {data.difficulty}/7\n"
        f"Topic focus: {data.topic or 'All platforms'}"
    )

    quizzes = []
    try:
        ai_response = await call_llm(system, prompt, feature="quiz_generation", skip_cache=True)
        clean = ai_response.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
            clean = clean.rsplit("```", 1)[0]

        parsed = json_mod.loads(clean)
        if isinstance(parsed, list):
            for q in parsed[:data.count]:
                quiz = {
                    "id": str(uuid.uuid4()),
                    "question": q.get("question", ""),
                    "correct_answer": q.get("correct_answer", ""),
                    "wrong_answers": q.get("wrong_answers", [])[:3],
                    "explanation": q.get("explanation", ""),
                    "platform_topic": q.get("platform_topic", "Hub"),
                    "task_type": q.get("task_type", "knowledge"),
                    "difficulty": data.difficulty,
                    "status": "pending",
                    "generated_by": user["id"],
                    "approved_by": None,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "published_date": None,
                }
                quizzes.append(quiz)
    except Exception as e:
        logger.error(f"AI quiz generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)[:100]}")

    if quizzes:
        await db.quiz_pool.insert_many([{**q} for q in quizzes])
        # Strip _id for response
        for q in quizzes:
            q.pop("_id", None)

    return {"quizzes": quizzes, "count": len(quizzes)}


@router.get("/admin/pool")
async def admin_get_quiz_pool(
    status: Optional[str] = Query(None),
    topic: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: dict = Depends(require_admin),
):
    """Get quiz pool with optional filtering."""
    db = deps.db
    query = {}
    if status:
        query["status"] = status
    if topic:
        query["platform_topic"] = topic

    total = await db.quiz_pool.count_documents(query)
    quizzes = await db.quiz_pool.find(
        query, {"_id": 0}
    ).sort("created_at", -1).skip((page - 1) * page_size).limit(page_size).to_list(page_size)

    return {"quizzes": quizzes, "total": total, "page": page}


@router.post("/admin/approve")
async def admin_approve_quizzes(data: ApproveQuizRequest, user: dict = Depends(require_master_admin)):
    """Master admin approves quiz questions."""
    db = deps.db
    result = await db.quiz_pool.update_many(
        {"id": {"$in": data.quiz_ids}, "status": "pending"},
        {"$set": {
            "status": "approved",
            "approved_by": user["id"],
            "approved_at": datetime.now(timezone.utc).isoformat(),
        }}
    )
    return {"approved": result.modified_count}


@router.post("/admin/reject")
async def admin_reject_quizzes(data: RejectQuizRequest, user: dict = Depends(require_admin)):
    """Admin rejects quiz questions."""
    db = deps.db
    result = await db.quiz_pool.update_many(
        {"id": {"$in": data.quiz_ids}, "status": {"$in": ["pending", "approved"]}},
        {"$set": {
            "status": "rejected",
            "rejected_by": user["id"],
            "rejection_reason": data.reason,
            "rejected_at": datetime.now(timezone.utc).isoformat(),
        }}
    )
    return {"rejected": result.modified_count}


@router.put("/admin/edit/{quiz_id}")
async def admin_edit_quiz(quiz_id: str, data: EditQuizRequest, user: dict = Depends(require_admin)):
    """Admin edits a quiz question. After saving, AI verifies the edit is coherent."""
    from services.ai_service import call_llm
    db = deps.db

    quiz = await db.quiz_pool.find_one({"id": quiz_id}, {"_id": 0})
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Build update fields from non-None values
    updates = {}
    if data.question is not None:
        updates["question"] = data.question
    if data.correct_answer is not None:
        updates["correct_answer"] = data.correct_answer
    if data.wrong_answers is not None:
        updates["wrong_answers"] = data.wrong_answers
    if data.explanation is not None:
        updates["explanation"] = data.explanation
    if data.platform_topic is not None:
        updates["platform_topic"] = data.platform_topic
    if data.task_type is not None:
        updates["task_type"] = data.task_type
    if data.difficulty is not None:
        updates["difficulty"] = data.difficulty

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Merge edits with existing quiz for verification
    merged = {**quiz, **updates}

    # AI Verification: quick check that the edited quiz is coherent
    verification = {"verified": True, "note": ""}
    try:
        system = (
            "You are a quiz quality checker. Verify that the quiz question is coherent, "
            "the correct answer actually answers the question correctly, the wrong answers "
            "are plausible but incorrect, and the explanation matches the correct answer. "
            "Respond with JSON: {\"valid\": true/false, \"issues\": \"brief description if invalid, empty if valid\"}"
        )
        prompt = (
            f"Question: {merged['question']}\n"
            f"Correct Answer: {merged['correct_answer']}\n"
            f"Wrong Answers: {merged.get('wrong_answers', [])}\n"
            f"Explanation: {merged.get('explanation', '')}"
        )
        ai_resp = await call_llm(system, prompt, feature="quiz_generation", skip_cache=True)
        clean = ai_resp.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
            clean = clean.rsplit("```", 1)[0]
        import json as json_mod
        result = json_mod.loads(clean)
        verification["verified"] = result.get("valid", True)
        verification["note"] = result.get("issues", "")
    except Exception as e:
        verification["note"] = f"AI verification skipped: {str(e)[:80]}"

    updates["edited_by"] = user["id"]
    updates["edited_at"] = datetime.now(timezone.utc).isoformat()
    updates["ai_verification"] = verification

    # If quiz was already approved, reset to pending so master admin re-reviews
    if quiz.get("status") == "approved" and not verification["verified"]:
        updates["status"] = "pending"

    await db.quiz_pool.update_one({"id": quiz_id}, {"$set": updates})

    # Also update in daily_quizzes if already published
    publish_updates = {k: v for k, v in updates.items()
                       if k in ("question", "correct_answer", "wrong_answers", "explanation", "platform_topic", "task_type", "difficulty")}
    if publish_updates:
        await db.daily_quizzes.update_many({"quiz_id": quiz_id}, {"$set": publish_updates})

    return {
        "success": True,
        "quiz_id": quiz_id,
        "verification": verification,
        "updated_fields": list(updates.keys()),
    }


@router.post("/admin/publish")
async def admin_publish_quizzes(data: PublishQuizRequest, user: dict = Depends(require_admin)):
    """Publish approved quizzes as today's (or a specific date's) tasks."""
    db = deps.db
    target_date = data.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Only approved quizzes can be published
    quizzes = await db.quiz_pool.find(
        {"id": {"$in": data.quiz_ids}, "status": "approved"}, {"_id": 0}
    ).to_list(20)

    if not quizzes:
        raise HTTPException(status_code=400, detail="No approved quizzes found in the selection.")

    # Clear any existing published quizzes for this date
    await db.daily_quizzes.delete_many({"date": target_date})

    published = []
    for q in quizzes:
        daily = {
            "id": str(uuid.uuid4()),
            "quiz_id": q["id"],
            "date": target_date,
            "question": q["question"],
            "correct_answer": q["correct_answer"],
            "wrong_answers": q["wrong_answers"],
            "explanation": q["explanation"],
            "platform_topic": q.get("platform_topic", "Hub"),
            "task_type": q.get("task_type", "knowledge"),
            "difficulty": q.get("difficulty", 1),
            "published_by": user["id"],
            "published_at": datetime.now(timezone.utc).isoformat(),
        }
        published.append(daily)

    if published:
        await db.daily_quizzes.insert_many([{**p} for p in published])
        # Mark source quizzes as published
        await db.quiz_pool.update_many(
            {"id": {"$in": [q["id"] for q in quizzes]}},
            {"$set": {"published_date": target_date}}
        )
        # Strip _id
        for p in published:
            p.pop("_id", None)

    return {"published": len(published), "date": target_date, "quizzes": published}


@router.get("/admin/published")
async def admin_get_published(
    date: Optional[str] = Query(None),
    user: dict = Depends(require_admin),
):
    """Get published quizzes for a date (defaults to today)."""
    db = deps.db
    target_date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    quizzes = await db.daily_quizzes.find(
        {"date": target_date}, {"_id": 0}
    ).to_list(20)
    return {"quizzes": quizzes, "date": target_date}


# ─── Member: Quiz Tasks ───

@router.get("/today")
async def get_todays_quizzes(user: dict = Depends(get_current_user)):
    """Get today's published quizzes for the member + their answer status."""
    db = deps.db
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    quizzes = await db.daily_quizzes.find(
        {"date": today}, {"_id": 0}
    ).to_list(20)

    # Get user's answers for today
    answers = await db.quiz_responses.find(
        {"user_id": user["id"], "date": today}, {"_id": 0}
    ).to_list(20)
    answer_map = {a["quiz_id"]: a for a in answers}

    result = []
    for q in quizzes:
        user_answer = answer_map.get(q["id"])
        # Shuffle answers for display (don't reveal correct answer position)
        all_answers = [q["correct_answer"]] + q.get("wrong_answers", [])
        import random
        random.shuffle(all_answers)

        entry = {
            "id": q["id"],
            "question": q["question"],
            "options": all_answers,
            "platform_topic": q.get("platform_topic", "Hub"),
            "task_type": q.get("task_type", "knowledge"),
            "difficulty": q.get("difficulty", 1),
            "answered": user_answer is not None,
            "is_correct": user_answer["is_correct"] if user_answer else None,
            "user_answer": user_answer["answer"] if user_answer else None,
            "correct_answer": q["correct_answer"] if user_answer else None,  # Only reveal after answering
            "explanation": q["explanation"] if user_answer else None,
        }
        result.append(entry)

    total_answered = sum(1 for r in result if r["answered"])
    total_correct = sum(1 for r in result if r.get("is_correct"))

    return {
        "quizzes": result,
        "date": today,
        "total": len(result),
        "answered": total_answered,
        "correct": total_correct,
        "all_done": total_answered == len(result) and len(result) > 0,
    }


@router.post("/{quiz_id}/answer")
async def answer_quiz(quiz_id: str, data: AnswerQuizRequest, user: dict = Depends(get_current_user)):
    """Submit an answer for a quiz question."""
    db = deps.db
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Get the quiz
    quiz = await db.daily_quizzes.find_one({"id": quiz_id, "date": today}, {"_id": 0})
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found for today")

    # Check if already answered
    existing = await db.quiz_responses.find_one({
        "user_id": user["id"], "quiz_id": quiz_id, "date": today
    })
    if existing:
        raise HTTPException(status_code=400, detail="Already answered this question")

    is_correct = data.answer.strip() == quiz["correct_answer"].strip()

    response = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "quiz_id": quiz_id,
        "date": today,
        "answer": data.answer,
        "is_correct": is_correct,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.quiz_responses.insert_one({**response})

    # Award bonus points for correct answer
    correct_bonus = None
    if is_correct:
        try:
            from utils.rewards_engine import award_points, check_and_award_badges
            await award_points(db, user["id"], QUIZ_CORRECT_POINTS, "quiz_correct", {
                "quiz_id": quiz_id,
                "date": today,
                "question": quiz["question"][:80],
            })
            correct_bonus = QUIZ_CORRECT_POINTS
            # Increment quiz stats for badge tracking
            await db.rewards_stats.update_one(
                {"user_id": user["id"]},
                {"$inc": {"quiz_correct_count": 1}},
                upsert=True,
            )
            # Check for newly earned badges
            new_badges = await check_and_award_badges(db, user["id"])
            if new_badges:
                logger.info(f"User {user['id']} earned badges: {new_badges}")
        except Exception as e:
            logger.warning(f"Failed to award quiz correct bonus: {e}")

    # Check if all quizzes for today are now answered
    total_quizzes = await db.daily_quizzes.count_documents({"date": today})
    total_answered = await db.quiz_responses.count_documents({"user_id": user["id"], "date": today})
    all_done = total_answered >= total_quizzes and total_quizzes > 0

    # Award habit streak points if all quizzes done
    reward_info = None
    if all_done:
        try:
            from routes.referral_routes import _award_habit_points
            reward_info = await _award_habit_points(user["id"])
        except Exception as e:
            logger.warning(f"Failed to award quiz completion points: {e}")

    return {
        "is_correct": is_correct,
        "correct_answer": quiz["correct_answer"],
        "explanation": quiz["explanation"],
        "all_done": all_done,
        "reward": reward_info,
        "correct_bonus": correct_bonus,
    }
