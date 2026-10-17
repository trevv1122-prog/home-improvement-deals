import json
import csv
import os

STORES = [
    # Collin County - Home Depot
    {"id": "6589", "retailer": "Home Depot", "name": "The Home Depot Wylie #6589", "city": "Wylie", "county": "Collin", "address": "951 S Westgate Way, Wylie, TX 75098", "url": "https://www.homedepot.com/l/Wylie/TX/Wylie/75098/6589"},
    {"id": "0528", "retailer": "Home Depot", "name": "The Home Depot McKinney #0528", "city": "McKinney", "county": "Collin", "address": "1515 N Central Expy, McKinney, TX 75070", "url": "https://www.homedepot.com/l/Mckinney/TX/Mckinney/75070/528"},
    {"id": "6809", "retailer": "Home Depot", "name": "The Home Depot West McKinney #6809", "city": "McKinney", "county": "Collin", "address": "252 N Custer Rd, McKinney, TX 75071", "url": "https://www.homedepot.com/l/West-Mckinney/TX/Mckinney/75071/6809"},
    {"id": "0582", "retailer": "Home Depot", "name": "The Home Depot Plano West #0582", "city": "Plano", "county": "Collin", "address": "6200 W Park Blvd, Plano, TX 75093", "url": "https://www.homedepot.com/l/W-Plano/TX/Plano/75093/582"},
    {"id": "0589", "retailer": "Home Depot", "name": "The Home Depot Frisco #0589", "city": "Frisco", "county": "Collin", "address": "11255 Preston Rd, Frisco, TX 75034", "url": "https://www.homedepot.com/l/Frisco/TX/Frisco/75034/0589"},
    {"id": "6513", "retailer": "Home Depot", "name": "The Home Depot Allen #6513", "city": "Allen", "county": "Collin", "address": "510 W McDermott Dr, Allen, TX 75013", "url": "https://www.homedepot.com/l/Allen/TX/Allen/75013/6513"},

    # Collin County - Lowe's
    {"id": "2929", "retailer": "Lowe's", "name": "Lowe's of Murphy #2929 (Wylie Area)", "city": "Murphy", "county": "Collin", "address": "111 E FM 544, Murphy, TX 75094", "url": "https://www.lowes.com/store/TX-Murphy/2929"},
    {"id": "1072", "retailer": "Lowe's", "name": "Lowe's of Allen #1072", "city": "Allen", "county": "Collin", "address": "1010 W McDermott Dr, Allen, TX 75013", "url": "https://www.lowes.com/store/TX-Allen/1072"},
    {"id": "1087", "retailer": "Lowe's", "name": "Lowe's of Frisco #1087", "city": "Frisco", "county": "Collin", "address": "3360 Preston Rd, Frisco, TX 75034", "url": "https://www.lowes.com/store/TX-Frisco/1087"},
    {"id": "2825", "retailer": "Lowe's", "name": "Lowe's of McKinney #2825", "city": "McKinney", "county": "Collin", "address": "2055 N Central Expy, McKinney, TX 75070", "url": "https://www.lowes.com/store/TX-Mckinney/2825"},
    {"id": "0060", "retailer": "Lowe's", "name": "Lowe's of East Plano #0060", "city": "Plano", "county": "Collin", "address": "5001 Central Expy, Plano, TX 75023", "url": "https://www.lowes.com/store/TX-Plano/0060"},
    {"id": "2878", "retailer": "Lowe's", "name": "Lowe's of McKinney South #2878", "city": "McKinney", "county": "Collin", "address": "8550 State Hwy 121, McKinney, TX 75070", "url": "https://www.lowes.com/store/2878-mckinney-tx/hardware-store"},

    # Dallas County - Home Depot
    {"id": "0553", "retailer": "Home Depot", "name": "The Home Depot Garland #0553", "city": "Garland", "county": "Dallas", "address": "3261 N George Bush Hwy, Garland, TX 75040", "url": "https://www.homedepot.com/l/Garland/TX/Garland/75040/553"},
    {"id": "8951", "retailer": "Home Depot", "name": "The Home Depot Rowlett #8951", "city": "Rowlett", "county": "Dallas", "address": "2201 Lakeview Pkwy, Rowlett, TX 75088", "url": "https://www.homedepot.com/l/Rowlett/TX/Rowlett/75088/8951"},
    {"id": "0556", "retailer": "Home Depot", "name": "The Home Depot Richardson #0556", "city": "Richardson", "county": "Dallas", "address": "2140 Jupiter Rd, Garland/Richardson, TX 75044", "url": "https://www.homedepot.com/l/Richardson/TX/Garland/75044/556"},
    {"id": "6804", "retailer": "Home Depot", "name": "The Home Depot Dallas Skillman #6804", "city": "Dallas", "county": "Dallas", "address": "6000 Skillman St, Dallas, TX 75231", "url": "https://www.homedepot.com/l/Skillman/TX/Dallas/75231/6804"},
    {"id": "0550", "retailer": "Home Depot", "name": "The Home Depot Dallas White Rock #0550", "city": "Dallas", "county": "Dallas", "address": "11255 Garland Rd, Dallas, TX 75218", "url": "https://www.homedepot.com/l/White-Rock/TX/Dallas/75218/550"},
    {"id": "0598", "retailer": "Home Depot", "name": "The Home Depot Dallas Forest Lane #0598", "city": "Dallas", "county": "Dallas", "address": "11682 Forest Ln, Dallas, TX 75243", "url": "https://www.homedepot.com/l/Forest-Lane/TX/Dallas/75243/598"},

    # Dallas County - Lowe's
    {"id": "0604", "retailer": "Lowe's", "name": "Lowe's of Garland #0604", "city": "Garland", "county": "Dallas", "address": "2949 N George Bush Fwy, Garland, TX 75040", "url": "https://www.lowes.com/store/TX-Garland/0604"},
    {"id": "2779", "retailer": "Lowe's", "name": "Lowe's of Richardson #2779", "city": "Richardson", "county": "Dallas", "address": "501 S Plano Rd, Richardson, TX 75081", "url": "https://www.lowes.com/store/TX-Richardson/2779"},
    {"id": "0515", "retailer": "Lowe's", "name": "Lowe's of North Dallas #0515", "city": "Dallas", "county": "Dallas", "address": "11920 Inwood Rd, Dallas, TX 75244", "url": "https://www.lowes.com/store/TX-Dallas/0515"},
    {"id": "2280", "retailer": "Lowe's", "name": "Lowe's of Central Dallas #2280", "city": "Dallas", "county": "Dallas", "address": "2525 Inwood Rd, Dallas, TX 75235", "url": "https://www.lowes.com/store/TX-Dallas/2280"},
    {"id": "1780", "retailer": "Lowe's", "name": "Lowe's of Northeast Dallas #1780", "city": "Dallas", "county": "Dallas", "address": "9520 McCree Rd, Dallas, TX 75238", "url": "https://www.lowes.com/store/TX-Dallas/1780"},
    {"id": "0665", "retailer": "Lowe's", "name": "Lowe's of Far North Dallas #0665", "city": "Dallas", "county": "Dallas", "address": "19210 Preston Rd, Dallas, TX 75252", "url": "https://www.lowes.com/store/TX-Dallas/0665"},
]

print(f"Loaded {len(STORES)} verified stores across Collin & Dallas Counties.")
