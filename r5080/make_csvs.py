df = pd.read_csv("../max_dua_policy_zones/run5080_parcel_output.csv")

# fill in missing jurises
p = orca.get_table("parcels")
df["juris"] = p.juris.loc[df.parcel_id].values

for name, grp in df.groupby("juris"):
	grp.to_csv("csvs/r5080_{}_devs.csv".format(name))