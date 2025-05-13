# -*- coding: utf-8 -*-
"""
Created on Wed May  7 10:54:59 2025

@author: win11
"""

import pandas as pd




#DATAPROCESSING####


#population contains countryname = location, iso_2 and iso_3 codes
#easies way to use as a base to join with other data like lat/lon and economic status
#popraw has duplicates

df_popraw = pd.read_csv('wpp2024_totalpopulationbysex-cleaned.csv')



df_countries = df_popraw[['ISO2_code', 'ISO3_code']] \
        .drop_duplicates(keep='first') \
        .dropna(subset = ['ISO2_code', 'ISO3_code']) \
        .reset_index(drop=True)


#read country/lat/long values

df_latlon = pd.read_csv("countries.csv")

# Create mapping dictionary
iso2_code_to_name = df_latlon.set_index('country')['name'].to_dict()


#read economic income status
# Load the income classification Excel
df_income = pd.read_excel('class-country.xlsx')  # .head(218) Adjust the path if needed

#PROCESS COUNTRIES LAT/LONG, this one has ISO2 and a name everybody recognizes,
#the un name will be replaces by this name so Viet Nam is going to be Vietnam

df_countries_1 = pd.merge(df_countries, df_latlon, left_on='ISO2_code', right_on='country') \
    .drop('country', axis=1)

#PROESS INCOME GROUP, JOIN WITH DF_INCOME ON ISO3,
#DF_COUNTRIES_2 CONTAINS ALL PASSIVE ONE-ROW INFO LIKE LAT/LONG,INCOME_GROUP 2024 ETC.
df_countries_2 = pd.merge(df_countries_1, df_income, left_on='ISO3_code', right_on='Code') \
    .drop(['Economy','Code','Lending category','Other (EMU or HIPC)' ], axis=1)


name_to_incomegroup = df_countries_2.set_index('name')['Income group'].to_dict()
    

#CONVERT df_popraw into a df to use for visualisation

#filter on time (=year), remove columns with nan values, VARIANT medium is for medium growth
useyears = [ 1990,1995,2000,2005,2010,2015,2020,2024]
df_popyears = df_popraw[(df_popraw['Time'].isin(useyears)) & (df_popraw['Variant'] == 'Medium')]\
        .drop(columns=['Location','Variant'], axis=1) \
        .dropna(subset = ['ISO2_code', 'ISO3_code']) \
        .reset_index(drop=True)

#get name from df_latlon based on ISO_2 code = country
df_popyears['name'] = df_popyears['ISO2_code'].map(iso2_code_to_name)
#populations totals are in K's, migration totals are in nothing, for comparison
df_popyears['PopTotal_viz']= df_popyears['PopTotal']*1000
#and we add the jul variant as extra column, makes viz easier
df_popyears['julTime'] = df_popyears['Time'].apply(lambda x: 'jul'+str(x))

# Create mapping dictionary based on LocID
locid_code_to_name = df_popyears.set_index('LocID')['name'].to_dict()


#PROCESS MIGRATION DATA 
#read it, drop destination and Origin and use map to get both column
#values from df_popyears based on LocID (LocID is a UN unique identifier
# for a location begin land, region etc)
#this action is necessary to standardize country names used in the app.

df_migration_raw = pd.read_excel('undesa_pd_2024_ims_stock_by_sex_destination_and_origin.xlsx',
                        sheet_name='Table 1',
                        header=10,
                        usecols=[1,4,5,6,7,8,9,10,11,12,13,14])

df_migration = df_migration_raw.drop(columns=['Destination','Origin'])

#iloc >= 900 equals everything other than a country, 900 equals world, to vague to visualise




#remove World as a destination

df_migration_region = df_migration_raw[ \
                     (df_migration_raw['Location code of destination'] > 900) & \
                     (df_migration_raw['Location code of origin'] > 900) ]    



#replace * after some destination/origin values
df_migration_region['Origin'] = df_migration_region['Origin'].str.replace('NORTHERN AMERICA','Northern America')
df_migration_region['Destination'] = df_migration_region['Destination'].str.replace('NORTHERN AMERICA','Northern America')

    
#remove rows with only uppercase in destination or origin => all uppercase    
df_migration_region = df_migration_region[
    ~(
        df_migration_region['Origin'].str.isupper() |
        df_migration_region['Destination'].str.isupper()
    )
]



#replace * after some destination/origin values
df_migration_region['Origin'] = df_migration_region['Origin'].str.replace('*','')
df_migration_region['Destination'] = df_migration_region['Destination'].str.replace('*','')

#remove combinations in Destination, Origin => contains " and "
df_migration_region = df_migration_region[
    ~(
        df_migration_region['Origin'].str.contains(" and ", case=False, na=False) |
        df_migration_region['Destination'].str.contains(" and ", case=False, na=False)
    )
]

# Define pattern to match names that include (but not equal) 'income' or 'developed'
pattern = r'(?i)(?=.*income|developed|others|LLDC|SIDS|Sub-Saharan)'
#Polynesia|Micronesia|Melanesia|

# Filter out unwanted rows in both Destination and Origin
mask_dest = df_migration_region['Destination'].str.contains(pattern) & (df_migration_region['Destination'].str.lower() != 'income') & (df_migration_region['Destination'].str.lower() != 'developed')
mask_orig = df_migration_region['Origin'].str.contains(pattern) & (df_migration_region['Origin'].str.lower() != 'income') & (df_migration_region['Origin'].str.lower() != 'developed')

# Keep only rows where neither Destination nor Origin contain the keywords
df_migration_region = df_migration_region[~(mask_dest | mask_orig)]

df_migration_region['Origin'] = df_migration_region['Origin'].apply(lambda x: 'Australia and New Zealand' if x == 'Australia/New Zealand' else x)
df_migration_region['Destination'] = df_migration_region['Destination'].apply(lambda x: 'Australia and New Zealand' if x == 'Australia/New Zealand' else x)


    

# Combine the origin and destination into one DataFrame
combined = pd.concat([
    df_migration_region[['Location code of destination', 'Destination']].rename(
        columns={'Location code of destination': 'code', 'Destination': 'name'}
    ),
    df_migration_region[['Location code of origin', 'Origin']].rename(
        columns={'Location code of origin': 'code', 'Origin': 'name'}
    )
])

# Drop duplicates based on the code
combined_unique = combined.drop_duplicates(subset='code')

# Convert to dictionary
location_vague_dict = dict(zip(combined_unique['code'], combined_unique['name']))



#get name from df_population based on locid = dest, since we are going to do
#so much with income group, add it here
df_migration['Destination'] = df_migration['Location code of destination'].map(locid_code_to_name)
df_migration['Origin'] = df_migration['Location code of origin'].map(locid_code_to_name)
df_migration['destination_income_group'] = df_migration['Destination'].map(name_to_incomegroup)
df_migration['origin_income_group'] = df_migration['Origin'].map(name_to_incomegroup)




#REMOVE ALL EXCEPT df_countries_2 from memory, no longer needed
#no idea if this works, I do not think so.


df_countries_2.to_csv('countries_general.csv',index=False)
df_popyears.to_csv('popyears.csv',index=False)
df_migration.to_csv('migration.csv',index=False)
df_migration_region.to_csv('migration_region.csv',index=False)

