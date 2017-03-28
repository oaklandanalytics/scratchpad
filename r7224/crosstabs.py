import pandas as pd
import orca
from baus import models

p = orca.get_table("parcels")
settings = orca.get_table("settings")
superdistricts = orca.get_table("superdistricts")
        
outdf = pd.DataFrame()

for year, df in [
	(2015, pd.read_csv("run7224_parcel_data_imputed_2015.csv",
	    index_col="parcel_id")),
	(2040, pd.read_csv("run7224_parcel_data_2040.csv",
		index_col="parcel_id"))
]:
	df["county"] = p.county
	df["built_dua"] = df.total_residential_units / p.parcel_acres
	df["high_rise"] = df.built_dua > 150
	df["sqft_per_job"] = \
		df.building_type_id.map(settings["building_sqft_per_job"]) *
		p.superdistrict.map(superdistricts.sqft_per_job_factor)
    df["total_non_residential_sqft"] = df.sqft_per_job * df.job_spaces

	df["single_family_homes_%d" % year] = \
		df[df.building_type_id.isin([1, 2])]\
			.groupby("county").total_residential_units.sum()

	df["multi_family_homes_%d" % year] = \
		df[df.building_type_id > 2]\
			.groupby("county").total_residential_units.sum()

	df["office_%d" % year] = \
		df[df.building_type_id == 4].\
			groupby("county").total_non_residential_sqft.sum()

	df["retail_%d" % year] = \
		df[df.building_type_id.isin([10, 11])].\
			groupby("county").total_non_residential_sqft.sum()

	df["industrial_%d" % year] = \
		df[df.building_type_id.isin([7, 8, 9])].\
			groupby("county").total_non_residential_sqft.sum()

outdf.to_csv("run7224_crosstabs.csv")