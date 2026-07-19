---
name: pandas
description: Use when manipulating and analyzing data with pandas. Covers DataFrames, groupby, merge/join, time series, and optimization.
---

# Pandas Skill

## Overview
pandas is a fast, powerful, flexible, and easy-to-use open-source data analysis and manipulation library built on top of NumPy for the Python programming language. It provides data structures like Series (1D) and DataFrame (2D) with integrated indexing, handling of missing data, and a rich set of I/O and transformation operations.

## Instructions
- Prefer vectorized operations over iterating rows with `iterrows()` or `apply()` with lambda
- Use `read_csv()` with `dtypes` parameter to specify column types and reduce memory
- Use `pd.options.display.max_columns` and `max_rows` for configuring display
- Set `df.info(verbose=False)` for a quick memory usage overview
- Use `.loc[]` for label-based indexing, `.iloc[]` for positional indexing
- Use `.query()` for readable boolean indexing on DataFrames
- Chain operations with `.pipe()` for complex transformation pipelines
- Always specify `inplace=False` (default) and assign back; avoid `inplace=True`
- Use `pd.to_datetime()` when parsing date columns for datetime operations
- Use `category` dtype for columns with few unique values to save memory
- Sort the index for better performance in `loc[]` operations on large DataFrames
- Use `.copy()` when extracting a subset to avoid `SettingWithCopyWarning`

## Core Concepts

### DataFrame and Series
- **DataFrame**: 2D labeled data structure with columns of potentially different types
- **Series**: 1D labeled array that can hold any type
- Index: row labels (default RangeIndex); can be datetime, string, or custom
- Columns: named with string labels; accessed as `df.column_name` or `df['column_name']`
- `df.head()`, `df.tail()`, `df.sample()` for viewing data
- `df.shape`, `df.columns`, `df.index`, `df.dtypes`, `df.info()`, `df.describe()`

### Indexing and Selection
- `.loc[rows, columns]` — label-based indexing (inclusive range)
- `.iloc[rows, columns]` — integer position-based indexing (exclusive range)
- `.at[]` — fast scalar access by label
- `.iat[]` — fast scalar access by integer position
- Boolean indexing: `df[df['column'] > value]`
- `.isin()` for filtering by multiple values
- `.between()` for range queries
- `.duplicated()` / `.drop_duplicates()` for duplicate handling

### Handling Missing Data
- `isna()` / `notna()` — detect missing values
- `dropna()` — remove rows/columns with missing data
- `fillna()` — fill missing values with a value or method (ffill, bfill)
- `interpolate()` — interpolate missing values
- `pd.NA` — the new missing value sentinel (vs `np.nan`)
- Setting `use_inf_as_na` to treat infinity as missing

### GroupBy Operations
- Split-Apply-Combine paradigm
- `df.groupby('column')` — group by a single column
- `df.groupby(['col1', 'col2'])` — group by multiple columns
- Aggregation: `.agg('sum')`, `.agg(['sum', 'mean', 'count'])`, `.agg({'col': 'sum'})`
- Transformation: `.transform()` — return same-shape result
- Filtering: `.filter()` — filter groups based on a condition
- Apply: `.apply()` — custom function per group
- `groupby().size()` or `groupby().value_counts()` for group sizes

### Merge, Join, and Concatenate
- `pd.merge(df1, df2, on='key')` — SQL-style joins
- `how='inner'`, `'outer'`, `'left'`, `'right'`, `'cross'`
- Suffixes for overlapping column names: `suffixes=('_x', '_y')`
- `df1.join(df2)` — join on index
- `pd.concat([df1, df2])` — concatenate along axis 0 or 1
- `pd.concat([df1, df2], axis=1)` — horizontal concatenation
- `combine_first()` — fill missing values from another DataFrame

### Reshaping and Pivoting
- `pd.melt()` — unpivot wide to long format
- `df.pivot()` — pivot long to wide (unique index/column pairs required)
- `df.pivot_table()` — pivot with aggregation (handles duplicates)
- `df.stack()` — pivot columns to rows
- `df.unstack()` — pivot rows to columns
- `pd.crosstab()` — cross-tabulation (frequency table)

### Time Series
- `pd.to_datetime()` — parse strings to datetime
- `pd.date_range()` — generate date ranges
- `df.resample()` — resample time series data (downsample/upsample)
- `df.shift()` — shift data by periods (lag/lead)
- `df.diff()` — compute differences between consecutive values
- `df.rolling()` — window functions (moving average, etc.)
- `df.expanding()` — expanding window functions
- Time zone handling: `.tz_localize()`, `.tz_convert()`
- `pd.Timedelta` for time differences
- `pd.Period` and `pd.PeriodIndex` for period-based analysis

## Examples

### Data Loading and Inspection
```python
import pandas as pd
import numpy as np

df = pd.read_csv(
    'sales.csv',
    parse_dates=['order_date'],
    dtype={
        'customer_id': 'category',
        'product_id': 'category',
        'quantity': 'int32',
        'price': 'float32',
    },
    usecols=['order_id', 'order_date', 'customer_id', 'product_id', 'quantity', 'price'],
)

df.info(memory_usage='deep')
print(f"Shape: {df.shape}")
print(df.describe())
print(df['customer_id'].value_counts().head(10))
```

### Data Cleaning Pipeline
```python
def clean_sales_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and prepare sales data."""

    # Remove duplicates
    df = df.drop_duplicates(subset=['order_id'])

    # Handle missing values
    df['quantity'] = df['quantity'].fillna(0).astype('int32')
    df['price'] = df['price'].fillna(df['price'].median())

    # Remove outliers
    q1 = df['price'].quantile(0.25)
    q3 = df['price'].quantile(0.75)
    iqr = q3 - q1
    df = df[(df['price'] >= q1 - 1.5 * iqr) & (df['price'] <= q3 + 1.5 * iqr)]

    # Create derived columns
    df['total'] = df['quantity'] * df['price']
    df['year_month'] = df['order_date'].dt.to_period('M')

    # Sort
    df = df.sort_values('order_date').reset_index(drop=True)

    return df

df_clean = clean_sales_data(df)
```

### GroupBy Analysis
```python
# Monthly sales by product category
monthly_sales = (
    df_clean.groupby(['year_month', 'product_id'], observed=True)
    .agg(
        total_revenue=('total', 'sum'),
        order_count=('order_id', 'nunique'),
        avg_order_value=('total', 'mean'),
        quantity_sold=('quantity', 'sum'),
    )
    .reset_index()
)

# Top 10 customers by revenue
top_customers = (
    df_clean.groupby('customer_id', observed=True)
    .agg(
        total_spent=('total', 'sum'),
        order_count=('order_id', 'nunique'),
        avg_order_value=('total', 'mean'),
        first_purchase=('order_date', 'min'),
        last_purchase=('order_date', 'max'),
    )
    .query('total_spent > 1000')
    .sort_values('total_spent', ascending=False)
    .head(10)
    .reset_index()
)
```

### Time Series Resampling
```python
df_ts = df_clean.set_index('order_date')

# Daily revenue
daily_revenue = df_ts['total'].resample('D').sum()

# 7-day rolling average
rolling_avg = daily_revenue.rolling(window=7, min_periods=1).mean()

# Monthly comparison with year-over-year change
monthly = df_ts['total'].resample('ME').sum()
monthly_yoy = monthly.pct_change(periods=12) * 100

# Business day vs. weekend analysis
df_ts['is_weekend'] = df_ts.index.dayofweek.isin([5, 6])
weekday_avg = df_ts.groupby(df_ts.index.dayofweek)['total'].mean()

# Cumulative metrics
df_ts['cumulative_revenue'] = df_ts['total'].cumsum()
```

### Merge Example
```python
customers = pd.read_csv('customers.csv')
orders = pd.read_csv('orders.csv')
products = pd.read_csv('products.csv')

# Merge orders with customer info
orders_with_customer = orders.merge(
    customers[['customer_id', 'name', 'segment', 'region']],
    on='customer_id',
    how='left',
)

# Add product details
full_data = orders_with_customer.merge(
    products[['product_id', 'product_name', 'category', 'subcategory']],
    on='product_id',
    how='left',
)

# Cross-tab: region vs product category
cross_tab = pd.crosstab(
    full_data['region'],
    full_data['category'],
    values=full_data['total'],
    aggfunc='sum',
    normalize='index',
)
```

### Pivot and Melt
```python
# Pivot: long to wide
pivot = df_clean.pivot_table(
    index='year_month',
    columns='product_id',
    values='total',
    aggfunc='sum',
    fill_value=0,
)

# Melt: wide to long
long_format = pivot.reset_index().melt(
    id_vars=['year_month'],
    var_name='product_id',
    value_name='revenue',
)

# Stack / Unstack
stacked = df_clean.groupby(['year_month', 'product_id'])['total'].sum().unstack(fill_value=0)
```

## Best Practices
- Always convert date columns to `datetime` type when reading data
- Use `pd.read_csv()` with `chunksize` parameter for large files that don't fit in memory
- Use `.pipe()` for chaining multiple transformation functions
- Use `df.query('column == @variable')` for cleaner filtering with Python variables
- Use `df.eval()` for fast arithmetic operations on large DataFrames
- Prefer `category` dtype for columns with < 50% unique values
- Use `pd.concat()` with `ignore_index=True` when row order doesn't matter
- Use `df.merge()` with `validate` parameter to check relationship types (m:1, 1:m, 1:1)
- Use `pd.NA` instead of `np.nan` for missing values (consistent type handling)
- Use `df.sort_index()` after setting index for faster label-based lookups
- Specify `dtype` backend with `pd.set_option('mode.dtype_backend', 'pyarrow')` for better performance (pandas 2.0+)

## Common Mistakes
- Chained indexing: `df[df['col'] > 0]['other_col']` instead of `df.loc[df['col'] > 0, 'other_col']`
- Ignoring `SettingWithCopyWarning` — it indicates unexpected behavior
- Using `iterrows()` for row-by-row operations (extremely slow on large DataFrames)
- Not resetting index after groupby operations (getting MultiIndex unexpectedly)
- Forgetting to pass `observed=True` to groupby with categorical columns
- Using `pd.merge()` with duplicate key columns without handling suffixes
- Modifying a slice of a DataFrame thinking it modifies the original
- Not specifying `engine='pyarrow'` or `dtype_backend='pyarrow'` for large datasets
- Using `apply()` with axis=1 (row-wise) on large DataFrames (very slow)
- Not setting `parse_dates` when reading CSV with date columns
- Confusing `axis=0` (rows) and `axis=1` (columns) in operations
- Using `pd.DataFrame.append()` (deprecated; use `pd.concat()` instead)

## Libraries
- **pandas-gbq** — Google BigQuery I/O
- **pandas-profiling** / **ydata-profiling** — automated EDA report generation
- **polars** — faster DataFrame library (compatible API subset)
- **modin** — pandas with parallel backend (Dask, Ray)
- **dask** — parallel DataFrame operations for out-of-core computation
- **bottleneck** — accelerated C-level operations for rolling, groupby
- **numexpr** — fast numerical expression evaluator for pandas eval/query
- **fastparquet** / **pyarrow** — Parquet file I/O
- **openpyxl** — Excel file I/O (.xlsx)
- **sqlalchemy** — SQL database I/O with pd.read_sql
- **matplotlib** / **seaborn** — plotting from pandas DataFrames

## Design Principles
- **Tabular Data Model**: DataFrames mirror SQL tables and spreadsheet concepts
- **Label-Based Indexing**: Both row and column labels for intuitive access
- **Alignment**: Operations automatically align on labels (index and columns)
- **Split-Apply-Combine**: GroupBy operations follow this fundamental pattern
- **Missing Data Represented**: NaN/NA propagates through operations by default
- **Convention Over Configuration**: Sensible defaults for common operations

## Coding Standards
- Import as `import pandas as pd`
- Use `_` for multi-word DataFrame column names: `order_date`, `customer_id`
- Use `snake_case` for variable names
- Chain operations with `\` or parenthesized expressions for readability
- Use `df.rename(columns={'old': 'new'})` for column renaming
- Document data cleaning steps in functions with docstrings
- Use `pd.options.display.*` for consistent display settings
- Prefer method chaining over intermediate variables for simple pipelines
- Write unit tests for data transformation functions
- Use `df.to_parquet()` for saving processed DataFrames (smaller, faster than CSV)

## Performance
- Use `categorical` dtype for string columns with low cardinality
- Use `pd.read_csv()` with `usecols` to load only needed columns
- Use `pd.read_csv()` with `nrows` for quick sampling during exploration
- Use `.copy()` with `deep=False` for shallow copies when possible
- Use `numexpr` backend for `df.eval()` and `df.query()` (set `engine='numexpr'`)
- Use `groupby().agg()` over `groupby().apply()` (C-optimized vs Python loop)
- Prefer `pd.cut()` and `pd.qcut()` for binning operations
- Use `df.values` for fast NumPy array access when labels aren't needed
- Use `numba` JIT compilation with pandas for custom operations
- Use `pd.concat()` over `df.append()` (it creates a new array each time)
- Use `infer_datetime_format=True` in `pd.to_datetime()` for faster parsing
- Set `mode.chained_assignment = 'warn'` for safe development, `None` for production
- Use `pd.options.compute.use_bottleneck = True` for faster rolling operations

## Memory Management
- Use `df.info(memory_usage='deep')` to see actual memory usage including strings
- Downcast numeric types: `pd.to_numeric(df['col'], downcast='integer'/'float')`
- Use `category` for string columns with < 50% unique values
- Use `pd.read_csv()` with `dtypes` dictionary to specify exact types
- Use `chunksize` parameter in `pd.read_csv()` for out-of-core processing
- Use `sparse` data structures for DataFrames with mostly zeros
- Use `df.memory_usage(deep=True).sum()` to monitor memory
- Delete intermediate DataFrames with `del` and call `gc.collect()` if needed
- Use PyArrow backend for memory-efficient string columns: `pd.set_option('mode.dtype_backend', 'pyarrow')`
- Process data in chunks with `pd.read_csv(..., chunksize=10000)`

## Testing
- Use `pytest` with `pandas.testing` module
- `pd.testing.assert_frame_equal()` for DataFrame equality
- `pd.testing.assert_series_equal()` for Series equality
- Test edge cases: empty DataFrames, all-NaN, single row, duplicate index
- Test data transformations with known input/output pairs
- Use `tmp_path` fixture for file I/O tests
- Use `hypothesis` strategies for property-based testing of transformations
- Test groupby operations with controlled random data
- Test merge behavior with various join types and key configurations
- Parametrize tests for different data types and sizes
