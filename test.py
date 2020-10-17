import pandas as pd
df1 = pd.read_csv('NameOfCsv.csv')
df1['Date'] = pd.to_datetime(df1.Date)
df1.sort('Date')
