"""Interface inicial do Steam Sentiment Monitor."""

import os
from pathlib import Path
import sqlite3

import altair as alt
import streamlit as st

from collection import SteamCollectionError
from evaluation import evaluate_reviews
from dashboard_data import sentiment_chart_data, select_review_examples
from persistence import ReviewStore

PROJECT_DIR = Path(__file__).resolve().parent
os.environ.setdefault("HF_HOME", str(PROJECT_DIR / ".venv" / "hf-cache"))

from workflow import collect_and_store

DB_PATH = Path(os.environ.get("STEAM_SENTIMENT_DB", str(PROJECT_DIR / "data" / "reviews.sqlite3")))

st.set_page_config(page_title="Steam Sentiment Monitor", page_icon="🎮", layout="centered")
st.title("Steam Sentiment Monitor")
st.caption("Acompanhe o sentimento das reviews em inglês de um jogo da Steam.")

app_id_text = st.text_input("App ID", value="620", help="Número do jogo na Steam. Exemplo: 620 (Portal 2).").strip()
valid_id = app_id_text.isascii() and app_id_text.isdecimal() and int(app_id_text) > 0
update = st.button("Atualizar reviews", type="primary", disabled=not valid_id)
if not valid_id:
    st.error("Informe um App ID inteiro e positivo.")
    st.stop()
app_id = int(app_id_text)

if "last_updates" not in st.session_state:
    st.session_state["last_updates"] = {}

if update:
    try:
        with st.spinner("Buscando e analisando novas reviews…"):
            result = collect_and_store(app_id, db_path=DB_PATH)
        st.session_state["last_updates"][app_id] = result["new"]
        st.success(f"Atualização concluída: {result['new']} novas reviews.")
    except (SteamCollectionError, ValueError, OSError, RuntimeError, sqlite3.Error) as exc:
        st.error(f"Não foi possível atualizar as reviews: {exc}")

try:
    with ReviewStore(DB_PATH) as store:
        reviews = store.list_reviews(app_id)
except sqlite3.Error as exc:
    st.error(f"Não foi possível ler as reviews salvas: {exc}")
    st.stop()

new_count = st.session_state["last_updates"].get(app_id)
counts = st.columns(2)
counts[0].metric("Total armazenado", str(len(reviews)))
counts[1].metric("Novas na última atualização", str(new_count) if new_count is not None else "—")

if reviews:
    total = len(reviews)
    ai_positive = sum(review["label"] == "POSITIVE" for review in reviews) / total
    steam_positive = sum(review["voted_up"] for review in reviews) / total
    accuracy = evaluate_reviews(reviews)["accuracy"]
    values = [f"{ai_positive:.1%}", f"{steam_positive:.1%}", f"{accuracy:.1%}"]
else:
    values = ["—", "—", "—"]

metrics = st.columns(3)
for column, label, value in zip(metrics, ["Positivo segundo a IA", "Recomendaram na Steam", "Accuracy da IA"], values):
    column.metric(label, value)

if not reviews:
    st.info("Nenhuma review armazenada para este jogo. Clique em Atualizar reviews para começar.")
st.caption("Indicadores calculados sobre todas as reviews armazenadas deste App ID. Cada atualização busca até 100 reviews recentes.")
if new_count is None:
    st.caption("Ainda não houve atualização para este jogo nesta sessão.")

if reviews:
    distribution, daily = sentiment_chart_data(reviews)

    st.subheader("Distribuição atual segundo a IA")
    st.bar_chart(
        [{"Sentimento": label, "Reviews": count} for label, count in distribution.items()],
        x="Sentimento", y="Reviews",
    )

    st.subheader("Evolução das reviews positivas")
    timeline = alt.Chart(alt.Data(values=daily)).mark_line(point=True).encode(
        x=alt.X("date:T", title="Data da review (UTC)"),
        y=alt.Y("positive_percentage:Q", title="Reviews positivas (%)", scale=alt.Scale(domain=[0, 100])),
        tooltip=[
            alt.Tooltip("date:T", title="Data", format="%d/%m/%Y"),
            alt.Tooltip("positive_percentage:Q", title="Positivas (%)", format=".1f"),
            alt.Tooltip("total:Q", title="Reviews no dia", format="d"),
        ],
    )
    st.altair_chart(timeline)
    st.caption("Percentual positivo entre as reviews armazenadas de cada dia de criação (UTC). Dias sem reviews não recebem valor; passe o mouse para ver a quantidade por dia.")

    st.subheader("IA × recomendação do usuário")
    matrix = evaluate_reviews(reviews)["confusion_matrix"]
    st.table({
        "Usuário na Steam": ["Não recomendou", "Recomendou"],
        "IA: negativo": [matrix[0][0], matrix[1][0]],
        "IA: positivo": [matrix[0][1], matrix[1][1]],
    })
    st.caption("Cada célula mostra a quantidade de reviews. A IA concorda quando classifica como negativo quem não recomendou, ou como positivo quem recomendou.")

if reviews:
    examples = select_review_examples(reviews)
    sections = [
        ("Reviews positivas com maior confiança do modelo", "positive"),
        ("Reviews negativas com maior confiança do modelo", "negative"),
        ("Onde a IA discordou do usuário", "disagreements"),
    ]
    st.caption("Até 5 reviews por seção, em ordem de confiança da IA. Abra um item para ler o texto completo.")
    for title, section in sections:
        st.subheader(title)
        if not examples[section]:
            st.info("Nenhuma review encontrada nesta seção.")
        for position, review in enumerate(examples[section], start=1):
            sentiment = "Positivo" if review["label"] == "POSITIVE" else "Negativo"
            recommendation = "Recomendou" if review["voted_up"] else "Não recomendou"
            with st.expander(f"Review {position} · Confiança da IA: {review['confidence']:.1%}"):
                st.caption(f"IA: {sentiment} · Confiança: {review['confidence']:.1%} · Usuário: {recommendation}")
                st.text(review["texto"])
