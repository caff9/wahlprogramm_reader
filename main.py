import streamlit as st
import pandas as pd
import re
from decouple import config
from random import sample
from PIL import Image
import base64

from mappings import docs, docs_colors, chart_specifications, topics_df, entities_df
from utils.doc_handler import (
    read_docs_from_json,
    search_against_docs,
    request_textrazor_data,
)
from utils.chart_builder import create_horizontal_barchart


# #############################################
# SETTINGS
# #############################################
textrazor_key = st.secrets["TEXTRAZOR"]

# hide menu and fullscreen icon
st.markdown(
    """ <style>
.css-ucv8le.e19lei0e0 {visibility: hidden; position: relative; left: -50px;}
</style> """,
    unsafe_allow_html=True,
)

# #############################################
# CACHE DEFINTIONS
# #############################################
if "search_phrase" not in st.session_state:
    st.session_state["search_phrase"] = None
if "selected_party" not in st.session_state:
    st.session_state["selected_party"] = None
if "matches_to_analyze" not in st.session_state:
    st.session_state["matches_to_analyze"] = None
if "selected_topic" not in st.session_state:
    st.session_state["selected_topic"] = None
if "selected_entity" not in st.session_state:
    st.session_state["selected_entity"] = None

# ###############################
# APP STRUCTURE
# ###############################
st.image(Image.open("assets/header.png"))
f"""
    ## Jetzt noch alle Wahlprogramme im Detail lesen?
    ## Irgendwie unrealistisch, oder?
    ### Aber nur eine Zusammenfassung zu lesen ist dir trotzdem zu wenig?\n
    ### Dann kann dir diese App helfen: Durchsuche die Programme diverser Parteien gleichzeitig nach den Themen, die *dir* wichtig sind - und verschaffe dir *dein eigenes Bild*.
"""
st.markdown(
    "Starte mit einer einzelnen Suche, welche gegen alle Wahlprogramme durchgeführt wird "
    "und schau, wohin dich deine Entdeckungsreise führen wird."
)
with st.expander("Disclaimer & How-To", expanded=False):
    f"""
    **Disclaimer**\n
    - Für den Inhalt der Wahlprogramme sind allein die Parteien verantwortlich.
    - Die Inhalte der Wahlgramme wurden am 17.09.2021 abgerufen. Spätere Änderungen sind hier nicht mehr berücksichtigt.
    - Diese App ist eine Work-In-Progress Tech Demo und weist daher einige Einschränkungen auf:
      - Die Textsuche kann keine Zeilenumbrüche erkennen. Wird dein gesuchtes Wort im Text umgebrochen, wird dies daher nicht als Treffer aufgeführt.
      - Wird dein Suchwort (z.B. "Zug") als Teil eines anderen Worts (z.B. "Aufzug") gefunden, wird dies als Treffer gewertet.
      - Für die Themen- und Konzepterkennung stehen nur 500 Anfragen je Tag bereit. Ist dieses Kontingent erschöpft, werden für deine Suche keine Themen und Konzepte gefunden und die App gibt einen Fehler aus.
      - Themen und Konzepte können je Partei nur für 10 zufällig ermittelte Treffer bestimmt werden.\n\n
    **How-To**\n
    - Nach der Eingabe einen Suchbegriff kannst du zunächst einsehen, wie häufig das gesuchte Wort in den Wahlprogrammen der verschiedenen Parteien verwendet wird; Klein- / Großschreibung wird dabei ignoriert.
    - Über die Button unterhalb des ersten Charts kannst du anschließend eine Partei auswählen, für welche du die Treffer für deinen Suchbegriff analysieren möchtest.
      - In der aufklappbaren Sektion "Alle einzelnen Treffer anzeigen" kannst du ... nun ... alle Treffer anzeigen :wink:
      - Über die zusätzlichen Buttons unterhalb der Charts für Themen und Konzepte kannst du diejenigen Treffer im Kontext des jeweiligen Themas oder Konzepts anzeigen.
    """

f"""
    ---
    ### Los geht´s!
"""
search_phrase = st.text_input(
    label="Gib hier den Suchbegriff ein, der dich interessiert.", value="Klima"
)
if search_phrase != st.session_state["search_phrase"]:
    st.session_state["search_phrase"] = search_phrase
    st.session_state["selected_party"] = None
    st.session_state["selected_topic"] = None
    st.session_state["selected_entity"] = None

section1_placeholder = st.empty()
doc_match_chart_placeholder = st.empty()
section2_placeholder = st.empty()

button_container = st.container()
col1, col2, col3, col4 = button_container.columns(4)
party_matches_placeholder = st.empty()
all_matches_placeholder = st.empty()

topics_placeholder = st.empty()
topics_selection_placeholder = st.container()
topics_col0, topics_col1 = topics_selection_placeholder.columns(2)
topic_match_placeholder = st.empty()

entities_placeholder = st.empty()
entities_selection_placeholder = st.container()
entities_col0, entities_col1 = entities_selection_placeholder.columns(2)
entity_match_placeholder = st.empty()

st.markdown(
    f"""
        ---
        Check out the repository for this app: <a href="https://github.com/caff9/wahlprogramm_reader" target="_blank"><img src="data:image/gif;base64,{base64.b64encode(open("assets/GitHub-Mark-32px.png", "rb").read()).decode("utf-8")}" height="32" alt="GitHub"></a> \n
        Write me on LinkedIn: <a href="https://www.linkedin.com/in/erik-klemusch/" target="_blank"><img src="data:image/gif;base64,{base64.b64encode(open("assets/LI-In-Bug.png", "rb").read()).decode("utf-8")}" height="32" alt="LinkedIn"></a>
    """,
    unsafe_allow_html=True,
)

# #############################################
# DEFINTION OF FUNCTIONS USING CACHE
# #############################################
@st.cache(allow_output_mutation=True)
def st_read_docs_from_links():
    assets = read_docs_from_json()
    return assets


@st.cache
def st_search_against_docs(asset_dict, search_phrase):
    asset_search_matches = search_against_docs(asset_dict, search_phrase)
    return asset_search_matches


@st.cache
def st_create_horizontal_barchart(chart_data, chart_specs, **kwargs):
    fig = create_horizontal_barchart(chart_data, chart_specs, **kwargs)
    return fig


@st.cache
def st_random_match_sample(match_dict, party):
    matches_to_analyze = sample(
        list(range(0, match_dict[party])),
        min(10, match_dict[party]),
    )
    return matches_to_analyze


@st.cache
def st_textrazor_match_data(
    topics_across_matches,
    entities_across_matches,
    asset_search_matches,
    matches_to_analyze,
    match_context,
):
    tr_match_data = {}
    for asset_name, matches in asset_search_matches.items():
        if asset_name == st.session_state["selected_party"]:
            for match_nr, match in enumerate(matches):
                if match_nr in matches_to_analyze:
                    topics, entities = request_textrazor_data(
                        match_nr, match_context[match_nr], textrazor_key
                    )
                    topics_across_matches = topics_across_matches.append(
                        topics, ignore_index=True
                    )
                    entities_across_matches = entities_across_matches.append(
                        entities, ignore_index=True
                    )
                    # store textrazor_match_data
                    tr_match_data[match_nr] = {"topics": topics, "entities": entities}
    return tr_match_data, topics_across_matches, entities_across_matches


# ###############################
# LOAD DOCUMENTS
# ###############################
with st.spinner(
    "Einen Moment, wir laden erst einmal die Texte der verschiedenen Wahlprogramme."
):
    assets = st_read_docs_from_links()
    section1_placeholder.write(
        f"""
            ### Ok, lass uns zunächst einmal nachsehen, wie häufig die Wahlprogramme der Parteien ***{search_phrase}*** erwähnen. Mal schauen, was wir so finden :face_with_monocle:
        """
    )

# ################################
# EXECUTE SEARCH AGAINST DOCUMENTS
# ################################
with st.spinner("Einen Moment, wir führen die Suche gegen die Wahlprogramme durch."):
    asset_search_matches = st_search_against_docs(
        asset_dict=assets, search_phrase=search_phrase
    )
    match_dict = {
        asset_name: len(search_matches)
        for asset_name, search_matches in asset_search_matches.items()
    }
    search_topic_matches = (
        pd.DataFrame.from_dict(match_dict, orient="index", columns=["matches"])
        .rename_axis("doc")
        .reset_index()
    )
    match_fig = st_create_horizontal_barchart(
        chart_data=search_topic_matches,
        chart_specs=chart_specifications["search_topic_matches"],
        title_wildcards={
            "search_phrase": search_phrase,
        },
        meta_variables={"search_phrase": search_phrase},
    )
    doc_match_chart_placeholder.plotly_chart(
        match_fig, use_container_width=True, config={"displayModeBar": False}
    )

    section2_placeholder.write(
        f"""
            ### Alles klar, die oben gezeigten Parteien erwähnen ***{search_phrase}*** also mindestens einmal in ihrem Wahlprogramm.\n
            Klick auf eine Partei, um die einzelnen Ausschnitte der Wahlprogramme anzuzeigen und zu analysieren, im Kontext welcher Themen und Konzepte ***{search_phrase}*** erwähnt wird.
        """
    )

    # populate buttons for parties with >= 1 match
    i = 0
    for asset_name, matches in asset_search_matches.items():
        if len(matches) > 0:
            i = i + 1 if i < 4 else 1
            col = locals()[f"col{i}"]
            if col.button(asset_name):
                if asset_name != st.session_state["selected_party"]:
                    st.session_state["selected_party"] = asset_name
                    st.session_state["selected_topic"] = None
                    st.session_state["selected_entity"] = None

# ################################
# DISPLAY MATCHES
# ################################
if st.session_state["selected_party"] != None:
    party_matches_placeholder.write(
        f"""### Was {st.session_state["selected_party"]} zu {search_phrase} zu sagen hat:"""
    )
    topics_across_matches = topics_df.copy()
    entities_across_matches = entities_df.copy()
    with all_matches_placeholder.expander(
        "Alle einzelnen Treffer anzeigen", expanded=False
    ):
        # select random matches for subsequent Textrazor treatment
        matches_to_analyze = st_random_match_sample(
            match_dict, st.session_state["selected_party"]
        )
        # display matches; also store match context for subsequent Textrazor treatment
        match_context = {}
        for match_nr, match in enumerate(
            asset_search_matches[st.session_state["selected_party"]]
        ):
            f"#### Treffer {match_nr + 1}:\n"
            match_text = ">"
            for line_number in range(match - 5, match + 6):
                line_text = assets[st.session_state["selected_party"]][line_number]
                line_text = re.sub(
                    search_phrase,
                    f"`{search_phrase}`",
                    line_text,
                    flags=re.IGNORECASE,
                )
                match_text += f"{line_text}  \n"
            f"{match_text}"
            match_context[match_nr] = match_text

# ############################################
# EXECUTE TEXTRAZOR ANALYSIS PER MATCH
# ############################################
if st.session_state["selected_party"] != None:
    (
        tr_match_data,
        topics_across_matches,
        entities_across_matches,
    ) = st_textrazor_match_data(
        topics_across_matches,
        entities_across_matches,
        asset_search_matches,
        matches_to_analyze,
        match_context,
    )

# ############################################
# DISPLAY CHARTS FOR TOPICS AND ENTITIES
# ############################################
if st.session_state["selected_party"] != None:
    for unit in ["topics", "entities"]:
        agg_unit = (
            locals()[f"{unit}_across_matches"]
            .groupby(["label"], as_index=False)
            .agg({"match_nr": pd.Series.nunique, "score": "sum"})
        )
        agg_unit = agg_unit.nlargest(10, "score")
        fig = st_create_horizontal_barchart(
            chart_data=agg_unit,
            chart_specs=chart_specifications[unit],
            title_wildcards={
                "search_phrase": search_phrase,
                "selected_party": st.session_state["selected_party"],
            },
            meta_variables={"search_phrase": search_phrase},
        )
        locals()[f"{unit}_placeholder"].plotly_chart(
            fig, use_container_width=True, config={"displayModeBar": False}
        )
        for n, u in enumerate(agg_unit["label"].tolist()):
            col = locals()[f"{unit}_col{(n+1)%2}"]
            label = f"""{'T' if unit == 'topics' else 'K'}: {u}"""
            if col.button(label):
                if label.startswith("T"):
                    st.session_state["selected_topic"] = label.replace("T: ", "")
                if label.startswith("K"):
                    st.session_state["selected_entity"] = label.replace("K: ", "")

# ################################################
# DISPLAY MATCHES FOR SELECTED TOPICS AND ENTITIES
# ################################################
if st.session_state["selected_party"] != None and (
    st.session_state["selected_topic"] != None
    or st.session_state["selected_entity"] != None
):
    if st.session_state["selected_topic"] != None:
        with topic_match_placeholder.expander(
            f"""Treffer für {st.session_state["selected_topic"]} anzeigen""",
            expanded=False,
        ):
            for tr_match in tr_match_data.values():
                match_topics = tr_match["topics"]
                if st.session_state["selected_topic"] in match_topics["label"].unique():
                    for match_topic in match_topics["match_nr"].unique():
                        f"#### Treffer {match_topic + 1}:\n"
                        f"""{match_context[match_topic]}"""
    if st.session_state["selected_entity"] != None:
        with entity_match_placeholder.expander(
            f"""Treffer für {st.session_state["selected_entity"]} anzeigen""",
            expanded=False,
        ):
            for tr_match in tr_match_data.values():
                match_entities = tr_match["entities"]
                if (
                    st.session_state["selected_entity"]
                    in match_entities["label"].unique()
                ):
                    for match_entity in match_entities["match_nr"].unique():
                        f"#### Treffer {match_entity + 1}:\n"
                        f"""{match_context[match_entity]}"""
