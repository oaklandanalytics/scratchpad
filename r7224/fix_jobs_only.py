from baus.utils import round_series_match_target, \
    constrained_normalization, groupby_random_choice

parcel_log = pd.read_csv("run7224_parcel_output.csv")

employment_controls = pd.read_csv("/Users/fsfoti/src/bayarea_urbansim/data/employment_controls.csv",
                                  index_col="year")

base_zones = pd.read_csv("run7224_taz_summaries_2010_corrected.csv",
                         index_col="zone_id")

forecast_zones = pd.read_csv("run7224_taz_summaries_2040_corrected.csv",
                             index_col="zone_id")

emp_cols = "AGREMPN,MWTEMPN,RETEMPN,FPSEMPN,HEREMPN,OTHEMPN".split(",")


def match_controls_smoothly(parcels, year):

    base_pdf = base_zones[emp_cols].fillna(0)
    total = base_pdf.sum().sum()

    base_pdf /= total

    forecast_pdf = forecast_zones[emp_cols].fillna(0)
    total = forecast_pdf.sum().sum()

    forecast_pdf /= total

    # our target is to smooth the sector distribution between the 2010 and 2040 numbers
    mix_factor = (year - 2010) / float(2040 - 2010)

    target_pdf = base_pdf * (1.0-mix_factor) + forecast_pdf * mix_factor

    total_jobs = employment_controls.loc[year].sum()

    target_jobs = target_pdf * total_jobs

    can_exceed_capacity_by = (forecast_zones.TOTEMP - 
        forecast_zones.total_job_spaces).clip(0) * mix_factor

    while 1:
        # this is biproportional fitting

        # now we scale to meet control totals
        col_marginals = target_jobs.sum()

        controls = employment_controls.loc[year]

        factors = controls/col_marginals

        target_jobs *= factors

        # now we scale to meet row (zone) totals

        row_marginals = target_jobs.sum(axis=1)

        capacity = parcels.groupby("zone_id").total_job_spaces.sum()

        capacity += can_exceed_capacity_by

        convergence = (row_marginals - capacity).clip(lower=0).sum()

        print "Convergence criterion: ", convergence
        if convergence < 250:
            assert np.allclose(target_jobs.sum(), controls)
            assert np.isclose(target_jobs.sum().sum(), controls.sum())
            break

        constrained_row_marginals = constrained_normalization(
            row_marginals.copy(), capacity, total_jobs)

        factors = constrained_row_marginals / row_marginals

        target_jobs = target_jobs.multiply(factors, axis="index")

    # now get integers

    for col in target_jobs:
        target_jobs[col] = round_series_match_target(target_jobs[col], controls[col])

    return target_jobs


def groupby_random_choice_w_capacity(s, counts, capacity):

    #print s.head(), counts.head(), capacity.head()

    if counts.sum() == 0:
        return pd.Series()

    # align on index first
    df = pd.DataFrame({"group_ids": s, "capacity": capacity})
    df = df[df.capacity > 0]

    s, capacity = df.group_ids, df.capacity

    # fan out our s array for how mauch capcity we have for each element
    fan_out = s.take(np.repeat(np.arange(len(s)),
                               capacity.astype("int").values))

    # this is what we have capacity for
    aggregate_capacity = fan_out.value_counts()
    # we want mor ethan we have
    excess_demand = counts.sub(aggregate_capacity, fill_value=0)
    # this is what we can't meet - we will give back to the user
    excess_demand = excess_demand[excess_demand > 0]
    # contrain counts to the amount of capacity we really have
    counts = counts.sub(excess_demand, fill_value=0)

    ret = pd.concat([
        fan_out[fan_out == grp].sample(cnt, replace=False)
        for grp, cnt in counts[counts > 0].iteritems()
    ])

    return ret, excess_demand


def modify_parcels_to_match_zone_jobs(parcels, target_jobs):

    for col in emp_cols:

        current_jobs_sector = parcels.groupby("zone_id")[col].sum()
        target_jobs_sector = target_jobs[col]
        new_jobs_sector = target_jobs_sector - current_jobs_sector

        remove_jobs = new_jobs_sector[new_jobs_sector < 0]
        add_jobs = new_jobs_sector[new_jobs_sector > 0]

        remove_selection, _ = groupby_random_choice_w_capacity(
            parcels.zone_id, remove_jobs * -1, parcels[col])

        # did it work?
        assert np.allclose(
            remove_jobs * -1,
            remove_selection.value_counts().sort_index())

        capacity = parcels.total_job_spaces - parcels[emp_cols].sum(axis=1)

        add_selection, unplaced = groupby_random_choice_w_capacity(
            parcels.zone_id, add_jobs, capacity)

        add_selection2 = groupby_random_choice(
            parcels.zone_id[parcels.total_job_spaces > 0],
            unplaced, replace=True)

        # did it work?
        assert np.allclose(
            unplaced,
            add_selection2.value_counts().sort_index())

        parcels[col] = parcels[col].sub(
            pd.Series(remove_selection.index).value_counts(), fill_value=0
        ).add(
            pd.Series(add_selection.index   ).value_counts(), fill_value=0
        ).add(
            pd.Series(add_selection2.index  ).value_counts(), fill_value=0
        )

        # make sure we did it right
        assert np.allclose(target_jobs_sector,
                           parcels.groupby("zone_id")[col].sum())

    return parcels


for year in range(2015, 2040, 5):

    print year

    parcels = pd.read_csv("run7224_parcel_data_imputed_%d.csv" % year,
                          index_col="parcel_id")

    target_jobs = match_controls_smoothly(parcels, year)

    parcels = modify_parcels_to_match_zone_jobs(parcels, target_jobs)

    taz_file = pd.read_csv("run7224_taz_summaries_imputed_%d.csv" % year,
                           index_col="zone_id")

    taz_file[emp_cols] = target_jobs.fillna(0)
    taz_file["TOTEMP"] = target_jobs.sum(axis=1).fillna(0)

    taz_file.to_csv("run7224_taz_summaries_smoothjobs_%d.csv" % year)
    parcels.to_csv("run7224_parcel_data_smoothjobs_%d.csv" % year)