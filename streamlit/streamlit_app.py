"""
Estate Lens — interface Streamlit pour l'API FastAPI de prédiction immobilière.

- Onglet "Estimation" → estimation du prix d'un bien
- Onglet "Batch"      → prédictions en masse depuis un CSV
- Onglet "Modèle"     → informations et métriques du modèle

API attendue :
- POST /login
- GET  /refresh
- POST /prediction
- POST /prediction-batch
- GET  /model_info
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import requests
import streamlit as st
import plotly.graph_objects as go
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATASET_PATH = PROJECT_ROOT / "data" / "realtor-data.csv"


def read_local_env_value(name: str) -> str:
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return ""

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        if key.strip() == name:
            return value.strip().strip('"').strip("'")

    return ""


def get_config_value(name: str) -> str:
    try:
        secret_value = st.secrets.get(name)
    except (KeyError, FileNotFoundError):
        secret_value = None

    value = secret_value or os.getenv(name) or read_local_env_value(name)
    return str(value) if value else ""


def get_dataset_source() -> str:
    return get_config_value("REAL_ESTATE_DATA_URL") or str(DATASET_PATH)


# ╔════════════════════════════════════════════════════════════╗
# ║ ⚙️ CONFIG
# ╚════════════════════════════════════════════════════════════╝
st.set_page_config(
    page_title="Estate Lens",
    page_icon="🏡",
    layout="wide",
)

REQUIRED_COLUMNS = ["bed", "bath", "city", "state", "house_size", "prev_sold_year"]

# Palette "real estate premium" : ardoise + ivoire + cuivre
BG = "#0f1720"
PANEL = "#17212b"
PANEL_SOFT = "#1d2a35"
TEXT = "#f4efe6"
MUTED = "#a9b0b7"
ACCENT = "#c9894b"
ACCENT_LIGHT = "#e8b77f"
ACCENT_SAFE = "#34d399"
ACCENT_BRAND = "#38bdf8"
SUCCESS = "#7db89d"
BORDER = "rgba(232, 183, 127, 0.18)"


def default_api_url() -> str:
    try:
        return st.secrets["API_URL"]
    except (KeyError, FileNotFoundError):
        return os.environ.get("API_URL", "http://localhost:8000")


# ╔════════════════════════════════════════════════════════════╗
# ║ 🎨 STYLE
# ╚════════════════════════════════════════════════════════════╝
def inject_css():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

        html, body, [class*="css"] {{
            font-family: 'DM Sans', sans-serif;
        }}

        .stApp {{
            background:
                linear-gradient(rgba(15,23,32,.92), rgba(15,23,32,.96)),
                radial-gradient(circle at 85% 10%, rgba(201,137,75,.18), transparent 28%),
                radial-gradient(circle at 10% 75%, rgba(125,184,157,.10), transparent 25%);
            color: {TEXT};
        }}

        header[data-testid="stHeader"] {{
            background: transparent;
        }}

        #MainMenu, footer {{
            visibility: hidden;
        }}

        section[data-testid="stSidebar"] {{
            background: rgba(18, 27, 36, 0.97);
            border-right: 1px solid {BORDER};
        }}

        .estate-title {{
            font-family: 'Playfair Display', serif;
            font-size: 3.05rem;
            line-height: 1;
            color: {TEXT};
            margin-bottom: .3rem;
        }}

        .estate-subtitle {{
            color: {MUTED};
            font-size: 1rem;
            margin-bottom: 1.5rem;
        }}

        .eyebrow {{
            color: {ACCENT_LIGHT};
            text-transform: uppercase;
            letter-spacing: .17em;
            font-size: .72rem;
            font-weight: 700;
            margin-bottom: .7rem;
        }}

        .property-card {{
            background:
                linear-gradient(145deg, rgba(255,255,255,.055), rgba(255,255,255,.025));
            border: 1px solid {BORDER};
            border-radius: 22px;
            padding: 1.5rem 1.6rem;
            box-shadow: 0 16px 45px rgba(0,0,0,.18);
        }}

        .price-card {{
            background:
                linear-gradient(135deg, rgba(201,137,75,.20), rgba(201,137,75,.07));
            border: 1px solid rgba(232,183,127,.28);
            border-radius: 24px;
            padding: 2rem;
            text-align: center;
        }}

        .price-label {{
            color: {MUTED};
            text-transform: uppercase;
            font-size: .72rem;
            letter-spacing: .14em;
            font-weight: 700;
        }}

        .price-value {{
            font-family: 'Playfair Display', serif;
            font-size: 3.2rem;
            color: {TEXT};
            margin: .4rem 0;
        }}

        .price-note {{
            color: {ACCENT_LIGHT};
            font-size: .9rem;
        }}

        .metric-card {{
            background: rgba(255,255,255,.035);
            border: 1px solid {BORDER};
            border-radius: 18px;
            padding: 1rem 1.1rem;
            min-height: 110px;
        }}

        .metric-name {{
            color: {MUTED};
            font-size: .78rem;
            margin-bottom: .25rem;
        }}

        .metric-value {{
            color: {TEXT};
            font-size: 1.55rem;
            font-weight: 700;
        }}

        .metric-hint {{
            color: {ACCENT_LIGHT};
            font-size: .72rem;
            margin-top: .25rem;
        }}

        div[data-testid="stForm"] {{
            background: rgba(255,255,255,.025);
            border: 1px solid {BORDER};
            border-radius: 22px;
            padding: 1.35rem;
        }}

        .stButton > button,
        .stFormSubmitButton > button,
        .stDownloadButton > button {{
            background: linear-gradient(135deg, {ACCENT}, {ACCENT_LIGHT});
            color: #17120e;
            border: 0;
            border-radius: 12px;
            font-weight: 800;
            padding: .58rem 1.2rem;
            transition: transform .15s ease, box-shadow .15s ease;
        }}

        .stButton > button:hover,
        .stFormSubmitButton > button:hover,
        .stDownloadButton > button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 8px 26px rgba(201,137,75,.24);
        }}

        div[data-baseweb="tab-list"] {{
            gap: .5rem;
        }}

        button[data-baseweb="tab"] {{
            background: rgba(255,255,255,.025);
            border-radius: 12px;
            padding-left: 1rem;
            padding-right: 1rem;
        }}

        button[data-baseweb="tab"][aria-selected="true"] {{
            background: rgba(201,137,75,.12);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ╔════════════════════════════════════════════════════════════╗
# ║ 🔐 SESSION / AUTH
# ╚════════════════════════════════════════════════════════════╝
def init_session_state():
    defaults = {
        "base_url": default_api_url(),
        "access_token": None,
        "refresh_token": None,
        "username": None,
        "authenticated": False,
        "demo_mode": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def logout():
    st.session_state.access_token = None
    st.session_state.refresh_token = None
    st.session_state.username = None
    st.session_state.authenticated = False


def api_login(base_url: str, username: str, password: str) -> dict:
    response = requests.post(
        f"{base_url}/login",
        data={"username": username, "password": password},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def refresh_access_token() -> bool:
    if not st.session_state.refresh_token:
        return False

    try:
        # L'API fournie expose /refresh en GET avec un body JSON.
        response = requests.get(
            f"{st.session_state.base_url}/refresh",
            json={"refresh_token": st.session_state.refresh_token},
            timeout=10,
        )
    except requests.exceptions.RequestException:
        return False

    if not response.ok:
        return False

    tokens = response.json()
    st.session_state.access_token = tokens["access_token"]
    st.session_state.refresh_token = tokens["refresh_token"]
    return True


def check_demo_mode(base_url: str) -> bool:
    """
    Interroge GET /health pour savoir si l'API tourne en DEMO_MODE.
    Si l'API est injoignable, on part du principe que l'auth est requise
    (fail-safe : mieux vaut demander un login inutile que d'exposer
    l'app par erreur).
    """
    try:
        resp = requests.get(f"{base_url}/health", timeout=5)
        resp.raise_for_status()
        return bool(resp.json().get("demo_mode", False))
    except requests.exceptions.RequestException:
        return False


def authenticated_request(method: str, endpoint: str, **kwargs) -> requests.Response:
    url = f"{st.session_state.base_url}{endpoint}"

    headers = kwargs.pop("headers", {})
    if st.session_state.access_token:
        headers["Authorization"] = f"Bearer {st.session_state.access_token}"

    response = requests.request(
        method,
        url,
        headers=headers,
        timeout=20,
        **kwargs,
    )

    if response.status_code == 401 and refresh_access_token():
        headers["Authorization"] = f"Bearer {st.session_state.access_token}"
        response = requests.request(
            method,
            url,
            headers=headers,
            timeout=20,
            **kwargs,
        )

    if response.status_code == 401:
        logout()

    return response


# ╔════════════════════════════════════════════════════════════╗
# ║ 🧭 SIDEBAR
# ╚════════════════════════════════════════════════════════════╝


def render_sidebar():
    with st.sidebar:
        st.markdown("### ⚙️ Connexion API")

        if st.session_state.demo_mode:
            # En démo publique : l'URL est fixée par le déployeur, pas
            # modifiable par le visiteur (évite qu'il pointe l'app vers
            # une API tierce de son choix).
            st.caption(f"API : `{st.session_state.base_url}`")
        else:
            st.session_state.base_url = st.text_input(
                "URL de l'API", value=str(st.session_state.base_url)
            )

        if st.session_state.demo_mode:
            st.markdown(
                f'<div class="risk-badge" style="background: rgba(56,189,248,0.15); '
                f'color: {ACCENT_BRAND};">🌐 Mode démo — accès libre</div>',
                unsafe_allow_html=True,
            )
            st.caption(
                "L'authentification est désactivée sur cette instance de démonstration."
            )
            return

        if st.session_state.authenticated:
            st.markdown(
                f'<div class="risk-badge" style="background: rgba(52,211,153,0.15); '
                f'color: {ACCENT_SAFE};">🟢 Connecté — {st.session_state.username}</div>',
                unsafe_allow_html=True,
            )
            st.button("Se déconnecter", on_click=logout, use_container_width=True)
        else:
            with st.form("login_form"):
                username = st.text_input("Utilisateur", value="admin")
                password = st.text_input("Mot de passe", type="password")
                submitted = st.form_submit_button(
                    "Se connecter", use_container_width=True
                )

            if submitted:
                try:
                    tokens = api_login(
                        str(st.session_state.base_url), username, password
                    )
                    st.session_state.access_token = tokens["access_token"]
                    st.session_state.refresh_token = tokens["refresh_token"]
                    st.session_state.username = username
                    st.session_state.authenticated = True
                    st.rerun()
                except requests.exceptions.HTTPError:
                    st.error("Identifiants invalides.")
                except requests.exceptions.RequestException:
                    st.error(
                        f"Impossible de joindre l'API sur {st.session_state.base_url}."
                    )


# ╔════════════════════════════════════════════════════════════╗
# ║ 🏠 ESTIMATION
# ╚════════════════════════════════════════════════════════════╝
def format_price(value: float) -> str:
    return f"${value:,.0f}".replace(",", " ")


def render_estimation_tab():
    st.markdown(
        '<div class="eyebrow">Property valuation</div>',
        unsafe_allow_html=True,
    )
    st.markdown("### Décrire le bien")

    with st.form("property_form"):
        left, right = st.columns(2)

        with left:
            st.markdown("#### 🏠 Caractéristiques")
            bed = st.number_input(
                "Chambres",
                min_value=0,
                max_value=20,
                value=3,
                step=1,
            )
            bath = st.number_input(
                "Salles de bain",
                min_value=0,
                max_value=20,
                value=2,
                step=1,
            )
            house_size = st.number_input(
                "Surface du bien",
                min_value=1.0,
                value=1600.0,
                step=50.0,
                help="Utilise la même unité que celle du dataset d'entraînement.",
            )

            prev_sold_year = st.number_input(
                "Année de la dernière vente",
                min_value=1900,
                max_value=2026,
                value=2020,
                step=1,
            )

        with right:
            st.markdown("#### 📍 Localisation")
            city = st.text_input(
                "Ville",
                value="New York",
                placeholder="Ex. New York",
            )
            state = st.text_input(
                "État",
                value="New York",
                placeholder="Ex. New York",
            )

            st.markdown(
                f"""
                <div class="property-card" style="margin-top:1rem;">
                    <div class="eyebrow">Conseil</div>
                    <div style="color:{MUTED};font-size:.9rem;">
                        Utilise les libellés de ville et d'État présents dans
                        les données d'entraînement afin d'éviter les catégories inconnues.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        submitted = st.form_submit_button(
            "🏷️ Estimer le prix",
            use_container_width=True,
        )

    if not submitted:
        return

    payload = {
        "bed": int(bed),
        "bath": int(bath),
        "city": city.strip(),
        "state": state.strip(),
        "house_size": float(house_size),
        "prev_sold_year": int(prev_sold_year),
    }

    try:
        response = authenticated_request(
            "POST",
            "/prediction",
            json=payload,
        )
    except requests.exceptions.RequestException:
        st.error(f"Impossible de joindre l'API sur {st.session_state.base_url}.")
        return

    if not response.ok:
        st.error(f"Erreur API ({response.status_code}) : {response.text}")
        return

    prediction = float(response.json()["prediction"])

    st.markdown("---")
    result_left, result_right = st.columns([1.15, 0.85])

    with result_left:
        st.markdown(
            f"""
            <div class="price-card">
                <div class="price-label">Valeur estimée</div>
                <div class="price-value">{format_price(prediction)}</div>
                <div class="price-note">
                    Estimation générée par le modèle de régression
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with result_right:
        st.markdown(
            f"""
            <div class="property-card">
                <div class="eyebrow">Bien analysé</div>
                <div style="font-size:1.2rem;font-weight:700;color:{TEXT};">
                    {city}, {state}
                </div>
                <div style="color:{MUTED};margin-top:.7rem;line-height:1.8;">
                    🛏️ {int(bed)} chambre(s)<br>
                    🛁 {int(bath)} salle(s) de bain<br>
                    📐 {house_size:,.0f} de surface
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ╔════════════════════════════════════════════════════════════╗
# ║ 📦 BATCH
# ╚════════════════════════════════════════════════════════════╝
def render_batch_tab():
    st.markdown(
        '<div class="eyebrow">Portfolio valuation</div>',
        unsafe_allow_html=True,
    )
    st.markdown("### Estimation en masse")

    st.caption("Colonnes requises : `bed`, `bath`, `city`, `state`, `house_size`.")

    uploaded = st.file_uploader(
        "Importer un CSV de biens immobiliers",
        type="csv",
    )

    if uploaded is None:
        return

    try:
        df = pd.read_csv(uploaded)
    except Exception as exc:
        st.error(f"Impossible de lire le CSV : {exc}")
        return

    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        st.error(f"Colonnes manquantes : {missing}")
        return

    st.dataframe(
        df.head(10),
        use_container_width=True,
        hide_index=True,
    )

    if not st.button(
        "🏘️ Estimer tous les biens",
        use_container_width=True,
    ):
        return

    batch_df = df.copy()

    try:
        batch_df["bed"] = batch_df["bed"].astype(int)
        batch_df["bath"] = batch_df["bath"].astype(int)
        batch_df["house_size"] = batch_df["house_size"].astype(float)
        batch_df["city"] = batch_df["city"].astype(str)
        batch_df["state"] = batch_df["state"].astype(str)
        batch_df["prev_sold_year"] = batch_df["prev_sold_year"].astype(int)
    except (ValueError, TypeError) as exc:
        st.error(f"Types de données invalides : {exc}")
        return

    payload = {"data": batch_df[REQUIRED_COLUMNS].to_dict(orient="records")}

    try:
        response = authenticated_request(
            "POST",
            "/prediction-batch",
            json=payload,
        )
    except requests.exceptions.RequestException:
        st.error(f"Impossible de joindre l'API sur {st.session_state.base_url}.")
        return

    if not response.ok:
        st.error(f"Erreur API ({response.status_code}) : {response.text}")
        return

    results = response.json()
    batch_df["estimated_price"] = [float(item["prediction"]) for item in results]

    st.markdown("#### Résultats")
    st.dataframe(
        batch_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "estimated_price": st.column_config.NumberColumn(
                "Prix estimé",
                format="$ %.0f",
            )
        },
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Biens analysés",
            len(batch_df),
        )

    with col2:
        st.metric(
            "Estimation moyenne",
            format_price(batch_df["estimated_price"].mean()),
        )

    with col3:
        st.metric(
            "Estimation médiane",
            format_price(batch_df["estimated_price"].median()),
        )

    st.download_button(
        "⬇️ Télécharger les estimations",
        data=batch_df.to_csv(index=False).encode("utf-8"),
        file_name="real_estate_predictions.csv",
        mime="text/csv",
    )


# ╔════════════════════════════════════════════════════════════╗
# ║ 🔍 ONGLET — DATASET / EDA REAL ESTATE
# ╚════════════════════════════════════════════════════════════╝


@st.cache_data
def load_raw_dataset(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


@st.cache_data
def prepare_dataset_for_visualization(df: pd.DataFrame) -> pd.DataFrame:
    """
    Préparation minimale reproduisant les transformations nécessaires
    aux visualisations du notebook, sans appliquer le preprocessing ML.
    """
    df = df.copy()

    # Le notebook convertit prev_sold_date en datetime.
    if "prev_sold_date" in df.columns:
        df["prev_sold_date"] = pd.to_datetime(
            df["prev_sold_date"],
            errors="coerce",
        )

    # Le notebook crée log_price pour mieux visualiser
    # la distribution très asymétrique des prix.
    if "price" in df.columns:
        df["log_price"] = np.log1p(df["price"])

    return df


def dataset_expanders(df: pd.DataFrame):
    with st.expander("📏 Dimensions"):
        st.write(f"{df.shape[0]:,} lignes × {df.shape[1]} colonnes")

    with st.expander("🧬 Types de données"):
        st.dataframe(
            df.dtypes.astype(str).to_frame("dtype"),
            use_container_width=True,
        )

    with st.expander("⚠️ Valeurs manquantes"):
        missing = pd.DataFrame(
            {
                "n_missing": df.isna().sum(),
                "pct_missing": (df.isna().mean() * 100).round(2),
            }
        )

        missing = missing[missing["n_missing"] > 0].sort_values(
            "n_missing",
            ascending=False,
        )

        if missing.empty:
            st.write("Aucune valeur manquante détectée.")
        else:
            st.dataframe(
                missing,
                use_container_width=True,
            )

    with st.expander("🔂 Doublons"):
        st.write(f"{df.duplicated().sum():,} ligne(s) dupliquée(s)")

    with st.expander("🔢 Valeurs uniques"):
        unique_values = df.nunique().sort_values(ascending=False).to_frame("n_unique")

        st.dataframe(
            unique_values,
            use_container_width=True,
        )

    with st.expander("👀 Aperçu"):
        st.dataframe(
            df.head(10),
            use_container_width=True,
            hide_index=True,
        )


def dark_fig(figsize=(6, 4)):
    fig, ax = plt.subplots(figsize=figsize)

    fig.patch.set_alpha(0)
    ax.set_facecolor("none")

    for spine in ax.spines.values():
        spine.set_color("#485360")

    ax.tick_params(colors=MUTED)
    ax.xaxis.label.set_color(TEXT)
    ax.yaxis.label.set_color(TEXT)
    ax.title.set_color(TEXT)

    return fig, ax


# ──────────────────────────────────────────────────────────────
# Corrélations
# ──────────────────────────────────────────────────────────────
def plot_real_estate_correlation(df: pd.DataFrame):
    numeric_df = df.select_dtypes(include=np.number).copy()

    # Comme dans le notebook : on ne met pas price
    # dans la matrice afin de travailler avec log_price.
    if "price" in numeric_df.columns:
        numeric_df = numeric_df.drop(columns=["price"])

    fig, ax = dark_fig((6, 5))

    sns.heatmap(
        numeric_df.corr(),
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        square=True,
        ax=ax,
    )

    ax.set_title("Corrélations entre variables numériques")

    return fig


# ──────────────────────────────────────────────────────────────
# Distribution prix brut / logarithmique
# ──────────────────────────────────────────────────────────────
def plot_price_distribution(df: pd.DataFrame):
    fig, ax = dark_fig((6, 4))

    sns.histplot(
        data=df,
        x="price",
        bins=50,
        kde=True,
        ax=ax,
    )

    ax.set_title("Distribution des prix")
    ax.set_xlabel("Prix")

    return fig


def plot_log_price_distribution(df: pd.DataFrame):
    fig, ax = dark_fig((6, 4))

    sns.histplot(
        data=df,
        x="log_price",
        bins=50,
        kde=True,
        ax=ax,
    )

    ax.set_title("Distribution logarithmique des prix")
    ax.set_xlabel("Log(price)")

    return fig


# ──────────────────────────────────────────────────────────────
# Prix par ville
# ──────────────────────────────────────────────────────────────
def plot_price_by_city(df: pd.DataFrame):
    top_cities = df["city"].value_counts().head(10).index

    df_city = df[df["city"].isin(top_cities)].copy()

    fig, ax = dark_fig((7, 5))

    sns.boxplot(
        data=df_city,
        x="log_price",
        y="city",
        ax=ax,
        color=ACCENT,
    )

    ax.set_title("Distribution des prix dans les 10 villes les plus représentées")
    ax.set_xlabel("Log(price)")
    ax.set_ylabel("Ville")

    return fig


# ──────────────────────────────────────────────────────────────
# Prix selon nombre de chambres
# ──────────────────────────────────────────────────────────────
def plot_price_by_bedrooms(df: pd.DataFrame):
    df_plot = df[df["bed"].between(1, 14)].copy()

    fig, ax = dark_fig((6, 4))

    sns.boxplot(
        data=df_plot,
        x="bed",
        y="log_price",
        showfliers=False,
        ax=ax,
        color=ACCENT,
    )

    ax.set_title("Prix selon le nombre de chambres")
    ax.set_xlabel("Chambres")
    ax.set_ylabel("Log(price)")

    return fig


# ──────────────────────────────────────────────────────────────
# Prix selon nombre de salles de bain
# ──────────────────────────────────────────────────────────────
def plot_price_by_bathrooms(df: pd.DataFrame):
    bath_limit = df["bath"].quantile(0.999)

    df_plot = df[df["bath"].le(bath_limit)].copy()

    fig, ax = dark_fig((6, 4))

    sns.boxplot(
        data=df_plot,
        x="bath",
        y="log_price",
        showfliers=False,
        ax=ax,
        color=ACCENT_LIGHT,
    )

    ax.set_title("Prix selon le nombre de salles de bain")
    ax.set_xlabel("Salles de bain")
    ax.set_ylabel("Log(price)")

    return fig


# ──────────────────────────────────────────────────────────────
# Surface vs prix
# ──────────────────────────────────────────────────────────────
def plot_house_size_vs_price(df: pd.DataFrame):
    df_sample = (
        df[["house_size", "log_price"]]
        .dropna()
        .sample(
            n=min(10_000, len(df.dropna(subset=["house_size", "log_price"]))),
            random_state=42,
        )
    )

    fig, ax = dark_fig((6, 4))

    sns.scatterplot(
        data=df_sample,
        x="house_size",
        y="log_price",
        alpha=0.20,
        s=15,
        ax=ax,
        color=ACCENT,
    )

    ax.set_title("Surface du bien vs prix")
    ax.set_xlabel("Surface")
    ax.set_ylabel("Log(price)")

    return fig


# ──────────────────────────────────────────────────────────────
# États avec le plus d'annonces
# ──────────────────────────────────────────────────────────────
def plot_top_states(df: pd.DataFrame):
    state_count = df["state"].value_counts().head(15)

    fig, ax = dark_fig((6, 5))

    sns.barplot(
        x=state_count.values,
        y=state_count.index,
        ax=ax,
        color=ACCENT,
    )

    ax.set_title("Top 15 États par nombre d'annonces")
    ax.set_xlabel("Nombre de biens")
    ax.set_ylabel("État")

    return fig


# ──────────────────────────────────────────────────────────────
# Prix médian par État
# ──────────────────────────────────────────────────────────────
def plot_median_price_by_state(df: pd.DataFrame):
    median_price = (
        df.groupby("state")["price"].median().sort_values(ascending=False).head(15)
    )

    fig, ax = dark_fig((6, 5))

    sns.barplot(
        x=median_price.values,
        y=median_price.index,
        ax=ax,
        color=ACCENT_LIGHT,
    )

    ax.set_title("Top 15 États par prix médian")
    ax.set_xlabel("Prix médian")
    ax.set_ylabel("État")

    return fig


# ╔════════════════════════════════════════════════════════════╗
# ║ 🏘️ RENDER DATASET
# ╚════════════════════════════════════════════════════════════╝
def render_dataset_tab():

    st.markdown(
        '<div class="eyebrow">Dataset intelligence</div>',
        unsafe_allow_html=True,
    )

    st.markdown("### Exploration des données immobilières")

    dataset_source = get_dataset_source()
    is_remote_dataset = dataset_source.startswith(("http://", "https://"))

    if not is_remote_dataset and not Path(dataset_source).exists():
        st.error(
            "Dataset introuvable. Configure REAL_ESTATE_DATA_URL dans les "
            "secrets Streamlit ou ajoute le fichier local attendu."
        )
        return

    df_raw = load_raw_dataset(dataset_source)

    # Copie uniquement destinée aux visualisations.
    df_viz = prepare_dataset_for_visualization(df_raw)

    st.caption(
        "Exploration du dataset utilisé pour le projet. "
        "`prev_sold_date` est convertie en datetime et `log_price` "
        "est créée uniquement pour reproduire les visualisations du notebook."
    )

    dataset_expanders(df_raw)

    st.markdown("---")
    st.markdown("### Visualisations exploratoires")

    if not st.button(
        "📊 Générer les visualisations",
        use_container_width=False,
    ):
        return

    # ── Corrélation ──────────────────────────────────────────
    st.markdown("#### Matrice de corrélation")

    left, center, right = st.columns([1, 2.4, 1])

    with center:
        fig = plot_real_estate_correlation(df_viz)
        st.pyplot(
            fig,
            use_container_width=True,
        )

    plt.close(fig)

    # ── Distribution price / log price ───────────────────────
    st.markdown("#### Distribution du prix")

    col1, col2 = st.columns(2)

    with col1:
        fig = plot_price_distribution(df_viz)
        st.pyplot(
            fig,
            use_container_width=True,
        )
        plt.close(fig)

    with col2:
        fig = plot_log_price_distribution(df_viz)
        st.pyplot(
            fig,
            use_container_width=True,
        )
        plt.close(fig)

    # ── City ─────────────────────────────────────────────────
    st.markdown("#### Prix selon la localisation")

    left, center, right = st.columns([1, 2.5, 1])

    with center:
        fig = plot_price_by_city(df_viz)
        st.pyplot(
            fig,
            use_container_width=True,
        )

    plt.close(fig)

    # ── Bedrooms / bathrooms ─────────────────────────────────
    st.markdown("#### Caractéristiques du logement")

    col1, col2 = st.columns(2)

    with col1:
        fig = plot_price_by_bedrooms(df_viz)
        st.pyplot(
            fig,
            use_container_width=True,
        )
        plt.close(fig)

    with col2:
        fig = plot_price_by_bathrooms(df_viz)
        st.pyplot(
            fig,
            use_container_width=True,
        )
        plt.close(fig)

    # ── House size ────────────────────────────────────────────
    st.markdown("#### Surface et prix")

    left, center, right = st.columns([1, 2.4, 1])

    with center:
        fig = plot_house_size_vs_price(df_viz)
        st.pyplot(
            fig,
            use_container_width=True,
        )

    plt.close(fig)

    # ── States ────────────────────────────────────────────────
    st.markdown("#### Marché par État")

    col1, col2 = st.columns(2)

    with col1:
        fig = plot_top_states(df_viz)
        st.pyplot(
            fig,
            use_container_width=True,
        )
        plt.close(fig)

    with col2:
        fig = plot_median_price_by_state(df_viz)
        st.pyplot(
            fig,
            use_container_width=True,
        )
        plt.close(fig)


# ╔════════════════════════════════════════════════════════════╗
# ║ 📊 MODÈLE
# ╚════════════════════════════════════════════════════════════╝
def render_model_tab():
    st.markdown(
        '<div class="eyebrow">Model intelligence</div>',
        unsafe_allow_html=True,
    )
    st.markdown("### Performance du modèle")

    try:
        response = authenticated_request(
            "GET",
            "/model_info",
        )
    except requests.exceptions.RequestException:
        st.error(f"Impossible de joindre l'API sur {st.session_state.base_url}.")
        return

    if not response.ok:
        st.error(f"Erreur API ({response.status_code}) : {response.text}")
        return

    info = response.json()

    st.markdown(
        f"""
        <div class="property-card">
            <div class="eyebrow">Modèle chargé</div>
            <div style="font-family:'Playfair Display',serif;
                        font-size:1.7rem;color:{TEXT};">
                {info["model_name"]}
            </div>
            <div style="color:{MUTED};margin-top:.5rem;">
                {info["model_description"]}
            </div>
            <div style="color:{ACCENT_LIGHT};margin-top:.6rem;">
                {info["model_type"]} · {info["model_length"]:,} observations
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### Indicateurs")

    metrics = [
        ("R²", info["model_r2"], "Qualité d'ajustement", None),
        ("MAE", info["model_mae"], "Erreur absolue moyenne", "$"),
        ("RMSE", info["model_rmse"], "Pénalise davantage les grosses erreurs", "$"),
        ("MSE", info["model_mse"], "Erreur quadratique moyenne", None),
        ("Max error", info["model_max_error"], "Erreur maximale observée", "$"),
    ]

    columns = st.columns(5)

    for container, (name, value, hint, prefix) in zip(columns, metrics):
        if prefix == "$":
            formatted = format_price(value)
        elif name == "R²":
            formatted = f"{value:.2f}"
        else:
            formatted = f"{value:,.2f}"

        with container:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-name">{name}</div>
                    <div class="metric-value">{formatted}</div>
                    <div class="metric-hint">{hint}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("#### Variables utilisées")
    st.write(", ".join(info["model_features"]))

    # Comparaison des métriques d'erreur, hors R² qui n'est pas dans la même unité.
    error_metrics = {
        "MAE": info["model_mae"],
        "RMSE": info["model_rmse"],
        "Max error": info["model_max_error"],
    }

    fig = go.Figure(
        go.Bar(
            x=list(error_metrics.keys()),
            y=list(error_metrics.values()),
            marker_color=ACCENT,
            text=[format_price(v) for v in error_metrics.values()],
            textposition="outside",
        )
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": TEXT},
        yaxis={
            "gridcolor": "rgba(255,255,255,.07)",
            "title": "Erreur",
        },
        xaxis={"gridcolor": "rgba(255,255,255,0)"},
        height=330,
        margin=dict(l=20, r=20, t=25, b=20),
        showlegend=False,
    )

    chart_left, chart_center, chart_right = st.columns([1, 2.5, 1])
    with chart_center:
        st.plotly_chart(
            fig,
            use_container_width=True,
        )


# ╔════════════════════════════════════════════════════════════╗
# ║ 🚀 MAIN
# ╚════════════════════════════════════════════════════════════╝
def main():
    init_session_state()
    inject_css()

    st.session_state.demo_mode = check_demo_mode(str(st.session_state.base_url))
    if st.session_state.demo_mode:
        st.session_state.authenticated = True

    render_sidebar()

    st.markdown(
        '<div class="eyebrow">Machine learning · Real estate</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="estate-title">Estate Lens</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="estate-subtitle">'
        "Estimation immobilière propulsée par un modèle de régression."
        "</div>",
        unsafe_allow_html=True,
    )

    if not st.session_state.authenticated:
        st.info("Connecte-toi via la barre latérale pour accéder aux estimations.")
        return

    tab_estimation, tab_batch, tab_dataset, tab_model = st.tabs(
        [
            "🏡 Estimation",
            "🏘️ Batch",
            "🔍 Dataset",
            "📊 Modèle",
        ]
    )

    with tab_estimation:
        render_estimation_tab()

    with tab_batch:
        render_batch_tab()

    with tab_dataset:
        render_dataset_tab()

    with tab_model:
        render_model_tab()


if __name__ == "__main__":
    main()
