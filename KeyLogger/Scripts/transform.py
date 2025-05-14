import getpass
import pandas as pd
import sqlite3
import numpy as np

def transform_df(df, output_db_path='data/transformed_outputPC.db', table_name='TransformedData'):
    username = getpass.getuser()
    df = df.rename(columns={'message': 'Button'})

    df['dwell_time'] = df['release_time'] - df['press_time']
    df = df[df['dwell_time'] > 0]

    # Add backspace count features before filtering out non-alphabetic keys
    df['is_enter'] = df['Button'].str.lower() == 'enter'
    df['message_id'] = df['is_enter'].cumsum()
    df['user_id'] = username

    backspace_features = []

    for msg_id, group in df.groupby('message_id'):
        keys = group['Button'].tolist()
        total_bksp = sum(k.lower() == '<-' for k in keys)

        # Count average burst lengths
        burst_lengths = []
        count = 0
        for k in keys:
            if k.lower() == '<-':
                count += 1
            else:
                if count > 0:
                    burst_lengths.append(count)
                    count = 0
        if count > 0:
            burst_lengths.append(count)

        avg_burst = np.mean(burst_lengths) if burst_lengths else 0

        backspace_features.append({
            'message_id': msg_id,
            'total_backspaces': total_bksp,
            'avg_backspace_burst': avg_burst
        })

    backspace_df = pd.DataFrame(backspace_features)

    # Now apply filtering for only alpha keys
    df = df[df['Button'].str.match(r'^[a-zA-Z0-9]$')]
    df.drop(columns=['is_enter'], inplace=True)
    df = df[df['Button'].str.len() == 1]

    all_keys = sorted(df['Button'].str.lower().unique())
    feature_rows = []

    for msg_id, group in df.groupby('message_id'):
        row = {
            'message_id': msg_id,
            'user_id': group['user_id'].iloc[0],
            'message_length': len(group),
            'avg_dwell': group['dwell_time'].mean(),
            'std_dwell': group['dwell_time'].std(),
            'key_diversity': group['Button'].nunique(),
            'typing_duration': group['release_time'].max() - group['press_time'].min()
        }

        group['Button'] = group['Button'].str.lower()
        for key in all_keys:
            key_dwell = group[group['Button'] == key]['dwell_time']
            row[f'dwell_{key}'] = key_dwell.mean() if not key_dwell.empty else np.nan

        feature_rows.append(row)

    # Create output DataFrame
    transformed_df = pd.DataFrame(feature_rows)
    transformed_df = transformed_df.merge(backspace_df, on='message_id', how='left')

    # Save to SQLite DB
    with sqlite3.connect(output_db_path) as conn:
        transformed_df.to_sql(table_name, sqlite3.connect(output_db_path), if_exists='replace', index=False)

    print(f"Transformed data saved to {output_db_path} (table: {table_name})")

df = pd.read_sql("SELECT * FROM messages", sqlite3.connect("data/Database.db"))
df = df.rename(columns={'message': 'Button'})
button_replacements = {
    "Key.space": " ",
    "Key.enter": "Enter",
    "Key.tab":"Tab",
    "Key.backspace": "<-",
    "Key.ctrl_l": "CTRL",
    "Key.alt_l": "alt",
    "Key.shift": "SH",
    "Key.esc": "esc"
}
def transform_button_name(button):
    return button_replacements.get(button, button)

df['Button'] = df['Button'].apply(transform_button_name)
transform_df(df)