import folium
import pandas as pd
import json

geo = '../data/2016pdas.geojson'

all_ids = pd.Series([
    feature["properties"]["joinkey"]
    for feature in json.load(open(geo))["features"]
])

df = pd.read_csv("max_density_per_pda_5080_sub_baseline.csv")
df["pda"] = df.pda.str.upper()
df = df.set_index("pda")

# folium doesn't like missing ids
df = df.reindex(all_ids).reset_index()
df.rename(columns={'index': 'pda'}, inplace=True)
df["max_built_dua"] = df.max_built_dua.fillna(0)
print df.max_built_dua.describe()

map = folium.Map(location=[37.8, -122.4], zoom_start=11, tiles='cartodbpositron')
map.choropleth(geo_path=geo, data=df,
             columns=['pda', 'max_built_dua'],
             key_on='feature.properties.joinkey',
             fill_color='YlGn', fill_opacity=0.7, line_opacity=0.2,
             legend_name='Max Dua by Policy Zone')
map.save('max_dua_pda_5080_subbaseline.html')
