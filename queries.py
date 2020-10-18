import sqlalchemy as db
import pandas as pd

def sort_csv(filename):
    df = pd.read_csv(f"./{filename}")
    username = df.iloc[0, 0]
    df["Username"] = username
    df["Datetime"] = pd.to_datetime(df.Datetime).dt.strftime("%d-%m-%Y %H:%S").astype(str)
    df.drop(axis=0, index=[0, len(df.index) - 1], inplace=True)
    df.drop(["Beginning Balance", "Ending Balance", "Disclaimer"], axis=1, inplace=True)
    df.update(df[["Amount (fee)", "Statement Period Venmo Fees", "Year to Date Venmo Fees"]].fillna(0))
    df.update(df[["Destination", "Funding Source"]].fillna(""))
    df["Amount (total)"] = df["Amount (total)"].str.strip("$")
    df["Note"] = df["Note"].str.capitalize()
    df.columns = df.columns.str.replace(r"(\()|(\))", "", regex=True).str.strip(" ").str.replace(" ", "_").str.lower()
    df = df.rename({"from": "sender", "id": "transaction_id", "type": "transaction_type", "to": "recipient"}, axis=1)

    df.sort_values('datetime')
    return df


file = sort_csv('./ACTS Challenge 1 Sample.csv')
for row in file.values:
	username = row[0]
	transaction_id = row[1]
	_datetime = row[2]
	transaction_type = row[3]
	status = row[4]
	note = row[5]
	sender = row[6]
	recipient = row[7]
	amount_total = row[8]
	amount_fee = row[9]
	funding_source = row[10]
	destination = row[11]
	statement_period_venmo_fees = row[12]
	terminal_location = row[13]
	year_to_date_venmo_fees = row[14]
	