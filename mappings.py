import pandas as pd

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

docs_colors = {
    "Bündnis 90 / Grüne": "#A8C671",
    "SPD": "#D12C24",
    "CDU / CSU": "#1A1919",
    "FDP": "#D32F7C",
    "Die Linke": "#A32A4D",
    "Volt": "#3F2C69",
    "Freie Wähler": "#1C508E",
    "Die PARTEI": "#97353A",
    "Piratenpartei": "#EB8F35",
    "ÖDP": "#DF772D",
    "V-Partei": "#52672F",
}

chart_specifications = {
    "search_topic_matches": {
        "label": "doc",
        "value": "matches",
        "marker_color_list": list(docs_colors.values()),
        "meta_template": "{search_phrase}",
        "hovertemplate": "<extra></extra>%{y} erwähnt %{meta} %{x} mal in ihrem Wahlprogramm.",
        "chart_title": "Anzahl Erwähnungen von <b>{search_phrase}</b> nach Partei",
    },
    "topics": {
        "label": "label",
        "value": "match_nr",
        "color_col": "match_nr",
        "colorscale": "blues",
        "meta_template": "{search_phrase}",
        "hovertemplate": "<extra></extra>%{meta} wird %{x} mal im Kontext von %{y} erwähnt.",
        "chart_title": "Top 10 Themen, in deren Kontext <b>{search_phrase}</b><br>von <b>{selected_party}</b> erwähnt wird",
    },
    "entities": {
        "label": "label",
        "value": "match_nr",
        "color_col": "match_nr",
        "colorscale": "blues",
        "meta_template": "{search_phrase}",
        "hovertemplate": "<extra></extra>%{meta} wird %{x} mal im Kontext von %{y} erwähnt.",
        "chart_title": "Top 10 Konzepte, in deren Kontext <b>{search_phrase}</b><br>von <b>{selected_party}</b> erwähnt wird",
    },
}

topics_df = pd.DataFrame(
    columns=[
        "match_nr",
        "topic_result_id",
        "label",
        "score",
        "wikiLink",
    ]
)

entities_df = pd.DataFrame(
    columns=[
        "match_nr",
        "entity_result_id",
        "label",
        "type",
        "freebase_types",
        "score",
        "relevanceScore",
        "wikiLink",
    ]
)
