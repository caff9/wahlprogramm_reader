import streamlit as st
import requests
import fitz
import tempfile
import plotly.graph_objects as go
import pandas as pd
import re
from itertools import count
import textrazor

from mappings import docs, docs_colors


@st.cache(allow_output_mutation=True)
def read_docs_from_links(doc_dict):
    """
    Reads a dict of structure doc_name: doc_link and imports the respective
    documents.

    Returns
    -------
    dict
        A dict with doc_name as key. Contains a nested dict of structure
        line_number: line_text.
    """
    return_dict = {}
    for asset_name, asset_link in doc_dict.items():
        asset = requests.get(asset_link)
        with tempfile.TemporaryDirectory() as directory:
            temp_file_name = asset_name.replace("/", "-")
            t = open(f"{directory}/{temp_file_name}.pdf", "wb").write(asset.content)
            doc = fitz.Document(f"{directory}/{temp_file_name}.pdf")
            doc_text = ""
            for page in doc:
                doc_text += page.getText()
            asset_dict = {}
            for line_number, line_text in zip(count(), doc_text.splitlines()):
                asset_dict[line_number] = line_text
            return_dict[asset_name] = asset_dict
    return return_dict


@st.cache
def search_against_docs(asset_dict, search_phrase):
    """
    Checks all loaded docs against search phrase and creates a dict
    of matches.

    Parameters
    ----------
    search_phrase : string

    Returns
    -------
    dict
        A dict with doc_name as key. Contains a nested dict of structure
        line_number: line_text for lines with a match against search_phrase.
    """
    asset_search_matches = {}
    for asset_name, asset_content_dict in asset_dict.items():
        match_dict = {}
        for line_number, line_text in asset_content_dict.items():
            if search_phrase.lower() in line_text.lower():
                match_dict[line_number] = [line_text]
        asset_search_matches[asset_name] = match_dict
    return asset_search_matches


@st.cache
def create_match_histogram(asset_search_matches, docs_colors):
    """
    Checks a dictionary of matches and returns a histogram.

    Parameters
    ----------
    asset_search_matches : dict
    docs_colors : dict

    Returns
    -------
    Plotly figure
    """
    match_dict = {}
    for asset_name, search_matches in asset_search_matches.items():
        match_dict[asset_name] = len(search_matches)
    fig = go.Figure(
        data=go.Bar(
            y=list(match_dict.keys()),
            x=list(match_dict.values()),
            text=list(match_dict.values()),
            opacity=0.9,
            marker_color=list(docs_colors.values()),
            marker_line={
                "color": "white",
                "width": 1,
            },
            textposition="outside",
            orientation="h",
            meta=search_phrase,
            hovertemplate="<extra></extra>%{y} erwähnt %{meta} %{x} mal in ihrem Wahlprogramm.",
        )
    )
    fig.update_layout(
        yaxis={"categoryorder": "total ascending"},
        xaxis={
            "zeroline": True,
            "zerolinewidth": 1,
            "zerolinecolor": "black",
            "gridcolor": "black",
        },
        title={
            "text": f"Anzahl Erwähnungen von <b>{search_phrase}</b> nach Partei",
            "y": 0.9,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": {"size": 24},
        },
        paper_bgcolor="rgba(162,162,162,0.1)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin_pad=10,
    )
    return fig


def request_textrazor_data(match_nr, text_to_analyze):
    textrazor.api_key = st.secrets["textrazor_key"]
    tr_client = textrazor.TextRazor(extractors=["entities", "topics", "categories"])

    response = None
    topic_df = pd.DataFrame(columns=["topic_result_id", "label", "score", "wikilink"])
    try:
        response = tr_client.analyze(text_to_analyze)
    except textrazor.TextRazorAnalysisException:
        pass
    if response:
        if response.topics():
            for topic, topic_n in zip(response.topics(), count()):
                topic_data = topic.json
                topic_df = topic_df.append(
                    {
                        "match_nr": match_nr,
                        "topic_result_id": topic_n,
                        "label": topic_data["label"],
                        "score": topic_data["score"],
                    },
                    ignore_index=True,
                )
    return topic_df


def create_topic_histogram(topic_df):
    """
    Builds a chart for the frequency of topics based on a DataFrame.

    Parameters
    ----------
    topic_df : DataFrame

    Returns
    -------
    Plotly figure
    """
    fig = go.Figure(
        data=go.Bar(
            y=topic_df["label"],
            x=topic_df["match_nr"],
            text=topic_df["match_nr"],
            textposition="outside",
            orientation="h",
            meta=search_phrase,
            hovertemplate="<extra></extra>%{meta} wird %{x} mal im Kontext von %{y} erwähnt.",
            opacity=0.9,
            marker={
                "color": topic_df["match_nr"],
                "colorscale": "blues",
            },
            marker_line={
                "color": "white",
                "width": 1,
            },
        )
    )
    fig.update_layout(
        yaxis={"categoryorder": "total ascending"},
        xaxis={
            "zeroline": True,
            "zerolinewidth": 1,
            "zerolinecolor": "black",
            "gridcolor": "black",
        },
        title={
            "text": f"Top 10 Themen, in deren Kontext <b>{search_phrase}</b><br>von <b>{st.session_state['selected_party']}</b> erwähnt wird",
            "y": 0.9,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": {"size": 24},
        },
        paper_bgcolor="rgba(162,162,162,0.1)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin_pad=10,
    )
    return fig


# ###############################
# APP HEADER
# ###############################
st.markdown(
    "# Versuchst du, ein besseres Verständnis der aktuellen Wahlprogramme zu entwickeln?"
)
st.markdown(
    "Diese App ist der richtige Ort dafür.\n\n"
    "Starte mit einer einzelnen Suche, welche gegen alle Wahlprogramme durchgeführt wird "
    "und schau, wohin dich deine Entdeckungsreise führen wird."
)

# ###############################
# ASK FOR USER INPUT
# ###############################
search_phrase = st.text_input(
    label="Gib hier das Suchwort ein, das dich interessiert.", value="klima"
)

with st.spinner(
    "Einen Moment, wir durchsuchen die Wahlprogramme nach deiner Suchanfrage."
):
    assets = read_docs_from_links(doc_dict=docs)
    f"""
        ---
        ## Ok, lass uns zunächst einmal nachsehen, wie häufig die Wahlprogramme der Parteien ***{search_phrase}*** erwähnen. Mal schauen, was wir so finden :face_with_monocle:
    """

    asset_search_matches = search_against_docs(
        asset_dict=assets, search_phrase=search_phrase
    )
    match_histogram = create_match_histogram(
        asset_search_matches=asset_search_matches, docs_colors=docs_colors
    )

    st.plotly_chart(match_histogram, use_container_width=True)

    f"""
        ### Alles klar, die folgenden Parteien erwähnen ***{search_phrase}*** mindestens einmal in ihrem Wahlprogramm.\n
        Klick auf eine Partei, um die einzelnen Ausschnitte der Wahlprogramme anzuzeigen.

    """

    button_container = st.container()
    col1, col2, col3, col4 = button_container.columns(4)

    i = 0
    for asset_name, matches in asset_search_matches.items():
        if len(matches) > 0:
            if i == 4:
                i = 1
            else:
                i += 1
            col = locals()[f"col{i}"]
            if col.button(asset_name):
                st.session_state["selected_party"] = asset_name
                topic_placeholder = st.empty()
                topics_across_matches = pd.DataFrame(
                    columns=["topic_result_id", "label", "score", "wikilink"]
                )
                with st.expander("Treffer anzeigen", expanded=False):
                    for match, match_nr in zip(matches, count()):
                        f"#### Treffer {match_nr + 1}:\n"
                        match_text = ">"
                        for line_number in range(match - 5, match + 6):
                            line_text = assets[asset_name][line_number]
                            line_text = re.sub(
                                search_phrase,
                                f"`{search_phrase}`",
                                line_text,
                                flags=re.IGNORECASE,
                            )
                            match_text += f"{line_text}  \n"
                        f"{match_text}"
                        if match_nr <= 9:
                            topics = request_textrazor_data(match_nr, match_text)
                            topics_across_matches = topics_across_matches.append(
                                topics, ignore_index=True
                            )
                            st.dataframe(data=topics)
                agg_topics = topics_across_matches.groupby(
                    ["label"], as_index=False
                ).agg({"match_nr": pd.Series.nunique, "score": "sum"})
                agg_topics = agg_topics.nlargest(10, "score")
                topic_fig = create_topic_histogram(topic_df=agg_topics)
                topic_placeholder.plotly_chart(topic_fig, use_container_width=True)
