"""
Updates tag attribute values to proper formats.
"""

import re

# Appends "Highway" if needed
def append_highway(name):
    newparts = []
    parts = name.split()
    for item in parts:
        if (item == "Interstate" or item == "States") and "Highway" not in parts:
            newparts.append(item)
            newparts.append("Highway")
        else:
            newparts.append(item)
    name = ' '.join(newparts)
    return name

# Cleans the "Farm" or "Ranch" "-to-Market" roads
def update_farm_ranch_to_market(name):
    parts = name.split()
    if "Farm-to-Market" in parts or "Ranch-to-Market" in parts:
        if "Road" in parts:
            return name
        else:
            try:
                parts.insert(parts.index("Farm-to-Market")+1, "Road")
                name = " ".join(parts)
            except ValueError:
                parts.insert(parts.index("Ranch-to-Market")+1, "Road")  
                name = " ".join(parts)
    elif "Farm" in parts and "to" in parts and "Market" in parts:
        newname = []
        for i in range(parts.index("Farm")):
            newname.append(parts[parts.index(i)])
        newname.append("Farm-to-Market")
        newname += parts[parts.index("Market")+1:]

        if "Road" in parts:
            name = " ".join(newname)
        else:
            newname.insert(newname.index("Farm-to-Market")+1,"Road")
            name = " ".join(newname)
    
    elif "Ranch" in parts and "to" in parts and "Market" in parts:
        newname = []
        for i in range(parts.index("Ranch")):
            newname.append(parts[parts.index(i)])
        newname.append("Ranch-to-Market")
        newname += parts[parts.index("Market")+1:]

        if "Road" in parts:
            name = " ".join(newname)
        else:
            newname.insert(newname.index("Ranch-to-Market")+1,"Road")
            name = " ".join(newname)
        
    return name

# Combines all cleaning/updating functions
def update_name(name, mapping):
    parts = name.split()
    newparts = []
    for item in parts:
        if item == "St" and "Rue" in parts:
            newparts.append("Saint")
        elif item == "N" or item == "C" or item == "I" or item == "H": 
            try:
                if newparts[0] == "Avenue":
                    newparts.append(item)
                else:
                    newparts.append(mapping[item])
            except IndexError:
                newparts.append(mapping[item])
        else:
            if item in mapping.keys():
                newparts.append(mapping[item])
            else:
                newparts.append(item)
    name = ' '.join(newparts)
    name = append_highway(name)
    name = update_farm_ranch_to_market(name)
    return name

# Updates phone numbers
def update_phone(number):
    phone_re = re.compile(r'^\d\d\d\-\d\d\d\-\d\d\d\d$')
    if phone_re.search(number) == None:
        phno = []
        number = list(number.lstrip("+1"))
        for char in number:
            try:
                if int(char) in [x for x in range(10)]:
                    if len(phno) == 10:
                        continue
                    phno.append(char)
            except ValueError:
                continue
        number = "".join(phno)
        number = number[:3] + "-" + number[3:6] + "-" + number[6:]
                    
    return number

# Cleans postcode values
def update_postcode(postcode):
    try:
        postcode = re.compile(r'7\d\d\d\d').search(postcode).group()
    except AttributeError:
        postcode = 'None'
    return postcode

# Cleans city values
def update_city(city, expectedcities, mapping_city):
    if city not in expectedcities:
        if city in mapping_city.keys():
            city = mapping_city[city]
        else:
            city = "None"
    return city

# Returns the element where the value of the k attribute is "addr:street"
def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")

# Returns the element where the value of the k attribute is "phone" or "contact:phone"
def is_phone(element):
    return (element.attrib['k'] == "phone" or element.attrib['k'] == "contact:phone")

# Returns the element where the value of the k attribute is "addr:postcode" or "postal_code"
def is_postcode(element):
    return (element.attrib['k'] == "addr:postcode" or element.attrib['k'] == "postal_code")

# Returns the element where the value of the k attribute is "addr:city"
def is_city(element):
    return element.attrib['k'] == "addr:city"


# Combines all update functions to fix value
def clean(value, tag, mapping_street, expectedcities, mapping_city):
    if is_street_name(tag):
        value = update_name(value, mapping_street)
    elif is_phone(tag):
        value = update_phone(value)
    elif is_postcode(tag):
        value = update_postcode(value)
    elif is_city(tag):
        value = update_city(value, expectedcities, mapping_city)
    return value

if __name__ == '__main__':
	clean("+1 512 879 9999", tag, mapping_street, expectedcities, mapping_city)