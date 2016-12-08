fix.py was the first script which was used to created files that look like *imputed*

This ended up getting the households right (the households were never wrong, though we didn't have parcel level summaries) but not the jobs.

The fix_jobs_only script was then used to take the imputed files and create the *smoothjobs* files.

The algorithm looks something like this...

1) First we compute the weights for every TAZ-sector combination, such that you could multiply these weights by the total jobs and get the actual job distribution.

2) We compute those weights for the base year and out year, and do a weighted average based on what year it is.  We multiply times the total number of jobs for the current year in the control totals and this is our seed.

3) We scale jobs by sector to meet the control totals by sector.

4) We cap zonal totals at the number of job spaces and scale up non capped zones, repeating this process until we have no zones that exceed capacity.

4b) Technically we already use a modified capacity which is the number of jobs - job spaces in 2040 times the proportion of the duration of the simulation we have achieved = (year - 2010) / (2040-2010)

5) Repeat 3 and 4 until we only exceed capacity by a little bit - i.e. biproportional fitting.

Sorry this documentation is sparse but hopefully this won't have to be revisited at this point.
