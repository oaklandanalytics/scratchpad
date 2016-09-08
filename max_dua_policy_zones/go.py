import folium
import pandas as pd
import json

geo = 'policy_zones.geojson'

all_ids = pd.Series([
    feature["properties"]["zoningmodc"]
    for feature in json.load(open(geo))["features"]
])

df = pd.read_csv("max_density_per_policyzone.csv").set_index("zoningmodcat")

# folium doesn't like missing ids
df = df.reindex(all_ids).reset_index()
df.rename(columns={'index': 'zoningmodcat'}, inplace=True)
df["max_built_dua"] = df.max_built_dua.fillna(0)
print df.max_built_dua.describe()

map = folium.Map(location=[37.8, -122.4], zoom_start=11, tiles='cartodbpositron')
map.choropleth(geo_path=geo, data=df,
             columns=['zoningmodcat', 'max_built_dua'],
             key_on='feature.properties.zoningmodc',
             fill_color='YlGn', fill_opacity=0.7, line_opacity=0.2,
             legend_name='Max Dua by Policy Zone')
map.save('max_dua_policy_zones.html')
