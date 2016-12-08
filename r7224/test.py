emp_cols = "AGREMPN,MWTEMPN,RETEMPN,FPSEMPN,HEREMPN,OTHEMPN".split(",")

for year in range(2015, 2040, 5):
    for col in emp_cols:

    	df = pd.read_csv("run7224_parcel_data_smoothjobs_%d.csv" % year)
    	df2 = pd.read_csv("run7224_taz_summaries_smoothjobs_%d.csv" % year)

    	s = df.groupby("zone_id")[col].sum()
    	s2 = df2[col]

    	assert np.allclose(s.sort_index(), s2.sort_index())