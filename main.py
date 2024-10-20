# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

import pandas as pd
import os
import numpy as np
import csv

CAP_ONE_CATS = {'Airfare': 'Travel', 'Car Rental': 'Travel', 'Dining': 'Food', 'Entertainment': 'Entertainment',
                'Fee/Interest Charge': 'Annual Fee', 'Gas/Automotive': 'Travel', 'Health Care': 'Health',
                'Lodging': 'Travel', 'Merchandise': 'Shopping', 'Other': 'Other', 'Other Services': 'Other',
                'Other Travel': 'Travel', 'Payment/Credit': 'Return', 'Phone/Cable': 'Bills',
                'Professional Services': 'Other', 'Groceries': 'Groceries', 'Shopping': 'Shopping'}

CHASE_CATS = {'Bills & Utilities': 'Bills', 'Entertainment': 'Entertainment', 'Travel': 'Travel',
              'Groceries': 'Groceries', 'Shopping': 'Shopping', 'Personal': 'Shopping', 'Food & Drink': 'Food',
              'Home': 'Shopping', 'Health & Wellness': 'Health', 'Fees & Adjustments': 'Fees & Adjustments',
              'Merchandise & Inventory': 'Shopping', 'Gifts & Donations': 'Entertainment',
              'Professional Services': 'Professional Services', 'Education': 'Entertainment', 'Gas': 'Travel',
              'Repair & Maintenance': 'Shopping', 'Miscellaneous': 'Miscellaneous',
              'Office & Shipping': 'Professional Services', 'Automotive': 'Professional Services'}


def read_and_clean_chase(filename):
    """ read in Chase-style csv using pandas, only keep Sales/Returns transactions. returns cleaned df"""

    df = pd.read_csv(filename)

    # supported transaction types are sales, adjustments, returns, and card payments (i.e. payment of statement balance)
    trans_types = np.sort(np.array(['Payment', 'Adjustment', 'Sale', 'Return', 'Fee']))

    assert np.array_equal(np.sort(df['Type'].unique()), trans_types), f"{df['Type'].unique()}"

    df = df.drop('Post Date', axis=1)
    df = df.drop('Memo', axis=1)
    df = df[df['Type'] != 'Payment'].reset_index()
    df = df.drop('index', axis=1)
    df = df.drop('Type', axis=1)

    category_strings = df['Category'].unique()
    for c in category_strings:
        assert c in CHASE_CATS.keys(), f"Category: {c} not in CHASE_CATS"
    df = df.replace({'Category': CHASE_CATS})

    df = df.sort_values(by=['Category'])

    return df


def add_grocery_cap_one(df):
    """ Custom relabeling of categories based on store description for cap one"""
    df.loc[df['Description'].str.contains('TRADER JOE|TARGET|DAILY TABLE|WAL', regex=True, case=False),
           'Category'] = 'Groceries'
    df.loc[df['Description'].str.contains('GOODWILL', regex=False, case=False), 'Category'] = 'Shopping'
    return df


def read_and_clean_capone(filename):
    """ read in capone-style csv using pandas. remove monthly payments. Turn debits into negative nums and bring
        credits into same column as debits"""

    df = pd.read_csv(filename)

    df = df.drop(['Posted Date', 'Card No.'], axis=1)

    # remove monthly payments
    df = df[df['Description'] != 'CAPITAL ONE AUTOPAY PYMT'].reset_index()
    df = df.drop('index', axis=1)
    df = df[df['Description'] != 'CAPITAL ONE MOBILE PYMT'].reset_index()
    df = df.drop('index', axis=1)

    # make charges negative, move returns into amt column as positive vals
    df['Debit'] = df['Debit'] * -1
    df['Debit'] = df['Debit'].mask(df['Debit'].isnull(), df['Credit'], axis=0)
    df = df.drop('Credit', axis=1)
    df = df.rename({"Debit": "Amount"}, axis=1)

    df = add_grocery_cap_one(df)

    # rename to common categories
    category_strings = df['Category'].unique()
    for c in category_strings:
        assert c in CAP_ONE_CATS.keys(), f"Category: {c} not in CAP_ONE_CATS"
    df = df.replace({'Category': CAP_ONE_CATS})

    df = df.sort_values(by=['Category'])

    return df


def read_and_clean_venmo(filename):
    """ read in venmo-style csv using pandas. returns cleaned df"""

    df = pd.read_csv(filename, skiprows=2, usecols=range(1, 15))

    df = df.dropna(subset=['ID'])
    df = df.drop(['ID', 'Status', 'Amount (tip)', 'Amount (tax)', 'Amount (fee)', 'Tax Rate', 'Tax Exempt'], axis=1)

    cut_str_len = 10  # keep only date not time

    df['Datetime'] = df['Datetime'].str[:cut_str_len]

    return df


def sum_categories(df):
    """ Sum total spent in each category and place category sums in a new df, which is returned"""

    category_strings = df['Category'].unique()
    cat_col = []
    sums_col = []

    for c in category_strings:
        cat_col.append(c)
        sums_col.append(df.loc[df['Category'] == c, 'Amount'].sum())

    new_df = pd.DataFrame({'Category': cat_col, 'Amount': sums_col})
    return new_df

def read_and_clean_chase_debit(filename):

    df = pd.read_csv(filename, index_col=False)

    # Add new category column
    df['Category'] = 'Unassigned'

    # start categorizing main things
    df.loc[df['Type'].str.contains('ACH_DEBIT', regex=False, case=False), 'Category'] = 'remove'
    df.loc[df['Description'].str.contains('bank', regex=True, case=False), 'Category'] = 'remove'
    df.loc[df['Description'].str.contains('ebay', regex=False, case=False), 'Category'] = 'ebay'
    df.loc[df['Description'].str.contains('general hosp', regex=False, case=False), 'Category'] = 'paycheck'
    df.loc[df['Description'].str.contains('venmo', regex=False, case=False), 'Category'] = 'venmo'
    df.loc[df['Description'].str.contains('zelle', regex=False, case=False), 'Category'] = 'zelle'
    df.loc[df['Description'].str.contains('capital one|chase', regex=True, case=False), 'Category'] = 'cc payment'

    df = df.sort_values(by=['Category'])
    return df


if __name__ == '__main__':

    outfilepath = "/Users/liviaqoshe/Documents/budgeting_script/test/"

    # # filepath of sample csv
    # sample_chase_csv = "/Users/liviaqoshe/Documents/budgeting_script/test/chase_sample.csv"
    # sample_chase_df = read_and_clean_chase(sample_chase_csv)
    # sum_cats = sum_categories(sample_chase_df)
    # # print(sample_chase_df)
    # # print(sum_cats)
    #
    # # manual sorting
    # sample_chase_df.to_csv(os.path.join(outfilepath, "manual_sort_chase.csv"))
    # sorted_sample_chase_csv = "/Users/liviaqoshe/Documents/budgeting_script/test/sorted_chase.csv"
    # sorted_chase_df = pd.read_csv(sorted_sample_chase_csv)
    # sum_cats = sum_categories(sorted_chase_df)
    # # print(sum_cats)
    #
    # # filepath of sample csv
    # sample_venmo_csv = "/Users/liviaqoshe/Documents/budgeting_script/test/venmo_sample.csv"
    # sample_venmo_df = read_and_clean_venmo(sample_venmo_csv)
    # # print(sample_venmo_df)
    #
    # # filepath of sample csv
    # sample_capone_csv = "/Users/liviaqoshe/Documents/budgeting_script/test/capone_sample.csv"
    # sample_capone_df = read_and_clean_capone(sample_capone_csv)
    # # print(sample_capone_df)
    # sample_capone_df.to_csv(os.path.join(outfilepath, "manual_sort_capone.csv"))
    #
    # # filepath of sample csv
    # sample_chase_debit_csv = "/Users/liviaqoshe/Documents/budgeting_script/test/chase_debit_sample.csv"
    # sample_chase_debit_df = read_and_clean_chase_debit(sample_chase_debit_csv)
    #     # manual sort
    # sample_chase_debit_df.to_csv(os.path.join(outfilepath, "manual_sort_chase_debit.csv"))

    actual_chase_csv = "/Users/liviaqoshe/Documents/budgeting_script/test/Chase4062_Activity20230301_20231225_20240311.csv"
    to_do_manual_sort = read_and_clean_chase(actual_chase_csv)
    to_do_manual_sort.to_csv(os.path.join(outfilepath, "manual_sort_chase_4062_mar2024.csv"))




