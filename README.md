# Insider-Trading

This program is a command line interface (CLI) tool which extracts insider trading data from the SEC website, and then stores the data in an excel file for a specified time fram. The program gathers a variety of metrics such as the number of pruchases, sales, average shared bought and sold, etc.

# How to run:

To run the program, simply run the command:

```
python3 'insider trading.py'
```

Enter any ticker symbol(s) in a comma separated list or type 'all' to search through every possible ticker symbol in the 'ticker and cik.csv' file.

Enter the starting date, or the date which you want to start gathering data from (ex: 2018-MM-DD):

Would you like to extract data to excel file (Press enter for no OR enter filename):
Here, simply enter the name of the .xlsx file you would like to the data to, or press enter if you do not want to the date. If the data is not saved to a file, you can print out the data frame in the shell using print(all_df) or print(symbol_df).
