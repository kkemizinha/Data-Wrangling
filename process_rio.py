#!/usr/bin/python
 # -*- coding: utf-8 -*-
"""
This code is responsible to prepare the data to the DB.

To run this code:

    $python process_rio.py

The output have this format as in Guidelines:

    {'node': {'id': 757860928,
              'user': 'uboot',
              'uid': 26299,
           'version': '2',
              'lat': 41.9747374,
              'lon': -87.6920102,
              'timestamp': '2010-07-22T16:16:51Z',
          'changeset': 5288876},
     'node_tags': [{'id': 757860928,
                    'key': 'amenity',
                    'value': 'fast_food',
                    'type': 'regular'},
                   {'id': 757860928,
                    'key': 'cuisine',
                    'value': 'sausage',
                    'type': 'regular'},
                   {'id': 757860928,
                    'key': 'name',
                    'value': "Shelly's Tasty Freeze",
                    'type': 'regular'}]}

"""

import xml.etree.cElementTree as ET
from collections import defaultdict
import pprint
import re
import csv
import codecs
import os, sys

OSMFILE = 'rio-de-janeiro_brazil_sample.osm'

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

expected_street = ["Rua", "Avenida", "Beco", "Rodovia", "Expressa", u"Praça",
                   "Alameda", "Praia", "Travessa", "Ladeira", "Via"]

mapping = { "Av.": "Avenida",
            "Av": "Avenida",
            "Rod.": "Rodovia",
            "Al.": "Alameda",
            "R.": "Rua",
            "Praca" : u"Praça",
            "Largo do Machado": u"Praça Largo do Machado"
            }

mapping_city = { "Teresópoli":"Teresópolis",
                 "Rua Monsenhor Magaldi":"Rio de Janeiro"
               }

def is_city_name(name):
    """
    For each key "K", verifies if it's a city

    Args:
        name: node from XML file
    Returns:
        True ou False
    """
    return (name == "addr:city")

def update_city_name(name, mapping):
    """
    1) Capitalize the first letter
    2) Remove special characters (',')
    3) Replace the data

    Input:
        name: City
        mapping: Dictionary of cities
    Returns:
        Corrected name
    """
    name = name.title()
    name = name.replace(',', '')
    if name in mapping:
        name = mapping[name]
    return name

def is_street_name(name):
    """
    For each key "K", verifies if it's a street

    Args:
        name: node from XML file
    Returns:
        True ou False
    """
    return (name == "addr:street")

def update_street_name(name, mapping, expected_street):
    """
    1) Identifies the first string
    2) Verifies if it is in the accepted list
    3) Clean the data

    Input:
        name: Street
        mapping: Dictionary of streets
        expected_street: Accepted street types
    Returns:
        Corrected name
    """
    street_type_re = re.compile(r'^\b(?u)\w\S+\.?', re.IGNORECASE)

    name = name.title()
    m = street_type_re.search(name)
    if m:
        street_type = m.group()

        if street_type not in expected_street:
            try:
                name = re.sub(street_type_re, mapping[street_type], name)
            except:
                name = "Rua " + name

    return name

def update_street_middle(name, mapping):
    """
    1. Identifies the second string in the street name
    2. Replaces the string for a new value

    Input:
        name: Street name
        mapping: Dictionary of accepted words
    Returns:
        Formatted string
    """
    title = name.split()[1]

    if title.endswith("."):
        if mapping[title]:
            name = name.replace(title,mapping[title])

    return name

def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """
    1. Clean and shape node or way XML element to Python dict

    Input:
        element: XML elements (node, way)
    Returns:
        Python dict
    """

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []

    if element.tag == 'node':
        for attrib in element.attrib:
            if attrib in NODE_FIELDS:
                node_attribs[attrib] = element.attrib[attrib]
        for child in element:
            node_tag = {}

            if is_street_name(child.attrib['k']):
                better_name = update_street_name(child.attrib['v'], mapping, expected_street)
                child.attrib['v'] = update_street_middle(better_name, mapping)

            if is_city_name(child.attrib['k']):
                #print child.attrib['v']
                child.attrib['v'] = update_city_name(child.attrib['v'], mapping_city)

            if LOWER_COLON.match(child.attrib['k']):
                node_tag['type'] = child.attrib['k'].split(':',1)[0]
                node_tag['key'] = child.attrib['k'].split(':',1)[1]
                node_tag['id'] = element.attrib['id']
                node_tag['value'] = child.attrib['v']
                tags.append(node_tag)
            elif PROBLEMCHARS.match(child.attrib['k']):
                continue
            else:
                node_tag['type'] = 'regular'
                node_tag['key'] = child.attrib['k']
                node_tag['id'] = element.attrib['id']
                node_tag['value'] = child.attrib['v']
            tags.append(node_tag)
        return {'node': node_attribs, 'node_tags': tags}

    elif element.tag == 'way':
        for attrib in element.attrib:
            if attrib in WAY_FIELDS:
                way_attribs[attrib] = element.attrib[attrib]

        position = 0
        for child in element:
            way_tag = {}
            way_node = {}

            if child.tag == 'tag':

                if is_city_name(child.attrib['k']):
                    #print child.attrib['v']
                    child.attrib['v'] = update_city_name(child.attrib['v'], mapping_city)

                if is_street_name(child.attrib['k']):
                    better_name = update_street_name(child.attrib['v'], mapping, expected_street)
                    child.attrib['v'] = update_street_middle(better_name, mapping)

                if LOWER_COLON.match(child.attrib['k']):
                    way_tag['type'] = child.attrib['k'].split(':',1)[0]
                    way_tag['key'] = child.attrib['k'].split(':',1)[1]
                    way_tag['id'] = element.attrib['id']
                    way_tag['value'] = child.attrib['v']
                    tags.append(way_tag)

                elif PROBLEMCHARS.match(child.attrib['k']):
                    continue

                else:
                    way_tag['type'] = 'regular'
                    way_tag['key'] = child.attrib['k']
                    way_tag['id'] = element.attrib['id']
                    way_tag['value'] = child.attrib['v']
                    tags.append(way_tag)

            elif child.tag == 'nd':
                way_node['id'] = element.attrib['id']
                way_node['node_id'] = child.attrib['ref']
                way_node['position'] = position
                position += 1
                way_nodes.append(way_node)

        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


def get_element(osm_file, tags=('node', 'way', 'relation')):
    """
       1. Yield element if it is the right type of tag

        Input:
            osm_file: OSM map file
        Returns:
            No returns
    """

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()

class UnicodeDictWriter(csv.DictWriter, object):

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

def process_map(file_in):
    """
       Iteratively process each XML element and write to csv(s)

    Input:
        file_in: OSM map file
    Returns:
        No returns. It only writes CSV outputs

    """

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
        codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        #validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])

if __name__ == '__main__':
    process_map(OSMFILE)
