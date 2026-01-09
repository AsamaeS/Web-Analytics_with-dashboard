# LLM Integration Guide – Mistral 7B via Ollama

**Goal**: Connect the Decision Intelligence backend to a local/Azure LLM for grounded reasoning.

---

## 📥 Step 1: Install Ollama (Development)

### Windows
```powershell
# Download installer from https://ollama.com/download
# Or use PowerShell:
Invoke-WebRequest -Uri "https://ollama.com/download/OllamaSetup.exe" -OutFile "OllamaSetup.exe"
.\OllamaSetup.exe
```

### Verify Installation
```bash
ollama --version
```

---

## 🚀 Step 2: Download Mistral 7B Instruct

```bash
ollama pull mistral:7b-instruct
```

This downloads ~4.1 GB. First run may take 5-10 minutes.

---

## 🧪 Step 3: Test LLM Locally

```bash
ollama run mistral:7b-instruct
```

**Test Prompt**:
```
Analyze the following data: 
- 120 documents collected in the last 7 days
- Top keyword: "regulation" (42 occurrences)
- Anomaly detected on Jan 5 (spike of 35 docs)

What strategic insight can you provide?
```

Expected response should mention regulatory trends and recommend deeper analysis of the Jan 5 spike.

Press `Ctrl+D` to exit.

---

## 🔌 Step 4: Connect FastAPI to Ollama

Update `src/api/decision.py`:

```python
import requests

OLLAMA_API = "http://localhost:11434/api/generate"

def call_llm(prompt: str) -> str:
    """Send grounded prompt to Mistral via Ollama."""
    payload = {
        "model": "mistral:7b-instruct",
        "prompt": prompt,
        "stream": False
    }
    
    response = requests.post(OLLAMA_API, json=payload, timeout=60)
    
    if response.status_code == 200:
        return response.json().get("response", "")
    else:
        return "LLM unavailable."

# Usage in /summary endpoint:
grounding_context = f"""
You are an analytical assistant.
Analyze this data:
- Total documents: {total_docs}
- Top keywords: {keywords_str}
- Recent activity: {recent_trend}

Provide a 2-sentence executive summary.
"""

lldr_text = call_llm(grounding_context)
```

---

## ☁️ Step 5: Azure Deployment (Production)

### Option A: Azure VM with Ollama

1. **Create VM**:
   - Size: `Standard_D4s_v3` (4 vCPU, 16 GB RAM)
   - OS: Ubuntu 22.04 LTS
   - Enable HTTP/HTTPS inbound

2. **Install Ollama on VM**:
   ```bash
   ssh azureuser@<vm-ip>
   curl -fsSL https://ollama.com/install.sh | sh
   ollama serve &
   ollama pull mistral:7b-instruct
   ```

3. **Update Backend Config**:
   ```python
   OLLAMA_API = "http://<vm-ip>:11434/api/generate"
   ```

### Option B: Azure OpenAI (Fallback/Comparison)

If Ollama setup fails, use Azure OpenAI as a **fallback** (not replacement):
- Model: `gpt-4o-mini` or `gpt-35-turbo`
- Justification: "We compare open-source vs commercial LLMs for transparency analysis."

---

## 🛡️ System Prompt (Grounding Template)

Store in `src/prompts/system.txt`:

```
You are an analytical assistant integrated into an intelligent dashboard.
Your role is to analyze structured and semi-structured data, detect trends, anomalies, and risks, and generate concise, decision-oriented insights.
You must explain your reasoning clearly, adapt explanations to non-technical users, and suggest actionable recommendations.
You do not hallucinate data. If information is missing, you explicitly state it.

When citing data, reference document IDs or timestamps provided in the context.
```

---

## ✅ Validation Steps

1. **Test Ollama API**:
   ```bash
   curl http://localhost:11434/api/generate -d '{
     "model": "mistral:7b-instruct",
     "prompt": "What is LLM grounding?",
     "stream": false
   }'
   ```

2. **Test Decision Endpoint**:
   ```bash
   curl http://localhost:8000/api/decision/summary
   ```

   Expected: JSON with `tldr`, `insights`, `recommendation`.

3. **Test Copilot Chat**:
   - Go to dashboard → Decision Intelligence tab
   - Type: "What are the top trends?"
   - Verify response is grounded in MongoDB data

---

## 🎯 Demo Script for Judges

**Setup** (hidden from audience):
- MongoDB populated with 100+ test documents
- Ollama running in background
- Dashboard open to Decision Intelligence tab

**Live Demo**:
1. **Show TL;DR**: "The system analyzed 127 documents and detected a regulatory surge."
2. **Click Signal Radar**: Highlight the Jan 5 anomaly.
3. **Ask Copilot**: "Why did volume spike on January 5?"
4. **Show Response**: LLM cites documents #42, #57, #68 related to "new policy announcement."
5. **Explain**: "This is not generic AI—it's grounded in our NoSQL truth."

---

## 🚨 Troubleshooting

| Issue | Solution |
|-------|----------|
| Ollama not responding | `ollama serve` (ensure service is running) |
| Slow LLM responses | Reduce context length, use `mistral:7b` (not larger model) |
| FastAPI timeout | Increase `timeout=120` in `requests.post()` |
| Azure VM cost concerns | Use `Standard_B2s` for demo only (stop after presentation) |

---

**Status**: Ready for integration. Estimated time: 2-3 hours.
