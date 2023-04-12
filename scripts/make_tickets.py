"""
Creates data/processed/tickets.csv using data/raw/scoreboard.html.

data/processed/tickets.csv is a table that lists the number of tickets won by
each team, and data/raw/scoreboard.html is the scoreboard downloaded directly
from https://calicojudge.com/domjudge/public after the scoreboard has been
unfrozen for the current contest.
"""

from html.parser import HTMLParser
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCOREBOARD_HTML = PROJECT_ROOT / 'data/raw/scoreboard.html'
tickets_CSV = PROJECT_ROOT / 'data/processed/tickets.csv'

print('Parsing scoreboard.html into tickets.csv...')

# Parse scoreboard html into a dict with tickets for each team
class ScoreboardTicketsParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.tickets = {}
        self.curr_team = None
    
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'td' and 'class' in attrs and 'scoretn' in attrs['class']:
            self.curr_team = attrs['title']
            self.tickets[self.curr_team] = 0
        if tag == 'div' and 'class' in attrs and 'score_correct' in attrs['class']:
            if self.tickets[self.curr_team] == 0:
                self.tickets[self.curr_team] += 10
            else:
                self.tickets[self.curr_team] += 1

parser = ScoreboardTicketsParser()
# utf8 because y'all love emojis so much xdddd
parser.feed(SCOREBOARD_HTML.read_text(encoding='utf8'))

# Load tickets dict into table
tickets = pd.DataFrame.from_records(list(parser.tickets.items()))
tickets.columns = ['team_name', 'tickets']
tickets['team_name'] = tickets['team_name'].str.strip()

assert not any(tickets['team_name'].duplicated())

# Make csv from tickets table
tickets.to_csv(tickets_CSV, index=False, lineterminator='\n')

print('Done!')
