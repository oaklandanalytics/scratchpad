import pandas as pd 

df = pd.read_csv("run5080_taz_summaries_2010.csv")
print df.groupby("COUNTY").TOTHH.sum()

city_join = pd.read_csv("../data/city_to_county.csv").\
	drop_duplicates(subset="juris").\
	set_index("juris")

df2 = pd.read_csv("run5080_juris_summaries_2010.csv")
s = city_join.loc[df2.juris].county
print len(df2), len(s)
df2["county"] = city_join.loc[df2.juris].county.values

print df2.groupby("county").tothh.sum()