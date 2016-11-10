
"""
This program parses the elements of the OSM XML file, transforms them from document format to tabular format, thus making it possible to write to csv files. The csv files can then be imported to a SQL database as tables.

The process for this transformation is as follows:
- Use iterparse to iteratively step through each top level element in the XML
- Shape each element into several data structures using a custom function
- Utilize a schema and validation library to ensure the transformed data is in the correct format
- Write each data structure to the appropriate .csv files
"""

import csv
import codecs
import re
import xml.etree.cElementTree as ET
import cerberus
import schema
from clean import clean
import mapping_street
import cities


OSM_FILE = "austin_texas.osm"
SAMPLE_FILE = "sample.osm"
SMALL_OSM_FILE = "expectederror_file_smaller.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.SCHEMA
mapping_street = mapping_street.mapping_street
expectedcities = cities.expectedcities
mapping_city = cities.mapping_city

NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS= ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, lower_colon=LOWER_COLON, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements)

    if element.tag == 'node':
        for field in node_attr_fields:
            
            # Makes sure that the empty fields are field with appropriate values:
            if element.attrib[field] == '':
                node_attribs[field] = '999999'
            else:
                node_attribs[field] = element.attrib[field]
    
        for tag in element.iter("tag"):
            nodetags = {}
            if element.attrib['id'] == '':
                nodetags['id'] = '999999'
            else:
                nodetags['id'] = element.attrib['id']
                
            # Adding the nodetags['type'] and nodetags['key'] values and fixing them:
            
            if problem_chars.search(tag.attrib['k']) != None:
                continue  # any k values with problematic characters are ignored/removed
                
            else:
                if lower_colon.search(tag.attrib['k']) != None:
                    kvalue = tag.attrib['k'].split(":")
                    nodetags['type'] = kvalue[0]  # the first string becomes the type
                    
                    if len(kvalue) == 2:                        
                        nodetags['key'] = kvalue[1] # the second string (if there's only one colon, 
                                                    # becomes the key value
                    else:
                        nodetags['key'] = ':'.join(kvalue[1:]) # if there are more than one colon, 
                                                               # the rest are joined to become the key value
                        
                else:
                    nodetags['type'] = default_tag_type
                    nodetags['key'] = tag.attrib['k']
            
            if tag.attrib['v'] == '':
                nodetags['value'] == 'None' # makes sure that if the field is empty, it is field with 'None' (str)
                
            else:
                # cleaning of v attributes values:
                nodetags['value'] = clean(tag.attrib['v'], tag, mapping_street, expectedcities, mapping_city)
                
            tags.append(nodetags)
        
        return {'node': node_attribs, 'node_tags': tags}

    elif element.tag == 'way':
        for field in way_attr_fields:
            if element.attrib[field] == '':
                way_attribs[field] = '999999'
            else:
                way_attribs[field] = element.attrib[field]
        
        for tag in element.iter("tag"):
            waytags = {}
            if element.attrib['id'] == '':
                waytags['id'] = '999999'
            else:
                waytags['id'] = element.attrib['id']
           
            if problem_chars.search(tag.attrib['k']) != None:
                continue
            else:
                if lower_colon.search(tag.attrib['k']) != None:
                    kvalue = tag.attrib['k'].split(":")
                    waytags['type'] = kvalue[0]

                    if len(kvalue) == 2:
                        waytags['key'] = kvalue[1]
                        
                    else:
                        waytags['key'] = ':'.join(kvalue[1:])
                
                else:
                    waytags['type'] = default_tag_type
                    waytags['key'] = tag.attrib['k']
                    
            if tag.attrib['v'] == '':
                waytags['value'] = 'None'
            else:
                waytags['value'] = clean(tag.attrib['v'], tag, mapping_street, expectedcities, mapping_city)
        
            tags.append(waytags)
                
        position = 0
        for waytag in element.iter("nd"):
            waynd = {}
            if element.attrib['id'] == '':
                waynd['id'] = '999999'
            else:
                waynd['id'] = element.attrib['id']
            if waytag.attrib['ref'] == '':
                waynd['node_id'] = '999999'
            else:
                waynd['node_id'] = waytag.attrib['ref']

            waynd['position'] = position
            position += 1
            
            way_nodes.append(waynd)
        
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}

def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()

def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_strings = (
            "{0}: {1}".format(k, v if isinstance(v, str) else ",".join(v))
            for k, v in errors.iteritems()
        )                 
        raise cerberus.ValidationError(
            message_string.format(field, "\n".join(error_strings))
        )

class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, codecs.open(WAYS_PATH, 'w') as ways_file, codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:
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

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])

if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(SMALL_OSM_FILE, validate=True)


