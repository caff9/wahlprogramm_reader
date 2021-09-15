import streamlit as st
import pandas as pd
import re
from decouple import config

from mappings import docs, docs_colors, chart_specifications, topics_df, entities_df
from utils.doc_handler import (
    read_docs_from_links,
    search_against_docs,
    request_textrazor_data,
)
from utils.chart_builder import create_horizontal_barchart


textrazor_key = config("TEXTRAZOR")

# hide menu
st.markdown(
    """ <style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style> """,
    unsafe_allow_html=True,
)

# hide fullscreen icon
st.markdown(
    """ <style>
.css-ucv8le.e19lei0e0 {visibility: hidden;}
</style> """,
    unsafe_allow_html=True,
)


# #############################################
# DEFINTION OF FUNCTIONS USING CACHE
# #############################################
@st.cache(allow_output_mutation=True)
def st_read_docs_from_links(doc_dict):
    assets = read_docs_from_links(doc_dict)
    return assets


@st.cache
def st_search_against_docs(asset_dict, search_phrase):
    asset_search_matches = search_against_docs(asset_dict, search_phrase)
    return asset_search_matches


@st.cache
def st_create_horizontal_barchart(chart_data, chart_specs, **kwargs):
    fig = create_horizontal_barchart(chart_data, chart_specs, **kwargs)
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

# ###############################
# LOAD DOCUMENTS
# ###############################
with st.spinner(
    "Einen Moment, wir laden erst einmal die Texte der verschiedenen Wahlprogramme."
):
    assets = st_read_docs_from_links(doc_dict=docs)
    f"""
        ---
        ## Ok, lass uns zunächst einmal nachsehen, wie häufig die Wahlprogramme der Parteien ***{search_phrase}*** erwähnen. Mal schauen, was wir so finden :face_with_monocle:
    """

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
    st.plotly_chart(
        match_fig, use_container_width=True, config={"displayModeBar": False}
    )

    f"""
        ### Alles klar, die oben gezeigten Parteien erwähnen ***{search_phrase}*** also mindestens einmal in ihrem Wahlprogramm.\n
        Klick auf eine Partei, um die einzelnen Ausschnitte der Wahlprogramme anzuzeigen und zu analysieren, im Kontext welcher Themen und Konzepte ***{search_phrase}*** erwähnt wird.
    """

with st.spinner(
    "Ok, mal schauen, welche Themen und Konzepte wir finden :mag::mag::mag:"
):
    button_container = st.container()
    col1, col2, col3, col4 = button_container.columns(4)
    topics_placeholder = st.empty()
    entities_placeholder = st.empty()

    # ############################################
    # POPULATE BUTTONS FOR PARTIES WITH >= 1 MATCH
    # ############################################
    i = 0
    for asset_name, matches in asset_search_matches.items():
        if len(matches) > 0:
            i = i + 1 if i < 4 else 1
            col = locals()[f"col{i}"]
            if col.button(asset_name):

                # ############################################
                # DISPLAY MATCHES
                # ############################################
                st.session_state["selected_party"] = asset_name
                topics_across_matches = topics_df.copy()
                entities_across_matches = entities_df.copy()
                with st.expander("Einzelne Treffer anzeigen", expanded=False):
                    for match_nr, match in enumerate(matches):
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

                        # ############################################
                        # EXECUTE TEXTRAZOR ANALYSIS PER MATCH
                        # ############################################
                        if match_nr <= 3:
                            topics, entities = request_textrazor_data(
                                match_nr, match_text, textrazor_key
                            )
                            topics_across_matches = topics_across_matches.append(
                                topics, ignore_index=True
                            )
                            entities_across_matches = entities_across_matches.append(
                                entities, ignore_index=True
                            )
                            # st.dataframe(data=entities)

                # ############################################
                # DISPLAY CHARTS FOR TOPICS AND ENTITIES
                # ############################################
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
