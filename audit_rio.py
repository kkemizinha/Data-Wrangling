# -*- coding: utf-8 -*-
"""
  This module audits the data from OSM map file.
  You can run this script by using the following command:

    $ python audit_rio.py
"""
import re
import json
import xml.etree.cElementTree as ET
from collections import defaultdict
import pprint

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
removechars_streetname = re.compile(r'[=\+\&<>;\"\?%#$@\,\t\r\n]', re.IGNORECASE)
fixme_list = []

expected_street = ["Rua", "Avenida", "Rodovia", u"Praça", "Alameda", "Estrada",
                   "Praia", "Travessa", "Ladeira"]
expected_city = ["Rio de Janeiro", u"Niterói", u"Nilópolis", u"Teresópolis",
                 u"Petrópolis", u"Nova Iguaçu", u"Itaboraí", u"São Gonçalo",
                 u"Duque de Caxias", "Belford Roxo", u"São João de Meriti",
                 u"Magé", u"Mesquita", u"Maricá", "Queimados", u"Itaguaí",
                 "Japeri", u"Seropédica", "Rio Bonito", "Guapimirim",
                 "Cachoeiras de Macacu", "Paracambi", u"Tanguá"]

SAMPLE_FILE = 'rio-de-janeiro_brazil_sample.osm'

def audit_city(city):
    """
    1) Checks if the city is in the expected city list
    2) If not, it adds the city to the audit fix me list

    Input:
        city: city name
    Returns:
        No returns
    """
    if city not in expected_city:
        error = u"Problem with City: {}".format(city)
        audit_fixme(error)

def audit_street_type(street):
    """
    1) Gets the first substring from street
    2) If it is not in the expected street type,
       it adds the title to the audit fix me list

    Input:
        street: street name
    Returns:
        No returns
    """
    title = street.split(' ')[0]
    if title not in expected_street:
        error = u"Problem with Street type: {}".format(street)
        audit_fixme(error)

def audit_street_special(street_name):
    """
    1) Search for special characters

    Input:
        street_name: street name
    Returns:
        No returns
    """
    if removechars_streetname.search(street_name):
        error = u"Problem with Street Name: {}".format(street_name)
        audit_fixme(error)

def audit_fixme(fixme):
    """
    1) Gets the error phrase string

    Input:
        fixme: error phrase string
    Returns:
        No returns
    """
    fixme_list.append(fixme)

def audit(osmfile):
    """
    1) Checks errors from each node from the XML file
    2) It writes a txt file with the errors that were found

    Input:
        osmfile: OSM file
    Returns:
        No returns
    """
    osm_file = open(osmfile, "r")
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if tag.attrib['k'] == "addr:street":
                    audit_street_special(tag.attrib['v'])
                    audit_street_type(tag.attrib['v'])
                if tag.attrib['k']  == "addr:city":
                    audit_city(tag.attrib['v'])
    f = open( 'fixme.txt', 'w' )
    test = '\n'.join(fixme_list).encode('utf-8').strip()
    f.write( test )
    f.close()
    osm_file.close()

if __name__ == '__main__':
    audit(SAMPLE_FILE)
