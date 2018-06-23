import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET
import cerberus
import schema

### FILE PATHS
OSM_PATH = "sample.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

### AUDIT FILE PATHS
NODES_KEYS_AUDIT_PATH = "nodes_keys_audit.csv"
NODES_TYPES_AUDIT_PATH = "nodes_types_audit.csv"
NODES_VALUES_AUDIT_PATH = "nodes_values_audit.csv"
WAYS_KEYS_AUDIT_PATH = "ways_keys_audit.csv"
WAYS_TYPES_AUDIT_PATH = "ways_types_audit.csv"
WAYS_VALUES_AUDIT_PATH = "ways_values_audit.csv"

### REGULAR EXPRESSIONS
LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
STREET_TYPE_RE = re.compile(r'\b\S+\.?$', re.IGNORECASE)
PHONE_NUMBER_RE = re.compile(r'^(\+?1)?[\s.-]?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}$')

### SCHEMA
SCHEMA = schema.schema

### XML TAG ATTRIBUTES (i.e. FIELDS)
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

### AUDITING DICTIONARIES & LISTS:
nodes_audit_keys = {}
nodes_audit_types = {}
nodes_audit_values = {}
NODES_KEYS_AUDIT_FIELDS = []
NODES_TYPES_AUDIT_FIELDS = []
NODES_VALUES_AUDIT_FIELDS = []
ways_audit_keys = {}
ways_audit_types = {}
ways_audit_values = {}
WAYS_KEYS_AUDIT_FIELDS = []
WAYS_TYPES_AUDIT_FIELDS = []
WAYS_VALUES_AUDIT_FIELDS = []

### CLEANING DICTIONARIES & LISTS:
street_names_dict = {"Rd.": "Road", "Rd": "Road", "Dr.": "Drive", "Dr": "Drive", "Ave.": "Avenue", "Ave": "Avenue", "St.": "Street", "St": "Street", "Ln.": "Lane", "Ln": "Lane", "Ct.": "Court", "Ct": "Court", "Blvd.": "Boulevard", "Blvd.": "Boulevard", "Cir.": "Circle", "Cir": "Circle", "Pwky.": "Parkway", "Pwky": "Parkway", "Wy.": "Way", "Wy": "Way", "Pl.": "Place", "Pl": "Place"}
expected_street_names = ["Road", "Drive", "Avenue", "Street", "Lane", "Court", "Boulevard", "Circle", "Parkway", "Way", "Place", "Mall"]

# ================================================== #
#              Data Auditing Functions               #
# ================================================== #

def audit(tags, audit_keys, audit_types, audit_values):
    for el in tags:
      audit_count(audit_keys, el['key'])
      audit_count(audit_types, el['type'])
      audit_count(audit_values, el['value'])

### Used to count the number of occurrences of individual objects subject to auditing
def audit_count(dic, obj):
    if obj not in dic.keys():
      dic[obj] = 1
    else:
      dic[obj] = dic[obj] + 1

### Orders audit data by number of occurrences (ascending) then writes to given file path
def write_audit_file(dic, file_path, AUDIT_FIELDS):
    AUDIT_FIELDS = sorted(dic, key=dic.__getitem__)
    newdic = {}
    for field in AUDIT_FIELDS:
      newdic[field] = dic[field]
    with codecs.open(file_path, 'w') as f:
      writer = UnicodeDictWriter(f, AUDIT_FIELDS)
      writer.writeheader()
      writer.writerow(newdic)


# ================================================== #
#             Data Cleaning Functions                #
# ================================================== #

def check_for_unfilled(attribs):
    for field in NODE_FIELDS:
          if field not in attribs.keys():
            if field == 'uid': ### -1 is our unique identifier since all other uid entries are positive integers
              attribs[field] = -1 
            if field == 'user': ### "" is our unique identifier since all other user entries are non-empty strings
              attribs[field] = ""
    return attribs

def correct_phone_numbers(key, phone):
    if PHONE_NUMBER_RE.match(phone):
      result = re.sub('[^0-9]','', phone)
      if len(result) > 10:
        result = result[-10:]
      return [key, result]
    else:
      return ['phone_irregular', phone]

### Checks if street name ends with an abbreviation (in which case it replaces it using street_name_dict) or simply prints full street names with unusual endings 
def clean_street_names(dic):
    if (dic['type'] == 'addr') & (dic['key'] == 'street'): 
      if STREET_TYPE_RE.search(dic['value']):
        street_type = STREET_TYPE_RE.search(dic['value']).group()
        if street_type not in expected_street_names:
          if street_type in street_names_dict.keys():
            dic['value'] = street_names_dict[street_type]

def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  

    ### NODES
    if element.tag == 'node':
        tags = []
        for field in element.attrib.keys():
          if field in NODE_FIELDS:
            if element.get(field) != None:
              node_attribs[field] = element.get(field)
        
        node_attribs = check_for_unfilled(node_attribs) ### CHECK FOR UNFILLED FIELDS (DATA CLEANING)

        ### NODES_TAGS
        for tag in element.iter('tag'):
          dic = {}
          dic['id'] = node_attribs['id']
          if not PROBLEMCHARS.match(tag.get('k')):
              if LOWER_COLON.match(tag.get('k')):
                  x = tag.get('k')
                  index = x.find(':')
                  dic['key'] = x[index+1:]
                  dic['type'] = x[0:index]
                  dic['value'] = tag.get('v')
              else:
                  dic['key'] = tag.get('k')
                  dic['type'] = 'regular'
                  dic['value'] = tag.get('v')

              clean_street_names(dic) ### Clean street names (DATA CLEANING)

              if dic['key'] == 'phone': ### Clean irregular phone numbers (DATA CLEANING)
                  cleaned_phone_info = correct_phone_numbers(dic['key'], dic['value'])
                  dic['key'] = cleaned_phone_info[0]
                  dic['value'] = cleaned_phone_info[1]

              tags.append(dic)
                
        return {'node': node_attribs, 'node_tags': tags}
        
    ### WAYS
    elif element.tag == 'way':
        tags = []
        
        for field in element.attrib.keys():
            if field in WAY_FIELDS:
                if element.get(field) != None:
                    way_attribs[field] = element.get(field)
        
        way_attribs = check_for_unfilled(way_attribs) ### CHECK FOR UNFILLED FIELDS (DATA CLEANING)

        ### WAYS_TAGS
        for tag in element.iter('tag'):
            dic = {}
            dic['id'] = way_attribs['id']
            if not PROBLEMCHARS.match(tag.get('k')):
                if LOWER_COLON.match(tag.get('k')):
                    x = tag.get('k')
                    index = x.find(':')
                    dic['key'] = x[index+1:]
                    dic['type'] = x[0:index]
                    dic['value'] = tag.get('v')
                else:
                    dic['key'] = tag.get('k')
                    dic['type'] = 'regular'
                    dic['value'] = tag.get('v')
                
                clean_street_names(dic) ### Clean street names (DATA CLEANING)

                if dic['key'] == 'phone': ### Clean irregular phone numbers (DATA CLEANING)
                  cleaned_phone_info = correct_phone_numbers(dic['key'], dic['value'])
                  dic['key'] = cleaned_phone_info[0]
                  dic['value'] = cleaned_phone_info[1]
                tags.append(dic)
            
        ###WAYS_NODES
        position = 1
        for tag in element.iter('nd'):
            nodedic = {}
            nodedic['id'] = way_attribs['id']    
            nodedic['node_id'] = tag.get('ref')
            nodedic['position'] = position
            way_nodes.append(nodedic)
            position += 1
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# ================================================== #
#               Helper Functions                     #
# ================================================== #

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
        error_string = pprint.pformat(errors)
        print element
        raise Exception(message_string.format(field, error_string))

class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #

def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

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

        validator = cerberus.Validator()

        count = 1
        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            #print count 
            count += 1
            if el:
                if validate is True:
                    validate_element(el, validator)
                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                    audit(el['node_tags'], nodes_audit_keys, nodes_audit_types, nodes_audit_values) ### AUDITING PROCESS
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])
                    audit(el['way_tags'], ways_audit_keys, ways_audit_types, ways_audit_values) ### AUDITING PROCESS

        ### WRITE NODES_TAGS AUDIT FILES
        write_audit_file(nodes_audit_keys, NODES_KEYS_AUDIT_PATH, NODES_KEYS_AUDIT_FIELDS)
        write_audit_file(nodes_audit_types, NODES_TYPES_AUDIT_PATH, NODES_TYPES_AUDIT_FIELDS)
        write_audit_file(nodes_audit_values, NODES_VALUES_AUDIT_PATH, NODES_VALUES_AUDIT_FIELDS)
        ### WRITE WAYS_TAGS AUDIT FILES
        write_audit_file(ways_audit_keys, WAYS_KEYS_AUDIT_PATH, WAYS_KEYS_AUDIT_FIELDS)
        write_audit_file(ways_audit_types, WAYS_TYPES_AUDIT_PATH, WAYS_TYPES_AUDIT_FIELDS)
        write_audit_file(ways_audit_values, WAYS_VALUES_AUDIT_PATH, WAYS_VALUES_AUDIT_FIELDS)


if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. 
    process_map(OSM_PATH, validate=False)