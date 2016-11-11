# OpenStreetMap Data for Austin, TX

## Map Area

Austin, TX USA

https://mapzen.com/data/metro-extracts/metro/austin_texas/

This area is more familiar to me at the moment so I chose it. It also meets the project requirements of having at least 50 MB file size uncompressed. As delineated in class, the data was obtained by downloading the readily available extract above. Uncompressing the file gave a 1.4 GB osm file. A sample of this file was generated using the code provided in the instructions for the project. The link to this smaller osm file is:

https://www.dropbox.com/s/084lnztuwgxdgtm/sample.osm?dl=0

## Problems Encountered in the Map

Exploration of the sample osm file as well as the whole osm file showed that:

1. Street names need to be unabbreviated. 
2. Inconsistent abbreviation for street names poses challenge in cleaning data (ex: IH35, I H 35, I-35, I35)
3. Phone number format is not consistent (ex: (512) 782-5659, +1 512-472-1666, 51224990093, 512 466-3937, etc.)
4. More than one phone number are entered in the field (ex: "Main: (512) 899-4300 Catering: (512) 899-4343")
5. Postcodes didn't have a consistent format--some have county codes, some do not. 
6. City name format is not consistent (ex: Pflugerville, TX; Pflugerville)

### Cleaning of Street Names

Using the method described in the case study exercises for the course. However, the result from the audit showed that aside from the fact that some street names are heavily abbreviated, some street names are abbreviated inconsistently. In this project, the "update_name" function introduced in the case study exercises was modified by adding subfunctions and other lines of code, to successfully update the street names. Examples of updates done are:

    North IH 35 => North Interstate Highway 35
    South I 35 => South Interstate Highway 35
    Calhoun Ln => Calhoun Lane
    FM 685 => Farm-to-Market Road 685
    W. University Avenue,Ste 320 => West University Avenue Suite 320

The function was able to distinguish between some abbreviations:

    Avenue H => Avenue H (H stayed the same)
    N I H 35 Bldg 7 => North Interstate Highway 35 Building 7 (H was converted to Highway)

However, after the updates, there were still some problems remaining after the clean up, such as certain streets have different names. For example, Ranch Road 620 is also referred to as Farm-to-Market Road 620, US Highway 290 is also Country Road 290. These were not addressed in the project although it could be easily added to the "mapping_street" dictionary used by the function. 

### Cleaning Postcodes

Auditing the postcodes using a regular expression showed that it didn't follow a uniform format. To clean up postcodes, I decided to remove the county codes, but if a total cleaning is needed, a new field for county codes should be created in order to not lose the county codes data. This wasn't done here (however, it might be easily fixable if MongoDB was used--I used SQL). Some examples of updates for postcodes are:

    78704-7205 => 78704
    Texas => None
    TX 78613 => 78613

### Cleaning Phone Numbers

A similar approach to auditing post codes was used to audit the phone numbers (a regex was used). I simply chose the xxx-xxx-xxxx format for the phone numbers. Some of the results of the audit using a similar code as in the auditing of postcodes, are:

    512.386.1295 => 512-386-1295
    512-476-2625 => 512-476-2625
    Main: (512) 206-1000 Catering: (512) 206-1024 => 512-206-1000

In the last example above, I resorted to removing the second phone number. But to avoid losing data, the .findall() method can be used instead of the .search() method in the regex statement. It wasn't done in the project, however.

### The "clean" Function

Instead of using all the functions above individually in the final xml data extraction, particularly in the "shape_element" function, a "clean" function was created and eventually used.

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
        
## Extraction of Data from OSM File to CSV Files

Data were extracted from the OSM file using the functions from the case study exercises from the course. However, we were guided to write the "shape_element" function which not only parses the osm xml data but also cleans the data using the functions discussed above. The general scheme for processing osm files start from creating csv files as output files using the codecs module, then shaping the output, validating this output against a set schema and then writing the output onto the csv files.

#### *The shape_element function*

Parsing and cleaning of xml data occurs in the shape_element function. It extracts values of attributes from an xml element, instead of a whole xml tree (http://effbot.org/zone/celementtree.htm, http://effbot.org/zone/element-iterparse.htm, https://classroom.udacity.com/nanodegrees/nd002/parts/0021345404/modules/316820862075461/lessons/5436095827/concepts/54475500150923#). Along with this extraction, the data is updated accordingly and appended to receptacles (lists and dictionaries). 

I encountered problems processing the whole osm file with validation set to True even if I didn't obtain any errors processing the sample file with validation set to True. To figure out what was wrong, I gathered from the course forum that I needed to look for missing fields in the csv file obtained from running the program with validation set to False. However, I found it impossible to find any in the large csv output files. Besides, it was also impossible to load the whole file using a spreadsheet program. Blindly, I resorted to including lines of code to address missing data, though doing this was futile. An example of this is:

     if element.attrib[field] == '':
         node_attribs[field] = '999999'
     else:
         node_attribs[field] = element.attrib[field]

Eventually, I thought about looking at the output csv files from the processing of the whole file with validation on which failed. I took the last line in the resulting (incomplete) csv file, which happen to be nodes_tags.csv, using the csv module and the reader method.

    import csv
    with open("nodes_tags.csv", "r") as f:
        lastrow = None
        for lastrow in csv.reader(f):
            pass
        print lastrow
        
(Reference: http://stackoverflow.com/questions/20296955/reading-last-row-from-csv-file-python-error)

The result from this code gave me the 'id' of the element I can use to search where the line that causes the error is in the whole osm file:

    import xml.etree.cElementTree as ET
    
    def get_element(osm_file, tags=('node', 'way', 'relation')):
        """Yield element if it is the right type of tag
        Reference:
        http://stackoverflow.com/questions/3095434/inserting-newlines-in-xml-file-generated-via-xml-etree-elementtree-in-python
        """
        context = ET.iterparse(osm_file, events=('start', 'end'))
        _, root = next(context)
        for event, elem in context:
            if event == 'end' and elem.tag in tags:
                yield elem
                root.clear()
    
    counter = 0
    for element in get_element(OSM_FILE):
        counter += 1
        if element.tag == 'node':
            if element.attrib['id'] == '4133425201':
                print counter
                break
                
     Out: 6338418

This gave me the element number in the osm xml which gives rise to the error. I then generated a smaller osm file using this information, using the same lines of code used to make the sample osm file provided in the course.

    SAMPLE_FILE = "expectederror_file.osm"

    with open(SAMPLE_FILE, 'wb') as output:
        output.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        output.write('<osm>\n')
    
        for i, element in enumerate(get_element(OSM_FILE)):
            if i > 6338416:
                output.write(ET.tostring(element, encoding='utf-8'))
        output.write('</osm>')
        
I then processed "expectederror_file.osm" using my code with validation off and found the missing field or empty cell. I then found that the error was because of the value "service area" for attribute 'k', which should have been ignored since it contains a problem character. This then told me that the problem in the code is the cleaning of the 'k' values. The reason was the following lines of code in the shape_element function:

    try:
        problem_chars.search(tag.attrib['k']).group()
    except AttributeError:
       .....
       
This would have worked if I included "continue" in the third line of the code.

    try:
        problem_chars.search(tag.attrib['k']).group()
        continue
    except AttributeError:
        ....

I did change my code to use the if/else statement.

## Creation and Querrying of SQL Database

Creating the SQL database (atx_osm.db) was done using Python according to the method outlined in the course forum (https://discussions.udacity.com/t/creating-db-file-from-csv-files-with-non-ascii-unicode-characters/174958/6), using the schema specified in the following site: https://gist.github.com/swwelch/f1144229848b407e0a5d13fcb7fbbd6f. The process was straightfoward. All codes are contained in this notebook: https://github.com/mudspringhiker/wrangle_open_streetmap_data/blob/master/db_creation.ipynb

Querrying for list of cities showed that pretty much of all the cities were cleaned:

    cities = cur.execute("""SELECT tags.value, COUNT(*) as count
                            FROM (SELECT * FROM nodes_tags
                              UNION ALL 
                              SELECT * FROM ways_tags) tags 
                            WHERE tags.key = 'city' 
                            GROUP BY tags.value 
                            ORDER By count DESC""").fetchall()
    print cities
    
    Out: [(u'Austin', 3068),
        (u'Round Rock', 113),
        (u'Kyle', 64),
        (u'Cedar Park', 43),
        (u'Pflugerville', 37),
        (u'Leander', 33),
        (u'Buda', 26),
        (u'Georgetown', 17),
        (u'Dripping Springs', 13),
        (u'West Lake Hills', 12),
        (u'Bastrop', 9),
        (u'Elgin', 9),
        (u'Lakeway', 9),
        (u'Wimberley', 8),
        (u'Taylor', 7),
        (u'Bee Cave', 6),
        (u'Del Valle', 5),
        (u'Manor', 5),
        (u'Manchaca', 4),
        (u'Cedar Creek', 3),
        (u'Hutto', 3),
        (u'Spicewood', 3),
        (u'Creedmoor', 2),
        (u'Lago Vista', 2),
        (u'San Marcos', 2),
        (u'Sunset Valley', 2),
        (u'Webberville', 2),
        (u'Driftwood', 1),
        (u'Jonestown', 1),
        (u'Lost Pines', 1),
        (u'Manchacha', 1),
        (u'Maxwell', 1),
        (u'Smithville', 1)]

However, looking at the postcodes, there were three "None" values.
    
    postcode = cur.execute("""SELECT tags.value, COUNT(*) as count
                          FROM (SELECT * FROM nodes_tags
                                UNION ALL SELECT * FROM ways_tags) tags 
                          WHERE tags.key = 'postcode' 
                          GROUP BY tags.value 
                          ORDER By count DESC""").fetchall()

Result from the above query include:

    (u'None', 3)
    
To figure out what these should be, I querried for the accompanying information with these values. 

    missing_postcodes = cur.execute("""SELECT * 
                                       FROM (SELECT * FROM nodes_tags
                                         UNION ALL 
                                         SELECT * FROM ways_tags) tags 
                                       WHERE tags.key = 'postcode' 
                                       AND tags.value = 'None'""").fetchall()

    print missing_postcodes
    
    Out:    [(2152207067, u'postcode', u'None', u'addr'),
            (247506590, u'postcode', u'None', u'addr'),
            (383791236, u'postcode', u'None', u'addr')]
            
To determine what info is accompanying id 2152207067, the following query was done:

    cur.execute("""SELECT * 
             FROM (SELECT * FROM nodes_tags
             UNION ALL 
             SELECT * FROM ways_tags) tags
             WHERE tags.id = 2152207067""")
    missing_postcode1_info = cur.fetchall()
    print missing_postcode1_info
    
    Out: [(2152207067, u'name', u'Nyle Maxwell - Taylor', u'regular'),
        (2152207067, u'shop', u'car', u'regular'),
        (2152207067, u'website', u'www.nylemaxwellcjd.com', u'regular'),
        (2152207067, u'street', u'United States Highway 79', u'addr'),
        (2152207067, u'postcode', u'None', u'addr')]
        
From this result and accessing the provided website, it can be found that the postcode should be 76574.

The other postcodes were determined in the same way.

### Number of Nodes and Ways

Nodes:

    In [17]: cur.execute("SELECT COUNT(*) FROM nodes")
             nodes = cur.fetchall()
             nodes
    Out[17]:
             [(6356394,)]
             
This value is the same as the one obtained from the exploration of dataset using xml.etree.cElementTree module of Python (see p3_wrangle_openstreetmap_1.ipynb, High Level Tags).

    In [18]: cur.execute("SELECT COUNT(*) FROM ways")
             ways = cur.fetchall()
             ways
    Out[18]:
            [(666390,)]
            
This is also the same number obtained from the the ElementTree module in Python (p3_wrangle_openstreetmap_1.ipynb, High Level Tags).

### Number of Users/Contributors

    In [19]: cur.execute("""SELECT COUNT(DISTINCT(e.uid))
                            FROM (SELECT uid from nodes UNION ALL SELECT uid FROM ways) e""")
             users = cur.fetchall()
             users
    Out[19]:
             [(1146,)]

This number is lower than the one obtained using the ElementTree module in the exploration of the xml osm (1155 users, p3_wrangle_openstreetmap_1.ipynb, Exploring Users). This might be because when the csv files were created, the key values with problematic characters were removed, along with the rest of the record containing that value.

### Top 10 Contributing Users

    cur.execute("""SELECT e.user, COUNT(*) as num 
             FROM (SELECT user FROM nodes UNION ALL SELECT user FROM ways) e 
             GROUP BY e.user 
             ORDER BY num DESC 
             LIMIT 10""").fetchall()
Output:

    [(u'patisilva_atxbuildings', 2743705),
     (u'ccjjmartin_atxbuildings', 1300514),
     (u'ccjjmartin__atxbuildings', 940070),
     (u'wilsaj_atxbuildings', 359124),
     (u'jseppi_atxbuildings', 300983),
     (u'woodpeck_fixbot', 223425),
     (u'kkt_atxbuildings', 157847),
     (u'lyzidiamond_atxbuildings', 156383),
     (u'richlv', 50212),
     (u'johnclary_axtbuildings', 48232)]
             
However by using pandas module, a better looking table of the results can be obtained:

![alt tag](https://raw.githubusercontent.com/mudspringhiker/wrangle_open_streetmap_data/master/pandastable1.png)

### Locations of Restaurants

The query used to obtain a list of all the restaurants in the Austin, TX area was:
    
    cuisine_loc = cur.execute("""SELECT b.id, b.value, nodes.lat, nodes.lon 
                                 FROM (SELECT * FROM nodes_tags UNION ALL SELECT * FROM ways_tags) b
                                   JOIN nodes ON b.id = nodes.id 
                                 WHERE b.key = 'cuisine'""").fetchall()
                                 
Obtaining the locations of the coffee shops will then have a similar code:
    
    coffee_loc = cur.execute("""SELECT b.id, b.value, nodes.lat, nodes.lon 
                                FROM (SELECT * FROM nodes_tags UNION ALL SELECT * FROM ways_tags) b
                                  JOIN nodes ON b.id = nodes.id 
                                WHERE b.value = 'coffee_shop'""").fetchall()

Plotting the locations of these restaurants vs. the locations of coffee shops can then be done:

    import matplotlib.pyplot as plt
    import seaborn
    % matplotlib inline (only if using notebook)
    plt.scatter([x[2] for x in cuisine_loc], [y[3] for y in cuisine_loc], c='blue', label="restaurant")
    plt.scatter([x[2] for x in coffee_loc], [y[3] for y in coffee_loc], c='red', label="coffee shop")
    plt.xlabel('Latitude')
    plt.ylabel('Longtitude')
    plt.title('Restaurants, Coffee Shops')
    plt.legend(loc=2)


![alt tag](https://raw.githubusercontent.com/mudspringhiker/wrangle_open_streetmap_data/master/pandasplot1.png)

Lastly, querrying the database for the most popular cuisines was done. Pandas was used to eventually plot the distribution of the different types of restaurants in the Austin, TX area. It is no surprise that the area has a lot of Mexican restaurants.

![alt tag](https://raw.githubusercontent.com/mudspringhiker/wrangle_open_streetmap_data/master/pandasplot2.png)

## File Sizes

    austin_texas.osm        1.41 GB
    atx_osm.db              820.4 MB
    nodes.csv               604.3 MB
    nodes_tags.csv          11.7 MB
    ways.csv                48.6 MB
    ways_tags.csv           70.6 MB
    ways_nodes.csv          175.6 MB

## Conclusion

Information from an xml file can be scraped for data by Python through the xml.eTree.ElementTree module. This can be converted to a csv file which can be converted to an sql database (or to a pandas dataframe, which is not shown here, but was explored in another unit of the course). SQL databases can be converted to a pandas dataframe.

Cleaning of data takes a while. Knowledge of the nature of data also is very important so the best decisions on what to do with it can be done.

## Other References

Automate the Boring Stuff with Python: Practical Programming for Total Beginners, A. Sweighart, No Starch Press San Francisco, CA, USA ©2015 ISBN:1593275994 9781593275990

http://stackoverflow.com/questions/19877344/near-syntax-error-when-trying-to-create-a-table-with-a-foreign-key-in-sqlit

Brandon Rhodes - Pandas From The Ground Up - PyCon 2015, https://www.youtube.com/watch?v=5JnMutdy6Fw

Udacity Data Wrangling Course
(https://classroom.udacity.com/nanodegrees/nd002/parts/0021345404/modules/316820862075460/lessons/491558559/concepts/816599080

