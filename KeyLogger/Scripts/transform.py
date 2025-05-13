import getpass
import pandas as pd
import sqlite3

def transform_df(df, output_db_path='transformed_output.db', table_name='TransformedData'):
    username = getpass.getuser()
    df = df.rename(columns={'message': 'Button'})

    # Prepare and clean the input dataframe
    df['dwell_time'] = df['release_time'] - df['press_time']
    df = df[df['dwell_time'] > 0]
    df = df[df['Button'].str.isalpha()]
    df['is_enter'] = df['Button'].str.lower() == 'enter'
    df['message_id'] = df['is_enter'].cumsum()
    df['user_id'] = username
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
            row[f'dwell_{key}'] = key_dwell.mean() if not key_dwell.empty else 0

        feature_rows.append(row)

    # Create output DataFrame
    transformed_df = pd.DataFrame(feature_rows)

    # Save to SQLite DB
    with sqlite3.connect(output_db_path) as conn:
        transformed_df.to_sql(table_name, conn, if_exists='replace', index=False)

    print(f"Transformed data saved to {output_db_path} (table: {table_name})")

df = pd.read_sql("SELECT * FROM messages", sqlite3.connect("../data/Database.db"))
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