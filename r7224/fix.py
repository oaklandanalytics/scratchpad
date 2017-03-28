args = sys.argv[1:]

RUNNUM = 7224
if len(args) == 1: RUNNUM = int(args[0])

parcel_log = pd.read_csv("run%d_parcel_output.csv" % RUNNUM)

# ironically we know that the households are all correct, so we can trust zonal variables for
# everything but jobs.  we also want to recreate parcel level household variables

employment_controls = pd.read_csv("/Users/fsfoti/src/bayarea_urbansim/data/employment_controls.csv",
                                  index_col="year")

base_parcels = pd.read_csv("run%d_parcel_data_2010.csv" % RUNNUM,
                           index_col="parcel_id")

forecast_parcels = pd.read_csv("run%d_parcel_data_2040.csv" % RUNNUM,
                               index_col="parcel_id")

forecast_parcels["zone_id"] = orca.get_table("parcels").zone_id

base_parcels["zone_id"] = orca.get_table("parcels").zone_id

debug_df = pd.DataFrame()

def target_for_year_by_zone(colname, year):

    colname = {
        "hhq1": "HHINCQ1",
        "hhq2": "HHINCQ2",
        "hhq3": "HHINCQ3",
        "hhq4": "HHINCQ4"
    }.get(colname, colname)

    year = float(year) # to allow floats

    base = pd.read_csv("run%d_taz_summaries_2010.csv" % RUNNUM, index_col="zone_id")[colname]

    forecast = pd.read_csv("run%d_taz_summaries_2040.csv" % RUNNUM, index_col="zone_id")[colname]
    
    # linear interpolation from base to forecast
    return (forecast - base) * ((year - 2010) / 30) + base


def match_controls(parcels, year):

    def remove_match_col(col, tot):

        col = col.fillna(0)

        diff = tot - col.sum()

        print "remove", col.name, diff, tot

        if diff < 0:

            fan_out = pd.Series(np.repeat(col.index,
                                          col.values.astype('int')))

            remove = fan_out.sample(diff * -1)

            col = col.sub(remove.value_counts(), fill_value=0)

        return col

    def add_match_col(col, tot, empty_spaces):

        col = col.fillna(0)

        diff = tot - col.sum()

        print "add", col.name, diff, tot

        if diff > 0:

            fan_out = pd.Series(np.repeat(empty_spaces.index,
                                          empty_spaces.values.astype('int')))

            targets_by_zone = target_for_year_by_zone(col.name, year)
            current_by_zone = col.groupby(base_parcels.zone_id).sum()

            weights_by_zone = targets_by_zone - current_by_zone

            # first we get the zone_id for all the parcels in our sample
            # then we get the count by zone of this column in the forecast year
            weights = weights_by_zone.loc[forecast_parcels.zone_id.loc[fan_out.values]]

            print "total capacity", empty_spaces.sum()

            assert diff <= empty_spaces.sum()

            # normalize
            weights = weights.clip(.01)
            weights = weights / weights.sum()

            add = fan_out.sample(diff, weights=weights.values)

            col = col.add(add.value_counts(), fill_value=0)

        # print tot, col.sum() # should equal each other

        return col

    def household_capacity_func(df):

        capacity = df["total_residential_units"].copy()

        for col in "hhq1,hhq2,hhq3,hhq4".split(","):
            capacity -= df[col].fillna(0)

        return capacity.clip(0)

    def employment_capacity_func(df):

        capacity = df["total_job_spaces"].copy()

        for col in "AGREMPN,MWTEMPN,RETEMPN,FPSEMPN,HEREMPN,OTHEMPN".split(","):
            capacity -= df[col].fillna(0)

        return capacity.clip(lower=0)

    for controls, capacity_func in [
        (employment_controls, employment_capacity_func)
    ]:

        # first we remove then we add - we remove first in order
        # to have the most room for when we're adding

        for col in controls:

            tot = controls.loc[year, col]

            parcels[col] = remove_match_col(parcels[col], tot)

        for col in controls:

            tot = controls.loc[year, col]

            capacity = capacity_func(parcels)

            parcels[col] = add_match_col(parcels[col], tot, capacity)

            assert parcels[col].sum() == tot
            print parcels[col].sum(), tot

    colmap = {
        "hhq1": "HHINCQ1",
        "hhq2": "HHINCQ2",
        "hhq3": "HHINCQ3",
        "hhq4": "HHINCQ4"
    }


    for col in "hhq1,hhq2,hhq3,hhq4".split(','):

        capacity = capacity_func(parcels)

        # for households we have to match zonal totals, not regional totals
        for zone_id, row in pd.read_csv("run%d_taz_summaries_%d.csv" % (RUNNUM, year),
                                        index_col="zone_id").iterrows():

            # first we remove then we add - we remove first in order
            # to have the most room for when we're adding
            mask = parcels.zone_id == zone_id

            current = parcels.loc[mask, col].sum()

            totcapacity = capacity[mask].sum()

            tot = row[colmap[col]]

            print zone_id, current, tot

            if tot == current:

                continue

            elif tot < current:

                parcels.loc[mask, col] = remove_match_col(parcels.loc[mask, col], tot)

            elif tot - current > totcapacity:

                # random crapshoot
                random_parcels = parcels[mask].sample(tot-current, replace=True)

                counts = pd.Series(random_parcels.index).value_counts()

                parcels.loc[counts.index, col] = parcels.loc[counts.index, col].fillna(0) + counts.values

            else:

                parcels.loc[mask, col] = add_match_col(parcels.loc[mask, col], tot, capacity[mask])

    return parcels


def modify_zone_summary(parcels, year):

    df = pd.read_csv("run%d_taz_summaries_%d.csv" % (RUNNUM, year), index_col="zone_id")

    jobs_df = pd.DataFrame()

    for col in "AGREMPN,MWTEMPN,RETEMPN,FPSEMPN,HEREMPN,OTHEMPN".split(","):
        
        jobs_df[col] = parcels.groupby("zone_id")[col].sum()

    jobs_df["TOTEMP"] = jobs_df.sum(axis=1)

    for col in jobs_df:
        df[col] = jobs_df[col]

    df["total_job_spaces"] = parcels.groupby("zone_id").total_job_spaces.sum()
    df["total_residential_units"] = parcels.groupby("zone_id").total_residential_units.sum()

    return df


for year in range(2015, 2040, 5):

    print year

    this_years_parcels = parcel_log[parcel_log.year_built == year]

    this_years_parcel_ids = this_years_parcels.parcel_id

    # take the forecast year's parcels and add them to the base parcels
    # for the parcel_ids that we know developed that year

    isin_this_years_parcel_ids = \
        base_parcels.index.isin(this_years_parcel_ids)

    base_parcels[isin_this_years_parcel_ids] = \
        forecast_parcels[isin_this_years_parcel_ids]

    base_parcels = match_controls(base_parcels, year)

    base_parcels.to_csv("run%d_parcel_data_imputed_%d.csv" % (RUNNUM, year))

    modify_zone_summary(base_parcels, year).to_csv("run%d_taz_summaries_imputed_%d.csv" % (RUNNUM, year))

