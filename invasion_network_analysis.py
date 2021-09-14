import glob
import json
import logging
import os
import pandas as pd
import subprocess
import xml.etree.ElementTree as ET
from pprint import pprint

from bs4 import BeautifulSoup
from pyvis.network import Network

logging.basicConfig(level=logging.INFO)
metadata_dictionary = {}

def querying_pygetpapers_sectioning(query, hits, output_directory, using_terms=False, terms_txt=None):

    logging.info('querying pygetpapers')
    if using_terms:
        subprocess.run(f'pygetpapers -q "{query}" -k {hits} -o {output_directory} -x --terms {terms_txt} --logfile pygetpapers_log.txt',
                       shell=True)
    else:
        subprocess.run(f'pygetpapers -q "{query}" -k {hits} -o {output_directory} -x  --logfile pygetpapers_log.txt',
                       shell=True)
    logging.info('running ami section')
    subprocess.run(f'ami -p {output_directory} section', shell=True)

def get_metadata_json(output_directory):
    WORKING_DIRECTORY = os.getcwd()
    glob_results = glob.glob(os.path.join(WORKING_DIRECTORY,
                                          output_directory, "*", 'eupmc_result.json'))
    metadata_dictionary["metadata_json"] = glob_results
    logging.info(f'metadata found for {len(metadata_dictionary["metadata_json"])} papers')

def get_title(metadata_dictionary=metadata_dictionary):
    metadata_dictionary["title"] = []
    for metadata in metadata_dictionary["metadata_json"]:
        with open(metadata) as f:
            metadata_in_json = json.load(f)
            try:
                metadata_dictionary["title"].append(
                    metadata_in_json["full"]["title"])
            except KeyError:
                metadata_dictionary["title"].append('NaN')
    logging.info('getting title')

def get_PMCIDS(metadata_dictionary=metadata_dictionary):
    metadata_dictionary["PMCIDS"] = []
    for metadata in metadata_dictionary["metadata_json"]:
        with open(metadata) as f:
            metadata_in_json = json.load(f)
            try:
                metadata_dictionary["PMCIDS"].append(
                    metadata_in_json["full"]["pmcid"])
            except KeyError:
                metadata_dictionary["PMCIDS"].append('NaN')
    logging.info('getting PMCIDs')

def get_citation(output_directory, metadata_dictionary=metadata_dictionary):
    metadata_dictionary["cit"] = []
    for pmc in metadata_dictionary["PMCIDS"]:
        citation_list = []
        WORKING_DIRECTORY = os.getcwd()
        glob_results = glob.glob(os.path.join(WORKING_DIRECTORY,
                                            output_directory, pmc, '**','*ref.xml' ), recursive=True)
        for citation in glob_results:
            file = open(citation, "r", encoding='utf8')
            contents = file.read()
            soup = BeautifulSoup(contents, 'xml')
            title = soup.find('article-title')
            try:
                title_text = title.get_text()
                title_text = " ".join(title_text.split())
                title_text = title_text.replace('\n', ' ')
                citation_list.append(title_text)
            except AttributeError:
                pass
        metadata_dictionary["cit"].append(citation_list)

def creating_edges(metadata_dictionary=metadata_dictionary):
    metadata_dictionary["edge_tupule_list"] = []
    for title in metadata_dictionary["title"]: 
        tupule_list = []
        #metadata_dictionary["edge_tupule_list"]["ind"] = []
        for citation_list in metadata_dictionary["cit"]:
            for citation in citation_list:
                edge_tupule = (title, citation,)
                tupule_list.append(edge_tupule)
        metadata_dictionary["edge_tupule_list"].append(tupule_list)
    logging.info('getting the citations')

def flatten_list(metadata_dictionary=metadata_dictionary):
    flat_list = []
    for sublist in metadata_dictionary["edge_tupule_list"]:
        for item in sublist:
            flat_list.append(item)
    logging.info('flatenning the list of citations')
    return flat_list

def create_source_and_target(metadata_dictionary=metadata_dictionary, path = 'source_target.csv'):
    citation_list = flatten_list()
    source_target = pd.DataFrame(list(citation_list))
    source_target.to_csv(path, encoding='utf-8')


def graph_analysis(metadata_dictionary=metadata_dictionary):
    logging.info('working on the graph')
    net = Network()
    citation_list = flatten_list()
    nodes = list(set(metadata_dictionary["title"] + citation_list))
    net.add_nodes(nodes)
    logging.info('finished added nodes')
    for tupule_list in metadata_dictionary["edge_tupule_list"]:
        net.add_edges(tupule_list)
    logging.info('finished adding edges')
    net.show('nodes_2.html')
    logging.info('done creating the graph')

def convert_to_csv(path='citations.csv', metadata_dictionary=metadata_dictionary):
    df = pd.DataFrame(metadata_dictionary)
    df.to_csv(path, encoding='utf-8', line_terminator='\r\n')
    logging.info(f'writing the keywords to {path}')

HOME = os.path.expanduser("~")
CPROJECT = os.path.join(HOME,'network_analysis', 'invasion_25')
#querying_pygetpapers_sectioning("('invasion biology')", 25, 'invasion_25')
get_metadata_json(CPROJECT)
get_PMCIDS()
get_title()
get_citation(CPROJECT)
creating_edges()
create_source_and_target()
#convert_to_csv(metadata_dictionary=graph_dict)
#graph_analysis()
