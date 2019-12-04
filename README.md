# Analysis of Palo Alto's OpenStreetMap Database

## DATA WRANGLING PROCESS:

Obtainment of raw openstreetmap dataset

1. Go to https://mapzen.com/data/metro-extracts/

2. Type in “Palo Alto, CA, USA”

3. Click “GET EXTRACT” button

4. From here, download the raw openstreetmap dataset in the OSM XML format, which is 16 MB

### Auditing process

First, I should mention that I initially used the provided code to create a small sample of the larger dataset for convenience.
The nodes_tags and ways_tags lists are more likely than nodes, ways, and ways_nodes to contain various representations of data that are most in need of cleaning (since they contain qualitative information like keys, values, and types rather than quantitative information like latitude, longitude, user, etc.). Therefore, I intended to output several csv files containing every key, value, and type listed in nodes_tags and ways_tags lists. In addition, these csv files would list the number of instances of each key/value/type and order them from least to greatest. In total, there were 6 csv files to output:

(nodes_tags vs. ways_tags) x (key vs. value vs. type) = nodes_keys_audit.csv, nodes_values_audit.csv, nodes_types_audit.csv, ways_keys_audit.csv, ways_values_audit.csv, ways_types_audit.csv

After examining these various audit csv files, I came across a problem with the values of tags with ‘phone’ as their key. Namely, the phone numbers (i.e. the tag values) were irregular and had no consistent format (e.g. ‘+1 (650) 564-1024’, ‘650-564-1024’, ‘650.564.1024’, etc.). I will cover how I solved this in the “cleaning process” section below.

Furthermore, I noticed that running the program with validate=True provides an error message pointing out that there is at least one instance where the “uid” and “user” fields of the nodes list are missing. We will have to deal with this in the cleaning process.
### Cleaning process

As mentioned above, we need to find a way of dealing with data where the “uid” and “user” fields of the nodes list are missing. In order to accomplish this, I implemented the check_for_unfilled() function, which (1) checks if a field is missing, (2) checks if the missing field is either “uid” or “user”, and then (3) replaces the missing field with the appropriate value. In the case of a missing “uid” field, I decided to have the missing value replaced with -1 (negative one), as all other “uid” values are positive integers; this allows us to uniquely mark such data for later identification. In the case of a missing “user” field, I decided to have the missing value replaced with “” (an empty string), as all other “user” values are non-empty strings (since Openstreetmap requires usernames be non- empty strings); this allows us to uniquely mark such data for later identification.
  
Next, I realized that there could be multiple variations for one particular ending of street names, as witnessed in the homework for this section of the program (e.g. “Ave.”, “Avenue”, “Ave”). Therefore, I implemented the clean_street_names() function to solve this possible problem.

Then there was the problem of phone numbers being irregular in format. I tackled this problem by utilizing regex to detect a wide range of conceivable phone number formats and then stripping the string concerned of all non-numeric characters (i.e. digits). Lastly, I checked if the length of the stripped string was more than 10 characters, in which case only the last 10 characters of the string were returned as a final result to replace the value of the tag.

However, I was faced a problem in dealing with some tags with ‘phone’ as their key that contained a non-phone number (e.g. wrongly input phone number, website address, etc.) as their value. See the screenshot below for some examples:
Rather than simply let these values be erroneously labeled with the key ‘phone’, I decided to separate them into a new key of their own: ‘phone_irregular’. In this way, the proper phone numbers are cleaned and preserved while other non-phone numbers are removed but still preserved elsewhere.

## DATA ANALYSIS PROCESS:

In order to properly analyze the data, I transferred the written csv files to an SQL database according to the provided schema found here: https://gist.github.com/swwelch/f1144229848b407e0a5d13fcb7fbbd6f

From this point, I set out to discover some overview statistics that might provide some interesting aspects of the area I decided to investigate. See below for a list of the several aspects I decided to investigate:

#### Number of distinct users contributing to nodes and ways

<img width="421" alt="screen shot 2018-06-23 at 6 07 51 am" src="https://user-images.githubusercontent.com/25094252/41809036-9fd41e06-76ac-11e8-8984-620d06048640.png">

#### Number of distinct nodes

<img width="389" alt="screen shot 2018-06-23 at 6 08 07 am" src="https://user-images.githubusercontent.com/25094252/41809037-9fe474ea-76ac-11e8-9ef4-4632367bb1a7.png">

#### Number of distinct ways

<img width="384" alt="screen shot 2018-06-23 at 6 08 16 am" src="https://user-images.githubusercontent.com/25094252/41809038-9ff5c8a8-76ac-11e8-84aa-165ed8910188.png">

#### Number of distinct restaurants

<img width="706" alt="screen shot 2018-06-23 at 6 08 25 am" src="https://user-images.githubusercontent.com/25094252/41809039-a00660be-76ac-11e8-8764-fdaff2196813.png">

#### Number of distinct cafes

<img width="681" alt="screen shot 2018-06-23 at 6 08 37 am" src="https://user-images.githubusercontent.com/25094252/41809040-a016fcda-76ac-11e8-9d2f-b34b88b818fe.png">

#### Average speed limit

<img width="629" alt="screen shot 2018-06-23 at 6 08 48 am" src="https://user-images.githubusercontent.com/25094252/41809041-a026e532-76ac-11e8-8897-74b866f295d8.png">

#### Maximum speed limit

<img width="617" alt="screen shot 2018-06-23 at 6 08 56 am" src="https://user-images.githubusercontent.com/25094252/41809043-a0381a3c-76ac-11e8-825d-6650255aecaa.png">

#### Minimum speed limit

<img width="625" alt="screen shot 2018-06-23 at 6 09 04 am" src="https://user-images.githubusercontent.com/25094252/41809044-a048a668-76ac-11e8-9511-5aa5e1b0d73a.png">

#### Number of distinct addresses

<img width="680" alt="screen shot 2018-06-23 at 6 09 12 am" src="https://user-images.githubusercontent.com/25094252/41809045-a059306e-76ac-11e8-8d62-81f9249dead0.png">

#### Number of distinct streets ending in ‘Avenue’

<img width="560" alt="screen shot 2018-06-23 at 6 09 24 am" src="https://user-images.githubusercontent.com/25094252/41809046-a06a8c10-76ac-11e8-9c66-ba67efafc299.png">

#### Number of distinct streets ending in ‘Street’

<img width="563" alt="screen shot 2018-06-23 at 6 09 35 am" src="https://user-images.githubusercontent.com/25094252/41809047-a07a7a26-76ac-11e8-9e82-2bef12087bd9.png">

#### Number of distinct streets ending in ‘Way’

<img width="562" alt="screen shot 2018-06-23 at 6 09 44 am" src="https://user-images.githubusercontent.com/25094252/41809048-a0894cd6-76ac-11e8-88c4-b5813ecbb652.png">

## OTHER IDEAS:

It would be remiss to leave out a few words on what could be improved upon with regard to this project. Here I will list a couple ideas that could be explored and their merits and associated difficulties.

• An interesting improvement could revolve around the investigation into speed limits. Specifically, it would be interesting to examine speed limit in proportion to the length of the roads they apply to. Without this factor included in the proper analysis, the accuracy of our current measure of the “average” speed limit remains imprecise. 

• The problem of what to do with the phone numbers that did not match any of the conceivable formats remains unresolved. One possible way to improve the situation involves those non-phone number values that are website addresses. Specifically, I think it may be possible to find the phone number at the website address, in which case it is conceivable that we might scrape the phone numbers from the relevant websites and insert them in place of the website addresses. Of course, this sounds rather difficult and the efficacy of such an idea remains to be seen.
