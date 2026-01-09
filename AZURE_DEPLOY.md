# Déploiement sur Azure (15h restantes)

## 🎯 Objectif
Déployer l'application sur **Azure App Service** (Gratuit avec Student Pack) pour la rendre accessible publiquement.

---

## Étape 1 : Préparer Azure

1. Connectez-vous sur [Azure Portal](https://portal.azure.com)
2. Cherchez **"App Services"**
3. Cliquez sur **+ Create** → **Web App**

## Étape 2 : Configurer la Web App

Remplissez le formulaire :
- **Subscription** : Azure for Students
- **Resource Group** : Créer nouveau (ex: `rg-webanalytics`)
- **Name** : `web-analytics-asmae-demo` (choisir un nom unique)
- **Publish** : Code
- **Runtime stack** : **Python 3.11**
- **Operating System** : **Linux**
- **Region** : France Central (ou plus proche)
- **Pricing Plan** : Sélectionnez **Free F1** (ou Basic B1 si F1 indisponible)

Cliquez sur **Review + create** puis **Create**.

## Étape 3 : Configurer le Démarrage

Une fois la ressource créée, allez dans la ressource :
1. Menu de gauche → **Settings** → **Configuration**
2. Onglet **General settings**
3. **Startup Command** : 
   ```bash
   python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
   ```
4. Cliquez sur **Save**.

## Étape 4 : Déployer le Code

Méthode la plus simple (Local Git) :
1. Menu de gauche → **Deployment** → **Deployment Center**
2. **Source** : **Local Git**
3. Cliquez sur **Save**
4. Copiez l'URL **Git Clone Uri**
5. Allez dans l'onglet **Local Git/FTPS credentials** et configurez un User/Password (ou utilisez les User scopes).

Dans votre terminal local (VS Code) :
```bash
# Ajouter le remote Azure
git remote add azure <COLLER_LIEN_GIT_CLONE_URI_ICI>

# Déployer
git push azure main
```

## Étape 5 : Variables d'Environnement

Dans Azure Portal → **Settings** → **Environment variables** :
Ajoutez :
- `MONGODB_URL`: Si vous aviez une base cloud.
  > ⚠️ **Important pour la démo 15h** : Sans MongoDB Atlas (Cloud), l'app web affichera le dashboard mais les données seront vides.
  > **Recommandation** : Utilisez le déploiement Azure pour prouver que vous savez le faire ("Scalability"), mais faites la **démo fonctionnelle** sur votre machine locale (Localhost) avec Ollama et MongoDB local.

---

## ⚠️ Architecture Hybride (Cloud + Edge)

Pour le jury, expliquez cette architecture :
1. **Azure App Service** : Héberge le Front/Back pour l'accessibilité globale.
2. **Local Edge (Votre PC)** : Fait tourner le LLM (Ollama) et le Crawler pour la performance et la confidentialité des données (pas de coût GPU cloud).
3. **Avantage** : "Zero Cost Inference" grâce à l'Edge Computing.

C'est un argument MASSIF pour l'Imagine Cup ("Sustainable AI").

---

## ⏱️ Temps estimé
- Création App Service : 10 min
- Déploiement Code : 10 min

**Total : 20 min**
