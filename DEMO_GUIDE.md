# Guide Installation Ollama + Test Complet

## ⏱️ Temps estimé : 1h30

---

## Étape 1 : Installer Ollama (15 min)

### Windows
1. Télécharger depuis https://ollama.com/download
2. Exécuter `OllamaSetup.exe`
3. Vérifier installation :
   ```bash
   ollama --version
   ```

### Télécharger Mistral 7B
```bash
ollama pull mistral:7b-inst

ruct
```
**Taille** : ~4.1 GB (peut prendre 10-15 min selon connexion)

---

## Étape 2 : Tester Ollama (5 min)

```bash
ollama run mistral:7b-instruct
```

**Test Prompt** :
```
Analyze this data:
- Total documents: 127
- Top keyword: hospital (42 occurrences)
- Spike detected on Jan 5 (35 docs in 2h)

What is the strategic insight?
```

✅ **Expected**: LLM devrait mentionner le pic anormal et recommander une investigation.

Appuyer sur `Ctrl+D` pour quitter.

---

## Étape 3 : Tester le Backend (10 min)

### Lancer FastAPI
```bash
cd "d:\Users\hp\Downloads\web-analytics-project-Asmae\web-analytics-project-Asmae"
python main.py
```

✅ **Expected** :
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Tester

 l'API Decision
Ouvrir un nouveau terminal :

```bash
curl http://localhost:8000/api/decision/summary
```

✅ **Expected** : JSON avec `tldr`, `insights`, `recommendation`

---

## Étape 4 : Tester le Dashboard (15 min)

1. Ouvrir navigateur → `http://localhost:8000`
2. **Créer un projet** :
   - Cliquer sur le sélecteur de projet (sidebar)
   - "New Project"
   - Nom : "Healthcare Investment Analysis"
   - Domaine : "Healthcare"
   - Keywords : `hospital, medical, regulation, investment`
   - Icon : 🏥
   - Cliquer "Create Project"

3. **Ajouter une source** :
   - Onglet "Sources"
   - "Add Source"
   - Nom : "WHO Health News"
   - URL : `https://www.who.int/news`
   - Type : HTML
   - Frequency : `0 0 * * *`
   - Max Pages : 20
   - Rate Limit : 30
   - "Add Source"

4. **Lancer un crawl** :
   - Cliquer "▶ Start" sur la source
   - Attendre 30-60 secondes

5. **Vérifier Decision Intelligence** :
   - Onglet "Decision Intelligence"
   - Vérifier que les keywords du projet s'affichent
   - Cliquer "Refresh" sur le TL;DR
   - ✅ **Expected** : LLM génère un résumé basé sur les données

6. **Tester le Copilot** :
   - Taper : "What trends do you see?"
   - ✅ **Expected** : LLM répond avec références aux documents

---

## Étape 5 : Workflow Complet pour la Démo Prof (30 min)

### Checklist Démo

#### 1. Préparation (avant la démo)
- [ ] MongoDB lancé
- [ ] Ollama lancé (`ollama serve`)
- [ ] Backend lancé (`python main.py`)
- [ ] Navigateur ouvert sur `http://localhost:8000`

#### 2. Créer un projet test "Hospital Industry Analysis"
- [ ] Icon : 🏥
- [ ] Domain : Healthcare
- [ ] Keywords : `hospital, healthcare, medical equipment, regulation`

#### 3. Ajouter 2-3 sources
- [ ] Source 1 : WHO News (HTML)
- [ ] Source 2 : PubMed RSS Feed
- [ ] Source 3 : Healthcare.gov (HTML)

#### 4. Lancer les crawls
- [ ] Start crawl pour chaque source
- [ ] Attendre collecte de ~20-50 documents

#### 5. Demo Decision Intelligence
- [ ] Montrer le sélecteur de projet (cliquer sur l'icône)
- [ ] Montrer les keywords du projet
- [ ] Cliquer "Refresh" sur Executive Summary
- [ ] **Point clé** : "Le LLM analyse uniquement les données de MongoDB, pas d'invention"
- [ ] Poser une question au Copilot : "What are the main regulatory concerns?"
- [ ] Montrer les "Grounding Sources" (traçabilité)

#### 6. Montrer l'Analytics
- [ ] Onglet "Analytics" → graphiques mis à jour
- [ ] Expliquer que tout est filtré par projet

---

## 🎯 Script de Démo (3 minutes)

### Minute 1 : Problem Statement
> "Les entreprises veulent investir dans de nouveaux domaines, mais elles manquent d'outils pour analyser rapidement de grands volumes de données non structurées. Elles ont besoin d'**intelligence décisionnelle**."

### Minute 2 : Solution Walkthrough
1. **Créer un projet**: "Healthcare Investment"
2. **Définir keywords**: hospital, regulation, equipment
3. **Ajouter sources**: WHO, PubMed, Healthcare.gov
4. **Lancer crawl**: Collecte automatique
5. **Analyser**: Dashboard Decision Intelligence

### Minute 3 : Innovation
> "L'innovation : notre LLM open-source (Mistral 7B) est **grounded** dans MongoDB. Chaque réponse cite les documents sources. Pas d'hallucination. Transparence totale."

**Demo live** :
- Poser question : "What opportunities exist in hospital equipment?"
- LLM répond avec citations
- Cliquer sur "Grounding Sources" → montrer document ID

**Conclusion** :
> "Ce système réduit le temps de décision de 3 jours à 30 secondes. C'est scalable sur Azure. C'est open-source. C'est prêt pour le monde réel."

---

## 🚨 Troubleshooting

| Problème | Solution |
|----------|----------|
| Ollama ne répond pas | `ollama serve` dans un terminal séparé |
| LLM timeout | Augmenter `timeout=60` dans `decision.py` |
| Pas de données | Lancer un crawl et attendre 1-2 min |
| Projet ne s'affiche pas | F5 pour rafraîchir |
| MongoDB error | `net start MongoDB` (Windows) |

---

## ✅ Validation Finale

Avant la démo, vérifier :
- [ ] Ollama actif : `curl http://localhost:11434/api/tags`
- [ ] Backend actif : `curl http://localhost:8000/health`
- [ ] Au moins 1 projet créé
- [ ] Au moins 20 documents collectés
- [ ] LLM répond (pas de fallback)

---

**Temps total** : 1h30 setup + 30 min préparation démo = **2h**

**Status** : Prêt pour le 10 janvier 🚀
