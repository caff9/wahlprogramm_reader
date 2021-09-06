import streamlit as st
import requests
import fitz
import tempfile
import plotly.graph_objects as go
import re
from itertools import count


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
def create_match_histogram(asset_search_matches):
    """
    Checks a dictionary of matches and returns a histogram.

    Parameters
    ----------
    asset_search_matches : dict

    Returns
    -------
    Plotly figure
    """
    match_dict = {}
    for asset_name, search_matches in asset_search_matches.items():
        match_dict[asset_name] = len(search_matches)
    fig = go.Figure(
        data=go.Bar(
            x=list(match_dict.keys()),
            y=list(match_dict.values()),
            text=list(match_dict.values()),
            textposition="outside",
        )
    )
    match_histogram = fig
    return match_histogram


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

docs = {
    "Bündnis 90 / Grüne": "https://cms.gruene.de/uploads/documents/Wahlprogramm-DIE-GRUENEN-Bundestagswahl-2021_barrierefrei.pdf",
    "SPD": "https://www.spd.de/fileadmin/Dokumente/Beschluesse/Programm/SPD-Zukunftsprogramm.pdf",
    "CDU / CSU": "https://www.csu.de/common/download/Regierungsprogramm.pdf",
    "FDP": "https://www.fdp.de/sites/default/files/2021-06/FDP_Programm_Bundestagswahl2021_1.pdf",
    "Die Linke": "https://www.die-linke.de/fileadmin/download/wahlen2021/Wahlprogramm/DIE_LINKE_Wahlprogramm_zur_Bundestagswahl_2021.pdf",
    "Volt": "https://assets.volteuropa.org/2021-06/Wahlprogramm%20Langversion.pdf",
    "Freie Wähler": "https://www.freiewaehler.eu/template/elemente/203/FREIE%20WÄHLER_Wahlprogramm-BTW21.pdf",
    "Die PARTEI": "https://spitzenkandidatinnen.sh/file.php/btw21/wahlprogramm-btw21_online.pdf",
    "Piratenpartei": "https://wiki.piratenpartei.de/wiki/images/9/9e/Wahlprogramm_zur_Bundestagswahl_2021_der_Piratenpartei_Deutschland.pdf",
    "ÖDP": "https://www.oedp.de/fileadmin/user_upload/bundesverband/programm/programme/OEDPWahlprogrammBundestagswahl2021.pdf",
    "V-Partei": "https://v-partei.de/wp-content/uploads/V-Partei³-Wahlprogramm-BTW-2021.pdf",
}

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
    match_histogram = create_match_histogram(asset_search_matches=asset_search_matches)

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
                with st.expander("Treffer anzeigen", expanded=True):
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
