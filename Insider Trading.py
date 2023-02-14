'''*****************************************************************************
Purpose: To extract insider trading data from the SEC website
This program extracts insider trading data from the SEC website and stores it in an
excel file.
Usage:
Enter a ticker (ex: 'AAPL, MSFT') or type 'all' to search thru all the tickers in file: 

Here you can enter either single ticker or separate multiple tickers by comma or
type 'all' to go thru all the tickers in fName = 'ticker and cik.csv' (default name)

Enter the starting date (Ex: 2020-MM-DD): # enter date in this format no error checking

Would you like to extract data to excel file (Press enter for no OR enter filename): 
Here either enter file name or press enter if you don't want to save the data.
By default the program doesn't display any data on shell, but you can add 
print(all_df) or print(symbol_df) to print the data

Error checking:
1.) If a user enters an incorrect ticker name ex: 'appl, msft, amzn, wrongone' 
the program will skip 'appl' and 'wrongone'. It will print out an error msg with the ticker
name and will continue to get insider data and save it to a file for rest of the tickers.

2.) If you are pulling the data for short period of time and there isn't much
info to calculate avg_purch/avg_sale and/or the buy to sell ratio it will append rest
of the data to excel file.
****************************************************************************'''
import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import csv

fName = 'ticker and cik.csv'    # set the ticker/CIK file name

data_dict, symbols = {}, []
with open(fName, 'r') as file:
    reader = csv.reader(file)
    for row in reader:
        data_dict[row[0]] = row[1]   # creating a dict ex. format: 'msft': '789019'
        symbols.append(row[0])


'''taking user input'''
# ticker
ticker = input("Enter a ticker (ex: 'AAPL, MSFT') or type 'all' to search thru all the tickers in file: ").replace(" ", "")
ticker = ticker.lower()
if ticker == 'all': symbols = symbols[1:]
else:
    tickers = ticker.split(",")
    symbols = tickers
    
# date
start = input("Enter the starting date (Ex: 2020-MM-DD): ")
start2 = datetime.datetime(int(start[:4]),int(start[5:7]),int(start[8:]))
end_date = datetime.date.today()

# extract to excel
extract = input("Would you like to extract data to excel file (Press enter for no OR enter filename): ")
print()


def transaction(url):
    '''gets the transaction report from url
    Parameter:    url: string
                       url for data extraction
    Return: trans_report: soup object
                       transaction report
    '''
    response = requests.get(url)
    web = response.content
    soup = BeautifulSoup(web, 'html.parser')
    trans_report = soup.find('table', {'id':'transaction-report'})
    return trans_report


def insiders(cik):
    '''gets the insider info of given cik number 
    Parameter:    cik: string
                       cik number
    Return:       all_data: pandas dataframe
                       dataframe of all the data
    
    '''
    all_data = None

    num = 0
    url = f'https://www.sec.gov/cgi-bin/own-disp?action=getissuer&CIK={cik}&type=&dateb=&owner=include&start={num}'
    
    urls = []
    urls.append(url)
    for url in urls:
        
        try:
            report = pd.read_html(str(transaction(url)))[0]

            if report is None or report.shape[1] != 12:
                raise Exception("Unexpected response from data server")

            for _, row in report.iterrows():
                if all_data is None:
                    all_data = pd.DataFrame(columns = report.columns)
       
                if row['Transaction Date'] < start:
                    return all_data

                all_data = pd.concat([all_data,pd.DataFrame(row).T])
        
            #If we received a full report, add another url request
            if report.shape[0] >= 80: 
                num += 1
                url = f'https://www.sec.gov/cgi-bin/own-disp?action=getissuer&CIK={cik}&type=&dateb=&owner=include&start={num*80}'
                urls.append(url)
                
        except Exception as e:
            print(e)
            continue
    
    return  all_data 
          

def data_df(all_df):
    '''gets the insider info of given cik number 
    Parameter:    all_df: list
                       list of all the data frame
    Return:       None
    '''        
    done = 0
    for symbol in symbols:
        # key error handling
        try: cik = data_dict[symbol]
        except Exception as e:
            print(f"The symbol {e} is not valid, rest of the data will be saved to excel file (if available)")        
            if symbol == symbols[-1]: break
            else: continue

        df = insiders(cik)
        done += 1
        
        if df is None:
            print(f"Retreiving insider trades for the symbol \"{symbol}\" failed. Skipping...")
            continue
        
        print(f"Finished extracting {symbol.upper()} insider data from {start} till {end_date}. A total of {df.shape[0]} insider trades logged.")
        print(f"Finished: {done}/{len(symbols)} symbols.")
        
        df['Purchchase'] = pd.to_numeric(df['Acquistion or Disposition'].apply(lambda x: 1 if x == 'A' else 0) * df['Number of Securities Transacted'])
        df['Sale'] = pd.to_numeric(df['Acquistion or Disposition'].apply(lambda x: 1 if x == 'D' else 0) * df['Number of Securities Transacted'])   
        
        name = 'Transaction Type'
        sell = df['Transaction Type'].str.count("S-Sale").sum()
        buy = df['Transaction Type'].str.count("P-Purchase").sum()
        
        sale = df['Acquistion or Disposition'] == 'D'    
        purch = df['Acquistion or Disposition'] == 'A'
        num_purch = len(df[purch])
        num_sale = len(df[sale])
        total_sale = int(df['Sale'].sum(skipna=True))        
        total_purch = int(df['Purchchase'].sum(skipna=True))
        
        # adding data to separate df for excel
        symbol_df = pd.DataFrame({'Symbol': symbol.upper(),
                                           '# of Purchases': num_purch,
                                           '# of Sales': num_sale,
                                           'Total Bought': f'{total_purch:,}',
                                           'Total Sold': f'{total_sale:,}',
                                           'S-Sale count': f'{sell}',
                                           'P-Purchase count': f'{buy}'},
                                            index = [1])
        
        # handling division by zero error/adding data to separate df for excel
        try:
            avg_sale = int(total_sale/num_sale)    
            avg_purch = int(total_purch/num_purch)
            ratio = round(num_purch/num_sale, 2)    # purchase to sell ratio
            
        except ZeroDivisionError as e: 
            print(f"\n{e} error for '{symbol}' there isn't much data available to calculate avg sale/purch & ratio, data will be added to excel without these metrics")
            
        else:
            symbol_df.insert(3, 'Buy/Sell Ratio', ratio)
            symbol_df.insert(6, 'Avg Shares Bought', avg_purch)
            symbol_df.insert(7, 'Avg Shares Sold', avg_sale)
            
        symbol_df.set_index('Symbol', inplace=True)    
        all_df.append(symbol_df)

    
def excel(all_df):
    '''adds the data to excel sheet, data is saved in same floder as this file
    Parameter:    all_df: list
                       list of all the data frame
    Return:       None
    '''      
    try:
        if len(extract) != 0:
            pd.concat(all_df).to_excel(extract +'.xlsx', index = True)
            print(f"Extracted the data to {extract}.xlsx\n")
    except Exception as e: print(e)
     
     
if __name__ == '__main__':
    all_df = []
    data_df(all_df)
    excel(all_df)