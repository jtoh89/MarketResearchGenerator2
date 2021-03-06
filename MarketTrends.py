import pandas as pd
from markettrends_data import get_markettrends_data
from db_layer import sql_caller
import sys


sql = sql_caller.SqlCaller(create_tables=True)

zillow_data = get_markettrends_data.get_zillow_data()
unemployment_data = get_markettrends_data.get_unemployment_data()

# STEP 1
# Join Zillow data with BLS unemploment data
market_trends = pd.merge(zillow_data, unemployment_data, how='inner', left_on=['Date','Geo_ID'], right_on=['Date','Geo_ID'])
market_trends = market_trends.drop(columns=['Geo_Name_y']).rename(columns={'Geo_Name_x':'Geo_Name'})
# market_trends.to_excel('testdata/test1.xlsx')
market_trends_msas = market_trends[['Geo_ID', 'Geo_Name']].drop_duplicates()


# STEP 2
# Join Zillow, BLS unemploment data with Building Permits
buildingpermits = sql.db_get_MarketTrends_BuildingPermits()
market_trends = pd.merge(market_trends, buildingpermits, how='left', left_on=['Date','Geo_ID'], right_on=['Date','Geo_ID'])
market_trends = market_trends.drop(columns=['Geo_Name_y']).rename(columns={'Geo_Name_x':'Geo_Name'})


# STEP 3
# Get Population and make sure we filter out MSA not in Zillow
population_data = sql.db_get_MarketTrends_Population()
# population_data.to_excel('testdata/test2.xlsx')
population_data = pd.merge(population_data, market_trends_msas, how='inner', left_on=['Geo_ID'], right_on=['Geo_ID']).drop(columns=['Geo_Name_x']).rename(columns={'Geo_Name_y': 'Geo_Name'})
population_msas = population_data[['Geo_ID', 'Geo_Name']].drop_duplicates()


common_msas = pd.merge(market_trends_msas, population_msas, how='left', left_on=['Geo_ID'], right_on=['Geo_ID']).drop(columns=['Geo_Name_y']).rename(columns={'Geo_Name_x': 'Geo_Name'})
zillow_missing = market_trends_msas[(~market_trends_msas.Geo_ID.isin(common_msas.Geo_ID))]
arcgis_missing = population_msas[(~population_msas.Geo_ID.isin(common_msas.Geo_ID))]


if len(common_msas) != len(population_msas) or len(common_msas) != len(market_trends_msas):
    print('MISMATCH')
    # sys.exit()

common_msas.to_excel('testdata/market_trends_lookup.xlsx')

sql.db_dump_Market_Geo_ID_Lookup(common_msas)
sql.db_dump_MarketTrends_HistoricalTrends(market_trends)


