import pandas as pd
import numpy as np

# Configuration
num_users = 10
messages_per_user = 100
letters = list("abcdefghijklmnopqrstuvwxyzö")
columns = ['message_id', 'user_id', 'message_length', 'avg_dwell', 'std_dwell',
           'key_diversity', 'typing_duration'] + [f'dwell_{c}' for c in letters]

data = []

for user_index in range(1, num_users + 1):
    user_id = f'user_{user_index:03d}'  # Creates user_001, user_002, ...
    rng = np.random.default_rng(seed=user_index)  # User-specific pattern

    for msg_id in range(messages_per_user):
        message_length = rng.integers(5, 20)
        key_diversity = rng.integers(3, min(message_length, 10))
        avg_dwell = rng.uniform(0.08, 0.3)
        std_dwell = rng.uniform(0.01, 0.07)
        typing_duration = message_length * avg_dwell + rng.normal(0, 0.1)

        dwell_times = {f'dwell_{c}': 0.0 for c in letters}
        used_letters = rng.choice(letters, size=key_diversity, replace=False)

        for letter in used_letters:
            dwell_times[f'dwell_{letter}'] = rng.normal(loc=avg_dwell, scale=std_dwell)

        row = {
            'message_id': f'{user_id}_{msg_id}',
            'user_id': user_id,
            'message_length': message_length,
            'avg_dwell': avg_dwell,
            'std_dwell': std_dwell,
            'key_diversity': key_diversity,
            'typing_duration': typing_duration
        }
        row.update(dwell_times)
        data.append(row)

# Create DataFrame
df = pd.DataFrame(data, columns=columns)

# Save to CSV
df.to_csv('synthetic_typing_data.csv', index=False)
print("CSV file 'synthetic_typing_data.csv' created successfully.")