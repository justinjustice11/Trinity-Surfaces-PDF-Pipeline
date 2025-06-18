import pandas as pd

# Load every sheet into a dict, auto-detecting their real names
sheets = pd.read_excel('ChatGPTRandom.xlsx', sheet_name=None)

# Print out what pandas thinks the sheet names are
print("Detected sheets:", list(sheets.keys()))

# (Then, for example:)
quotes_df       = sheets['Quotes']            # or whatever the exact key turns out to be
samples_df      = sheets['Samples by rep']   # <-- note trailing space?
sales_df        = sheets['Sales and profits']
opps_df         = sheets['OpporOpportunities- branch and datetunities']

# From there you can parse each one’s date & value columns,
# aggregate monthly, plot quotes vs. sales vs. opportunities vs. samples,
# and compute correlations to see which pipeline metric best (and worst)
# predicts actual sales.
