"""Simple data loader for the Quora dataset used in the notebooks.
Provides `load_quora(path=None)` which returns a pandas.DataFrame.
If `path` is None it looks for `cleaned_quora.csv` next to this file, then in CWD.
"""
import os
import pandas as pd


def load_quora(path: str = None) -> pd.DataFrame:
    """Load cleaned_quora.csv and normalize expected columns.

    Args:
        path: Optional path to the CSV file. If omitted, tries module folder then CWD.

    Returns:
        pd.DataFrame with at least `clean_q1`, `clean_q2`, and `label` columns.

    Raises:
        FileNotFoundError: if no CSV is found at the candidate locations.
    """
    candidates = []
    if path:
        candidates.append(path)
    # try same folder as this module
    module_folder = os.path.dirname(__file__)
    # prefer parquet if present, then csv
    candidates.append(os.path.join(module_folder, 'cleaned_quora.parquet'))
    candidates.append(os.path.join(module_folder, 'cleaned_quora.csv'))
    # finally try current working directory
    candidates.append('cleaned_quora.parquet')
    candidates.append('cleaned_quora.csv')

    csv_path = None
    for p in candidates:
        try:
            if p and os.path.exists(p):
                csv_path = p
                break
        except Exception:
            continue

    if not csv_path:
        raise FileNotFoundError(
            'cleaned_quora.csv not found. Place the file in the project folder or call load_quora(path="/full/path/to/cleaned_quora.csv")'
        )

    # Read CSV or Parquet depending on file extension
    _, ext = os.path.splitext(csv_path)
    ext = ext.lower()
    if ext in ('.parquet', '.pq'):
        try:
            df = pd.read_parquet(csv_path)
        except Exception as e:
            raise RuntimeError(f'Failed to read parquet file {csv_path}: {e}')
    else:
        df = pd.read_csv(csv_path)

    # Ensure expected columns exist; attempt sensible fallbacks
    if 'clean_q1' not in df.columns:
        if 'question1' in df.columns:
            df['clean_q1'] = df['question1'].astype(str)
        else:
            df['clean_q1'] = df.iloc[:, 0].astype(str)

    if 'clean_q2' not in df.columns:
        if 'question2' in df.columns:
            df['clean_q2'] = df['question2'].astype(str)
        elif df.shape[1] > 1:
            df['clean_q2'] = df.iloc[:, 1].astype(str)
        else:
            df['clean_q2'] = df['clean_q1']

    if 'label' not in df.columns:
        if 'is_duplicate' in df.columns:
            df['label'] = df['is_duplicate']
        else:
            df['label'] = 0

    return df
