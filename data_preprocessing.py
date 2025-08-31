import pandas as pd
from delhi_districts import crime_weights

df = pd.read_csv('District-wise_Crimes_committed_against_Women_2015_1.csv')

df_proj = df[["State/ UT", "District/ Area", "Total Crimes against Women"]].copy()

state_totals = df_proj.groupby("State/ UT")["Total Crimes against Women"].transform("sum")

df_proj["Crime_Probability"] = df_proj["Total Crimes against Women"] / state_totals

df_proj["District_Score"] = sum(df[col] * weight for col, weight in crime_weights.items())

state_totals = df_proj.groupby("State/ UT")["District_Score"].transform("sum")

df_proj["Normalized_Score"] = df_proj["District_Score"] / state_totals

df_proj.to_csv("district_crime_scores.csv", index=False)
