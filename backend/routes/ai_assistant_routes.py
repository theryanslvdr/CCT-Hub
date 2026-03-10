"""AI Assistant routes — RyAI (technical/safeguard) & zxAI (knowledge/encouragement) chatbots.
Uses OpenRouter with the existing API key for the cheapest model.
Supports multi-turn conversations, admin training, active learning, and escalation."""

import os
import httpx
import logging
from datetime import datetime, timezone
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

import deps
from deps import get_current_user, require_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai-assistant", tags=["AI Assistant"])

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-4o-mini"

# ── Default AI Personality Configs ──────────────────────────────
DEFAULT_ASSISTANTS = [
    {
        "assistant_id": "ryai",
        "display_name": "RyAI",
        "tagline": "Technical & Safeguard Intelligence",
        "system_prompt": (
            "You are RyAI, the technical and safeguard intelligence for the CrossCurrent Finance Hub. "
            "Your primary role is to help members understand how to use the platform correctly, "
            "ensure they follow proper trading procedures, and prevent any form of cheating or misuse. "
            "You are precise, factual, and security-minded. You speak with authority but remain approachable. "
            "You never give generic internet advice — only platform-specific guidance."
        ),
        "personality": "Professional, precise, security-focused. Uses clear technical language. Firm but helpful.",
        "greeting": "Hello! I'm RyAI, your technical guide. I can help you navigate the platform, answer questions about features, and make sure you're getting the most out of CrossCurrent. What can I help with?",
        "model": DEFAULT_MODEL,
        "icon": "shield",
        "color": "#F97316",
    },
    {
        "assistant_id": "zxai",
        "display_name": "zxAI",
        "tagline": "Knowledge & Encouragement Engine",
        "system_prompt": (
            "You are zxAI, the knowledge base and encouragement engine for the CrossCurrent Finance Hub. "
            "Your role is to educate members about the importance and benefits of trading with CrossCurrent, "
            "encourage them to stay disciplined with their trading habits, and provide motivational support. "
            "You are warm, encouraging, and knowledgeable. You celebrate members' achievements and guide them "
            "through challenges. You never give generic financial advice — only CrossCurrent-specific education."
        ),
        "personality": "Warm, encouraging, motivational. Celebrates achievements. Uses positive reinforcement.",
        "greeting": "Hey there! I'm zxAI, your knowledge companion. I'm here to help you understand the amazing benefits of trading with CrossCurrent and keep you motivated on your journey. What's on your mind?",
        "model": DEFAULT_MODEL,
        "icon": "sparkles",
        "color": "#10B981",
    },
]


# ── Request / Response Models ───────────────────────────────────
class ChatRequest(BaseModel):
    assistant_id: str  # "ryai" or "zxai"
    message: str
    session_id: Optional[str] = None


class TrainRequest(BaseModel):
    assistant_id: str
    category: str
    question: str
    answer: str


class AdminAnswerRequest(BaseModel):
    answer: str


class UpdateAssistantConfig(BaseModel):
    display_name: Optional[str] = None
    system_prompt: Optional[str] = None
    personality: Optional[str] = None
    greeting: Optional[str] = None
    model: Optional[str] = None
    tagline: Optional[str] = None


# ── Helper Functions ────────────────────────────────────────────

async def ensure_assistants_exist():
    """Seed default assistant configs if they don't exist."""
    db = deps.db
    for a in DEFAULT_ASSISTANTS:
        existing = await db.ai_assistants.find_one({"assistant_id": a["assistant_id"]})
        if not existing:
            await db.ai_assistants.insert_one({
                **a,
                "active_learning": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })


async def get_assistant_config(assistant_id: str):
    """Get assistant config from DB."""
    db = deps.db
    config = await db.ai_assistants.find_one(
        {"assistant_id": assistant_id}, {"_id": 0}
    )
    return config


async def build_context(assistant_id: str, session_id: str, user_message: str):
    """Build conversation context including knowledge base and chat history."""
    db = deps.db
    config = await get_assistant_config(assistant_id)
    if not config:
        return None, None

    # Get knowledge base entries (relevant training data)
    knowledge_entries = []
    knowledge_cursor = db.ai_knowledge.find(
        {"assistant_id": assistant_id},
        {"_id": 0, "question": 1, "answer": 1, "category": 1}
    ).sort("created_at", -1).limit(50)
    async for entry in knowledge_cursor:
        knowledge_entries.append(entry)

    # Build enhanced system prompt with knowledge base
    system_prompt = config.get("system_prompt", "")
    if knowledge_entries:
        kb_text = "\n\n--- KNOWLEDGE BASE (Use this to answer questions) ---\n"
        for entry in knowledge_entries:
            kb_text += f"Q: {entry['question']}\nA: {entry['answer']}\n\n"
        system_prompt += kb_text

    system_prompt += (
        "\n\n--- INSTRUCTIONS ---\n"
        "1. Always answer based on the knowledge base and CrossCurrent-specific information.\n"
        "2. If you don't know the answer or it's outside your training, respond EXACTLY with: "
        "[ESCALATE] followed by a brief explanation of what you need help with.\n"
        "3. Keep responses concise and helpful.\n"
        "4. Never provide generic financial advice. Only CrossCurrent-specific guidance.\n"
    )

    # Get chat history for the session
    messages = [{"role": "system", "content": system_prompt}]

    if session_id:
        history_cursor = db.ai_messages.find(
            {"session_id": session_id}
        ).sort("created_at", 1).limit(20)
        async for msg in history_cursor:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

    messages.append({"role": "user", "content": user_message})
    return config, messages


async def call_openrouter(messages: list, model: str, max_tokens: int = 500):
    """Make the OpenRouter API call."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return None

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.4,
                    "max_tokens": max_tokens,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"OpenRouter AI Assistant call failed: {e}")
        return None


# ── User Endpoints ──────────────────────────────────────────────

@router.get("/assistants")
async def list_assistants(user=Depends(get_current_user)):
    """List available AI assistants."""
    await ensure_assistants_exist()
    db = deps.db
    assistants = []
    async for a in db.ai_assistants.find({}, {"_id": 0}):
        assistants.append(a)
    return {"assistants": assistants}


@router.post("/chat")
async def chat(req: ChatRequest, user=Depends(get_current_user)):
    """Send a message to an AI assistant."""
    await ensure_assistants_exist()
    db = deps.db
    user_id = user.get("id", "")

    # Create or get session
    session_id = req.session_id
    if not session_id:
        session_doc = {
            "user_id": user_id,
            "assistant_id": req.assistant_id,
            "title": req.message[:60] + ("..." if len(req.message) > 60 else ""),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        result = await db.ai_sessions.insert_one(session_doc)
        session_id = str(result.inserted_id)

    # Build context with knowledge base and history
    config, messages = await build_context(req.assistant_id, session_id, req.message)
    if not config:
        raise HTTPException(status_code=404, detail="Assistant not found")

    # Save user message
    await db.ai_messages.insert_one({
        "session_id": session_id,
        "role": "user",
        "content": req.message,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    # Call LLM
    model = config.get("model", DEFAULT_MODEL)
    ai_response = await call_openrouter(messages, model)

    if not ai_response:
        ai_response = "I'm sorry, I'm having trouble connecting right now. Please try again in a moment."

    # Check if AI escalated
    escalated = False
    if "[ESCALATE]" in ai_response:
        escalated = True
        # Store unanswered question for admin
        await db.ai_unanswered.insert_one({
            "assistant_id": req.assistant_id,
            "session_id": session_id,
            "question": req.message,
            "user_id": user_id,
            "user_name": user.get("full_name", "Unknown"),
            "status": "pending",
            "ai_attempted_response": ai_response,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        # Clean up the response for user
        ai_response = ai_response.replace("[ESCALATE]", "").strip()
        if not ai_response:
            ai_response = "That's a great question! I've flagged this for our team to provide you with the most accurate answer. Check back soon!"

    # Active learning: store the interaction
    if config.get("active_learning"):
        await db.ai_interactions.insert_one({
            "assistant_id": req.assistant_id,
            "user_id": user_id,
            "question": req.message,
            "response": ai_response,
            "escalated": escalated,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

    # Save assistant message
    await db.ai_messages.insert_one({
        "session_id": session_id,
        "role": "assistant",
        "content": ai_response,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    # Update session timestamp
    await db.ai_sessions.update_one(
        {"_id": ObjectId(session_id)},
        {"$set": {"updated_at": datetime.now(timezone.utc).isoformat()}}
    )

    return {
        "session_id": session_id,
        "response": ai_response,
        "escalated": escalated,
        "assistant_id": req.assistant_id,
    }


@router.get("/sessions")
async def get_sessions(assistant_id: str = None, user=Depends(get_current_user)):
    """Get user's chat sessions."""
    db = deps.db
    user_id = user.get("id", "")
    query = {"user_id": user_id}
    if assistant_id:
        query["assistant_id"] = assistant_id

    sessions = []
    async for s in db.ai_sessions.find(query).sort("updated_at", -1).limit(30):
        sessions.append({
            "id": str(s["_id"]),
            "assistant_id": s.get("assistant_id"),
            "title": s.get("title", "Chat"),
            "created_at": s.get("created_at"),
            "updated_at": s.get("updated_at"),
        })
    return {"sessions": sessions}


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, user=Depends(get_current_user)):
    """Get messages for a specific session."""
    db = deps.db
    messages = []
    async for m in db.ai_messages.find({"session_id": session_id}).sort("created_at", 1):
        messages.append({
            "role": m["role"],
            "content": m["content"],
            "created_at": m.get("created_at"),
        })
    return {"messages": messages}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, user=Depends(get_current_user)):
    """Delete a chat session and its messages."""
    db = deps.db
    await db.ai_messages.delete_many({"session_id": session_id})
    await db.ai_sessions.delete_one({"_id": ObjectId(session_id)})
    return {"status": "deleted"}


@router.get("/popular-prompts")
async def get_popular_prompts(assistant_id: str = "ryai", user=Depends(get_current_user)):
    """Get popular/trending prompts from active learning data."""
    db = deps.db
    pipeline = [
        {"$match": {"assistant_id": assistant_id, "escalated": False}},
        {"$group": {"_id": "$question", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
    ]
    prompts = []
    async for doc in db.ai_interactions.aggregate(pipeline):
        prompts.append({"question": doc["_id"], "count": doc["count"]})
    
    # Also include knowledge base questions as suggestions
    if len(prompts) < 6:
        kb_cursor = db.ai_knowledge.find(
            {"assistant_id": assistant_id},
            {"_id": 0, "question": 1, "category": 1}
        ).limit(10 - len(prompts))
        async for entry in kb_cursor:
            prompts.append({"question": entry["question"], "count": 0, "source": "knowledge"})
    
    return {"prompts": prompts}



# ── Admin Endpoints ─────────────────────────────────────────────

@router.get("/admin/config")
async def get_all_configs(user=Depends(require_admin)):
    """Get all assistant configs for admin."""
    await ensure_assistants_exist()
    db = deps.db
    configs = []
    async for c in db.ai_assistants.find({}, {"_id": 0}):
        configs.append(c)
    return {"assistants": configs}


@router.put("/admin/config/{assistant_id}")
async def update_config(assistant_id: str, req: UpdateAssistantConfig, user=Depends(require_admin)):
    """Update an AI assistant's configuration."""
    db = deps.db
    update = {}
    for field in ["display_name", "system_prompt", "personality", "greeting", "model", "tagline"]:
        val = getattr(req, field)
        if val is not None:
            update[field] = val

    if not update:
        raise HTTPException(status_code=400, detail="No fields to update")

    update["updated_at"] = datetime.now(timezone.utc).isoformat()
    update["updated_by"] = user.get("id", "")

    await db.ai_assistants.update_one(
        {"assistant_id": assistant_id},
        {"$set": update}
    )
    return {"status": "updated"}


@router.get("/admin/knowledge")
async def get_knowledge_base(assistant_id: str = None, user=Depends(require_admin)):
    """Get knowledge base entries."""
    db = deps.db
    query = {}
    if assistant_id:
        query["assistant_id"] = assistant_id

    entries = []
    async for entry in db.ai_knowledge.find(query).sort("created_at", -1).limit(200):
        entries.append({
            "id": str(entry["_id"]),
            "assistant_id": entry.get("assistant_id"),
            "category": entry.get("category"),
            "question": entry.get("question"),
            "answer": entry.get("answer"),
            "added_by": entry.get("added_by"),
            "created_at": entry.get("created_at"),
        })
    return {"entries": entries}


@router.post("/admin/train")
async def add_training_data(req: TrainRequest, user=Depends(require_admin)):
    """Add a knowledge base entry (training data)."""
    db = deps.db
    await db.ai_knowledge.insert_one({
        "assistant_id": req.assistant_id,
        "category": req.category,
        "question": req.question,
        "answer": req.answer,
        "added_by": user.get("full_name", "Admin"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"status": "added"}


@router.delete("/admin/knowledge/{entry_id}")
async def delete_knowledge_entry(entry_id: str, user=Depends(require_admin)):
    """Delete a knowledge base entry."""
    db = deps.db
    await db.ai_knowledge.delete_one({"_id": ObjectId(entry_id)})
    return {"status": "deleted"}


@router.get("/admin/unanswered")
async def get_unanswered(assistant_id: str = None, user=Depends(require_admin)):
    """Get questions the AI couldn't answer."""
    db = deps.db
    query = {"status": "pending"}
    if assistant_id:
        query["assistant_id"] = assistant_id

    items = []
    async for item in db.ai_unanswered.find(query).sort("created_at", -1).limit(100):
        items.append({
            "id": str(item["_id"]),
            "assistant_id": item.get("assistant_id"),
            "question": item.get("question"),
            "user_name": item.get("user_name"),
            "ai_attempted_response": item.get("ai_attempted_response"),
            "status": item.get("status"),
            "created_at": item.get("created_at"),
        })
    return {"items": items}


@router.post("/admin/unanswered/{item_id}/answer")
async def answer_unanswered(item_id: str, req: AdminAnswerRequest, user=Depends(require_admin)):
    """Admin answers an unanswered question — also adds it to the knowledge base for active learning."""
    db = deps.db
    item = await db.ai_unanswered.find_one({"_id": ObjectId(item_id)})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Mark as answered
    await db.ai_unanswered.update_one(
        {"_id": ObjectId(item_id)},
        {"$set": {
            "status": "answered",
            "admin_answer": req.answer,
            "answered_by": user.get("full_name", "Admin"),
            "answered_at": datetime.now(timezone.utc).isoformat(),
        }}
    )

    # Add to knowledge base for active learning
    await db.ai_knowledge.insert_one({
        "assistant_id": item.get("assistant_id"),
        "category": "User Questions",
        "question": item.get("question"),
        "answer": req.answer,
        "added_by": user.get("full_name", "Admin"),
        "source": "escalation",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    return {"status": "answered_and_trained"}


@router.get("/admin/stats")
async def get_ai_stats(user=Depends(require_admin)):
    """Get AI assistant usage stats."""
    db = deps.db
    total_sessions = await db.ai_sessions.count_documents({})
    total_messages = await db.ai_messages.count_documents({})
    pending_unanswered = await db.ai_unanswered.count_documents({"status": "pending"})
    knowledge_count = await db.ai_knowledge.count_documents({})
    total_interactions = await db.ai_interactions.count_documents({})
    escalated_count = await db.ai_interactions.count_documents({"escalated": True})

    return {
        "total_sessions": total_sessions,
        "total_messages": total_messages,
        "pending_unanswered": pending_unanswered,
        "knowledge_entries": knowledge_count,
        "total_interactions": total_interactions,
        "escalated_count": escalated_count,
        "escalation_rate": round(escalated_count / max(total_interactions, 1) * 100, 1),
    }
