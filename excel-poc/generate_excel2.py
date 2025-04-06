import pandas as pd

# Create a large DataFrame
data = {'Column1': range(1, 10000001), 'Column2': range(10000000, 0, -1)}
df = pd.DataFrame(data)

# Define the maximum number of rows per sheet
max_rows_per_sheet = 1048576

# Create a Pandas Excel writer using XlsxWriter as the engine
with pd.ExcelWriter('/output/large_file2.xlsx', engine='xlsxwriter') as writer:
    # Calculate the number of sheets needed
    num_sheets = (len(df) // max_rows_per_sheet) + 1
    
    for i in range(num_sheets):
        start_row = i * max_rows_per_sheet
        end_row = start_row + max_rows_per_sheet
        sheet_df = df.iloc[start_row:end_row]
        
        # Write each chunk to a separate sheet
        sheet_df.to_excel(writer, sheet_name=f'Sheet{i+1}', index=False)

print("Excel file created successfully.")