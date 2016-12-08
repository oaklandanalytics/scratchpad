
colmap = {
    "hhq1": "HHINCQ1",
    "hhq2": "HHINCQ2",
    "hhq3": "HHINCQ3",
    "hhq4": "HHINCQ4"
}

for year in range(2015, 2040, 5):

	print year

	df = pd.read_csv("run7224_taz_summaries_imputed_%d.csv" % year, index_col="zone_id")

	df2 = pd.read_csv("run7224_parcel_data_imputed_%d.csv" % year)

	for col in "AGREMPN,MWTEMPN,RETEMPN,FPSEMPN,HEREMPN,OTHEMPN".split(","):
		print col
 		assert df[col].sum() == df2[col].sum()

	for col in "hhq1,hhq2,hhq3,hhq4".split(','):
		print col
		eq = df[colmap[col]].fillna(0) == df2.groupby("zone_id")[col].sum().fillna(0)
		#print df2.groupby("zone_id")[col].sum()[~eq]
		#print df[colmap[col]][~eq]
		assert eq.value_counts()[True] == len(df)