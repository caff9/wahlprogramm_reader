import requests
import fitz
import tempfile
import textrazor
import pandas as pd
import json


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
            for line_number, line_text in enumerate(doc_text.splitlines()):
                asset_dict[line_number] = line_text
            return_dict[asset_name] = asset_dict
    return return_dict


def store_docs_as_json(docs):
    with open("doc_data.json", "w", encoding="utf8") as json_dump:
        json.dump(assets, json_dump, sort_keys=True, indent=4, ensure_ascii=False)


def read_docs_from_json():
    """
    Reads docs from json file. For performance purposes only.

    Returns
    -------
    dict
        A dict with doc_name as key. Contains a nested dict of structure
        line_number: line_text.
    """
    asset_dict = json.load(open("doc_data.json"))
    asset_dict = {
        k: {int(kk): vv for kk, vv in v.items()} for k, v in asset_dict.items()
    }
    return asset_dict


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


def request_textrazor_data(match_nr, text_to_analyze, api_key):
    textrazor.api_key = api_key
    tr_client = textrazor.TextRazor(extractors=["entities", "topics", "categories"])
    response = None
    topic_df = pd.DataFrame(
        columns=["match_nr", "topic_result_id", "label", "score", "wikiLink"]
    )
    entity_df = pd.DataFrame(
        columns=[
            "match_nr",
            "entity_result_id",
            "label",
            "type",
            "score",
        ]
    )

    try:
        response = tr_client.analyze(text_to_analyze)
    except textrazor.TextRazorAnalysisException:
        pass
    if response:
        if response.topics():
            for topic_n, topic in enumerate(response.topics()):
                topic_data = topic.json
                topic_df = topic_df.append(
                    {
                        "match_nr": match_nr,
                        "topic_result_id": topic_n,
                        "label": topic_data["label"],
                        "score": topic_data["score"],
                        "wikiLink": topic_data["wikiLink"],
                    },
                    ignore_index=True,
                )
        if response.entities():
            for entity_n, entity in enumerate(response.entities()):
                entity_data = entity.json
                # catch missing values
                try:
                    entity_type = str(entity_data["type"])
                except KeyError:
                    entity_type = "type unknown"
                # build df
                entity_df = entity_df.append(
                    {
                        "match_nr": match_nr,
                        "entity_result_id": entity_n,
                        "label": entity_data["entityId"],
                        "type": entity_type,
                        "score": entity_data["confidenceScore"],
                    },
                    ignore_index=True,
                )
            # filter irrelevant entity types
            entity_df = entity_df[entity_df["type"] != "['Number']"]
    return topic_df, entity_df
