import pandas as pd
import orca
from baus import models

p = orca.get_table("parcels")
superdistricts = orca.get_table("superdistricts")
building_sqft_per_job = {
  -1: 400,
  0: 400,
  1: 400,
  2: 400,
  3: 400,
  4: 355,
  5: 1161,
  6: 470,
  7: 661,
  8: 960,
  9: 825,
  10: 445,
  11: 445,
  12: 383,
  13: 383,
  14: 383
}        

outdf = pd.DataFrame()

for year, df in [
	(2015, pd.read_csv("run7224_parcel_data_smoothjobs_2015.csv",
	    index_col="parcel_id")),
	(2040, pd.read_csv("run7224_parcel_data_2040.csv",
		index_col="parcel_id"))
]:
	df["county"] = p.county
        df["first_building_type_id"] = df.first_building_type_id.astype("float")
	df["built_dua"] = df.total_residential_units / p.parcel_acres
	df["high_rise"] = df.built_dua > 100
	df["sqft_per_job"] = \
		df.first_building_type_id.map(building_sqft_per_job)
	df["sqft_per_job"] *= p.superdistrict.map(superdistricts.sqft_per_job_factor)
    	df["total_non_residential_sqft"] = df.sqft_per_job * df.total_job_spaces

	outdf["single_family_homes_%d" % year] = \
		df[df.built_dua < 40]\
			.groupby("county").total_residential_units.sum()

	outdf["multi_family_homes_%d" % year] = \
		df[df.built_dua.between(40, 130)]\
			.groupby("county").total_residential_units.sum()

	outdf["multi_family_homes_high_rise_%d" % year] = \
		df[df.built_dua > 130]\
			.groupby("county").total_residential_units.sum()

	outdf["office_jobs_%d" % year] = \
		df[df.first_building_type_id == 4].\
			groupby("county").total_job_spaces.sum()

	outdf["retail_jobs_%d" % year] = \
		df[df.first_building_type_id.isin([10, 11])].\
			groupby("county").total_job_spaces.sum()

	outdf["industrial_jobs_%d" % year] = \
		df[df.first_building_type_id.isin([7, 8, 9])].\
			groupby("county").total_job_spaces.sum()

	outdf["office_%d" % year] = \
		df[df.first_building_type_id == 4].\
			groupby("county").total_non_residential_sqft.sum()

	outdf["retail_%d" % year] = \
		df[df.first_building_type_id.isin([10, 11])].\
			groupby("county").total_non_residential_sqft.sum()

	outdf["industrial_%d" % year] = \
		df[df.first_building_type_id.isin([7, 8, 9])].\
			groupby("county").total_non_residential_sqft.sum()
print outdf.sum()
outdf.to_csv("run7224_crosstabs.csv")
