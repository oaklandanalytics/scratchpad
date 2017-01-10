import pandas as pd
import orca
from baus import models
import os

zoningmodcat = orca.get_table("parcels_geography").zoningmodcat

max_dua = None
max_far = None
runnum = 7224

df = pd.read_csv("run%d_parcel_output.csv" % runnum, index_col="parcel_id")
df = df[df.SDEM != True]

dua = df.residential_units / (df.parcel_size / 43560.0)

dua = dua.dropna()
dua = dua[dua > 0]
dua = dua.round()

if max_dua is None:
   max_dua = dua
else:
   max_dua = pd.concat([max_dua, dua], axis=1).max(axis=1)

far = df.non_residential_sqft / df.parcel_size

far = far.dropna()
far = far[far > 0]
far = far.round(1)

if max_far is None:
   max_far = far
else:
   max_far = pd.concat([max_far, far], axis=1).max(axis=1)

print max_dua.describe()
print max_far.describe()

outdf = pd.DataFrame({
    "max_built_dua": max_dua,
    "max_built_non_res_far": max_far
})

outdf["zoningmodcat"] = zoningmodcat

outdf.to_csv("max_building_sizes.csv")

outdf.groupby("zoningmodcat").max().to_csv("max_building_sizes_by_policy_zone.csv")


