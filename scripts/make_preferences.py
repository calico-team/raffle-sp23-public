"""
Creates data/processed/preferences.csv using data/raw/registrations.csv and
data/raw/feedback.csv.

data/processed/preferences.csv is a table that gives the prize preferences for
each contestant that submitted a feedback form (using their registration email)
and also what team they are on. Note that data/raw/registrations.csv and
data/raw/feedback.csv contain sensitive information (emails, real names, etc) so
it has been omitted from the public release.
"""

from pathlib import Path

import pandas as pd

PRIZE_COL_PREFIX = 'Raffle Prizes Ranking'

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REGISTRATIONS_CSV = PROJECT_ROOT / 'data/raw/registrations.csv'
FEEDBACK_CSV = PROJECT_ROOT / 'data/raw/feedback.csv'
PREFERENCES_CSV = PROJECT_ROOT / 'data/processed/preferences.csv'

print('Merging registrations.csv and feedback.csv into preferences.csv...')

# Load data
registrations = pd.read_csv(REGISTRATIONS_CSV)
feedback = pd.read_csv(FEEDBACK_CSV)

# Clean data
prize_cols = filter(lambda c: c.startswith(PRIZE_COL_PREFIX), feedback.columns)
feedback = feedback[['Registration Email', *prize_cols]]
feedback = feedback.rename(columns={'Registration Email': 'email'})
feedback = feedback[~feedback['email'].isna()]
feedback['email'] = feedback['email'].str.strip().str.lower()

# Remove non-pre-college teams
registrations = registrations[registrations['Are all team members pre-college students?'] == 'Yes']

# Make contestants table with email, display name, and team
contestants = pd.concat([
    registrations[[f'[Team Member {i}] Email', f'[Team Member {i}] Display Name', 'Team Name']]
        .rename(columns={'Team Name': 'team_name'})
        .rename(columns={'Are all team members pre-college students?': 'pre_college'})
        .rename(columns={f'[Team Member {i}] Display Name': 'display_name'})
        .rename(columns={f'[Team Member {i}] Email': 'email'})
        .fillna({'display_name': registrations[f'[Team Member {i}] Full Name']})
        .dropna()
        .apply(lambda col: col.str.strip(), axis=0)
    for i in range(1, 4)
])
contestants['email'] = contestants['email'].str.lower()

# This should have been resolved before the contest...
assert not any(contestants['email'].duplicated())

# If duplicated registration emails in feedback form, use the most recently
# submitted one for actual preferences
feedback = feedback.drop_duplicates(subset='email', keep='last')

# Make preference table with display name, team, and preferences
preferences = feedback.merge(contestants, how='left', on='email')

# Must have registered with an invalid email or something?
print('WARNING: unable to find registrations for the following raffle entries:')
print('\n'.join(preferences[preferences['team_name'].isna()]['email']))
preferences = preferences.dropna()

prize_cols = filter(lambda c: c.startswith(PRIZE_COL_PREFIX), feedback.columns)
preferences = preferences[['display_name', 'team_name', *prize_cols]]
for c in preferences.columns:
    if c.startswith(PRIZE_COL_PREFIX):
        preferences[c] = preferences[c].astype(int)
preferences = preferences.sort_values(by=['display_name', 'team_name'])

# Make csv from preferences table
preferences.to_csv(PREFERENCES_CSV, index=False, lineterminator='\n')

print('Done!')
