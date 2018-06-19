"""
  This module creates a sample file. It reduces its size to a better and
  faster performance. You can run this script by:

     $ python create_sample_osm.py

"""
import xml.etree.cElementTree as ET
from collections import defaultdict

OSMFILE = 'rio-de-janeiro_brazil.osm'
SAMPLE_FILE = 'rio-de-janeiro_brazil_sample.osm'

k = 10 # Parameter: take every k-th top level element

def get_element(filename, tags = ('node', 'way')):
    """
    Reference:
     http://stackoverflow.com/questions/3095434/inserting-newlines-in-xml-file-generated-via-xml-etree-
     elementtree-in-python
    """
    context = iter(ET.iterparse(filename, events=('start', 'end')))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()

with open(SAMPLE_FILE, 'wb') as output:
    # xml declaration
    output.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    # root element (opening tag for the whole document)
    output.write('<response>\n')
    # Write every kth element
    for i, element in enumerate(get_element(OSMFILE)):
        if i % k == 0:
            output.write(ET.tostring(element, encoding='utf-8'))
    # closing tag for the whole document
    output.write('</response>')
