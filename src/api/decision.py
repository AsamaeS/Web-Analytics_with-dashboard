from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import requests
from ..storage import db_manager
from ..processing.intelligent_keywords import intelligent_extractor
from datetime import datetime, timedelta

router = APIRouter()

# Ollama Configuration
OLLAMA_API = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "mistral:7b-instruct"

# System prompt for grounding
SYSTEM_PROMPT = """You are an analytical assistant integrated into an intelligent dashboard.
Your role is to analyze structured and semi-structured data, detect trends, anomalies, and risks, and generate concise, decision-oriented insights.
You must explain your reasoning clearly, adapt explanations to non-technical users, and suggest actionable recommendations.
You do not hallucinate data. If information is missing, you explicitly state it.
When citing data, reference document IDs or timestamps provided in the context."""


def call_llm(prompt: str, timeout: int = 60) -> str:
    """
    Send grounded prompt to Mistral via Ollama.
    Falls back to heuristic response if Ollama is unavailable.
    """
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": f"{SYSTEM_PROMPT}\\n\\n{prompt}",
            "stream": False
        }
        
        response = requests.post(OLLAMA_API, json=payload, timeout=timeout)
        
        if response.status_code == 200:
            return response.json().get("response", "LLM response unavailable.")
        else:
            raise Exception(f"Ollama returned status {response.status_code}")
            
    except Exception as e:
        # Fallback to heuristic response if Ollama not available
        print(f"LLM call failed: {e}. Using fallback logic.")
        return generate_fallback_response(prompt)


def generate_fallback_response(prompt: str) -> str:
    """Heuristic fallback when LLM is unavailable."""
    if "spike" in prompt.lower() or "anomaly" in prompt.lower():
        return "Detected volume anomaly. Recommend immediate investigation of contributing sources."
    elif "trend" in prompt.lower():
        return "Emerging trend identified. Monitor keyword evolution over next 48 hours."
    else:
        return "Analysis in progress. Please ensure Ollama is running for full LLM capabilities."


@router.get("/summary")
async def get_decision_summary():
    """
    Generates an executive-level summary grounded in the NoSQL database.
    """
    try:
        # 1. Gather Grounding Data
        global_stats = db_manager.get_global_stats()
        total_docs = global_stats.get("total_documents", 0)
        
        # 2. Get Recent Keywords (Semantic Layer)
        pipeline = [
            {"$project": {"cleaned_text": 1, "crawled_at": 1}},
            {"$sort": {"crawled_at": -1}},
            {"$limit": 50}
        ]
        docs = list(db_manager.documents.aggregate(pipeline))
        combined_text = " ".join([d.get("cleaned_text", "")[:500] for d in docs])  # Limit text length
        
        top_keywords = intelligent_extractor.get_best_keywords(combined_text, top_n=5) if combined_text else []
        keywords_str = ", ".join([k[0] for k in top_keywords]) if top_keywords else "No keywords extracted"
        
        # 3. Count documents in last 24h for trend detection
        last_24h = datetime.utcnow() - timedelta(hours=24)
        recent_count = db_manager.documents.count_documents({"crawled_at": {"$gte": last_24h}})
        
        # 4. Build Grounded Prompt
        grounding_context = f"""Analyze this data:
- Total documents in database: {total_docs}
- Documents collected in last 24 hours: {recent_count}
- Top emerging keywords: {keywords_str}
- Number of active sources: {global_stats.get('total_sources', 0)}

Provide a 2-sentence executive summary highlighting the most critical insight for decision-makers."""
        
        # 5. Call LLM
        llm_tldr = call_llm(grounding_context, timeout=30)
        
        # 6. Generate Insights (can also use LLM for each)
        insights = [
            {
                "type": "trend",
                "text": f"Primary focus detected: {top_keywords[0][0] if top_keywords else 'diverse topics'}",
                "confidence": 0.92
            },
            {
                "type": "risk",
                "text": "Data concentration risk: verify source diversity to avoid narrative bias.",
                "confidence": 0.85
            }
        ]
        
        summary = {
            "title": "Executive Intelligence Briefing",
            "timestamp": datetime.now().isoformat(),
            "status": "ACTIVE" if recent_count > 0 else "STALE",
            "tldr": llm_tldr,
            "insights": insights,
            "recommendation": "Monitor keyword evolution. Expand source coverage if concentration exceeds 60%."
        }
        
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")


@router.post("/chat")
async def decision_chat(query: Dict[str, str]):
    """
    Copilot-like Q&A grounded in the database.
    """
    user_msg = query.get("message", "").lower()
    
    if not user_msg:
        return {"text": "Please ask a question.", "grounding_sources": []}
    
    # 1. Search for grounding documents (simple keyword match)
    search_results = db_manager.search_documents(
        db_manager.SearchQuery(keywords=user_msg, limit=5)
    )
    
    # 2. Build grounding context
    if search_results:
        grounding_docs = "\\n".join([
            f"- Document {i+1}: {r.snippet}" 
            for i, r in enumerate(search_results[:3])
        ])
        sources = [{"title": r.title or "Untitled", "id": r.document_id} for r in search_results[:3]]
    else:
        grounding_docs = "No matching documents found in database."
        sources = []
    
    # 3. Construct prompt
    llm_prompt = f"""User question: "{user_msg}"

Grounding data from NoSQL database:
{grounding_docs}

Provide a concise answer based ONLY on the grounding data above. If the data doesn't answer the question, say so explicitly."""
    
    # 4. Get LLM response
    llm_response = call_llm(llm_prompt, timeout=30)
    
    response = {
        "text": llm_response,
        "grounding_sources": sources,
        "suggestion": "Would you like me to analyze this trend over a longer timeframe?"
    }
    
    return response
