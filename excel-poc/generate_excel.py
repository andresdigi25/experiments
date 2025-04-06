import pandas as pd

# Create a large DataFrame
data = {'Column1': range(1, 1000001), 'Column2': range(1000000, 0, -1)}
df = pd.DataFrame(data)

# Write the DataFrame to an Excel file
df.to_excel('/output/large_file.xlsx', index=False, engine='xlsxwriter')