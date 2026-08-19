# Real Estate Price Prediction Baseline

Application de prediction de prix immobilier, basee sur un modele scikit-learn sauvegarde avec `joblib`.

Le projet contient :

- une API FastAPI pour les predictions unitaires et batch ;
- une interface Streamlit qui consomme l'API ;
- un notebook d'analyse et d'entrainement ;
- un modele sauvegarde dans `models/`.

## Structure

```text
.
├── api/                         # Routes FastAPI, auth, schemas et utilitaires
├── core/                        # Configuration applicative
├── data/                        # Dataset local ignore par Git
├── models/                      # Modele joblib
├── notebooks/                   # Notebook d'analyse et d'entrainement
├── streamlit/                   # Interface Streamlit
├── tests/                       # Tests API
└── main.py                      # Point d'entree local
```

## Configuration

L'application lit les variables depuis `.env`, l'environnement ou les secrets Streamlit.

Exemple minimal :

```env
SECRET_KEY=tutorealestate
DEMO_MODE=true
REAL_ESTATE_DATA_URL=https://drive.google.com/uc?export=download&id=1EAkMjJW9OGQJPHO-jHsFalIbKjbrQeTB
```

Variables utiles :

- `SECRET_KEY` : mot de passe utilise par `/login`.
- `USERNAME` : identifiant utilisateur, `admin` par defaut.
- `DEMO_MODE` : si `true`, l'API accepte les predictions sans token.
- `API_URL` : URL de l'API consommee par Streamlit.
- `REAL_ESTATE_DATA_URL` : URL du dataset utilise pour l'onglet dataset.

## Lancer l'API

```bash
uvicorn api.app:app --host 127.0.0.1 --port 8000 --reload
```

Documentation interactive :

```text
http://127.0.0.1:8000/docs
```

## Lancer Streamlit

Dans un premier terminal, lancer l'API.

Dans un second terminal :

```bash
streamlit run streamlit/streamlit_app.py
```

Par defaut, l'interface appelle :

```text
http://localhost:8000
```

Sur Streamlit Cloud, ajouter les secrets :

```toml
API_URL = "https://mon-api.example.com"
REAL_ESTATE_DATA_URL = "https://drive.google.com/uc?export=download&id=1EAkMjJW9OGQJPHO-jHsFalIbKjbrQeTB"
```

## Deploiement Streamlit Cloud

Le fichier `streamlit/requirements.txt` contient les dependances necessaires a l'interface Streamlit.

Configuration de deploiement :

- Repository : `GeeksterLab/Real_Estate_Price_Prediction_baseline`
- Branch : `main`
- Main file path : `streamlit/streamlit_app.py`

Le dataset complet `data/realtor-data.csv` est ignore par Git car il depasse la limite GitHub de 100 MB. L'application Streamlit charge le dataset via `REAL_ESTATE_DATA_URL`.

## Routes API

| Methode | Route | Description |
| --- | --- | --- |
| `GET` | `/health` | Statut de l'API |
| `POST` | `/login` | Connexion et creation des tokens |
| `GET` | `/refresh` | Renouvellement des tokens |
| `POST` | `/prediction` | Prediction pour un bien |
| `POST` | `/prediction-batch` | Predictions pour plusieurs biens |
| `POST` | `/upload` | Lecture d'un CSV envoye |
| `GET` | `/model_info` | Informations et metriques du modele |
