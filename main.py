__author__ = "Mike Ebbe"
__copyright__ = "Copyright 2022, Mike Ebbe"
__credits__ = ["Mike Ebbe", "snooker.org"]
__license__ = "MIT"
__version__ = "0.7"

# Imports
import os
import requests
from dotenv import load_dotenv
from datetime import date, datetime

load_dotenv()

live_events = []
today = date.today()


# Get current season based on date
def get_season():
    cdate = today.strftime('%m-%d')  # Current date
    year = today.year  # Current year

    season_end = '05-31'  # End of season

    # Determine season
    if cdate <= season_end:
        season = year - 1
        print(str(today) + ' falls within the ' + str(season) + '/' + str(year) + ' season')
    else:
        season = year
        print(str(today) + ' falls within the ' + str(season) + '/' + str((year + 1)) + ' season')

    get_events(season)


# Get events in current season with snooker.org API
def get_events(season):
    events = requests.get('http://api.snooker.org/?t=5&s=' + str(season))  # Events in current season
    events = sorted(events.json(), key=lambda d: d['Name'])  # Sort events by name

    # Determine ongoing events
    for event in events:
        if datetime.strptime(event['StartDate'], '%Y-%m-%d').date() <= today <= datetime.strptime(event['EndDate'], '%Y-%m-%d').date():
            print(event['Name'] + " is live!")
            live_events.append({'id': event['ID'], 'name': event['Name'], 'start': event['StartDate'], 'end': event['EndDate'], 'type': event['Type']})  # Append to live_events list

    get_results()


# Get results of live events
def get_results():
    matches = []
    players = []
    rounds = []
    matches_today = []

    # Get matches, players and rounds for each live event
    for event in live_events:
        matches.extend(requests.get('http://api.snooker.org/?t=6&e=' + str(event['id'])).json())  # Get matches
        players.extend(requests.get('http://api.snooker.org/?t=9&e=' + str(event['id'])).json())  # Get players
        rounds.extend(requests.get('http://api.snooker.org/?t=12&e=' + str(event['id'])).json())  # Get rounds
        players = [dict(t) for t in {tuple(d.items()) for d in players}]  # Remove duplicate players

    # Get and format the results of today
    for match in matches:
        if match['StartDate']:  # Match has started
            start_date = datetime.strptime(match['StartDate'], '%Y-%m-%dT%H:%M:%SZ')  # Convert to datetime
            scheduled_date = datetime.strptime(match['ScheduledDate'], '%Y-%m-%dT%H:%M:%SZ')  # Convert to datetime
            if start_date.date() == today or scheduled_date.date() == today:  # Match either started or continued today
                for round in rounds:
                    if match['EventID'] == round['EventID'] and match['Round'] == round['Round']:
                        match['Round'] = round['RoundName']
                        matches_today.append(match)

    display_matches(matches_today, players)


# Display the matches
def display_matches(matches, players):
    print('There are ' + str(len(matches)) + ' matches today (' + str(today) + '):')

    # Assign player key values
    for match in matches:
        for player in players:
            if match['Player1ID'] == player['ID']:
                match['Player1FirstName'] = player['FirstName']
                match['Player1LastName'] = player['LastName']
                match['Player1FullName'] = match['Player1FirstName'] + ' ' + match['Player1LastName'] if not player['SurnameFirst'] else match['Player1LastName'] + ' ' + match['Player1FirstName']
                match['Player1Photo'] = player['Photo']
                match['Player1Country'] = player['Nationality']
                match['Player1CountryPhoto'] = "http://www.snooker.org/res/scorekeeper/gfx/flags/icondrawer/16/" + player['Nationality'].replace(" ", "%20") + ".png"
            if match['Player2ID'] == player['ID']:
                match['Player2FirstName'] = player['FirstName']
                match['Player2LastName'] = player['LastName']
                match['Player2FullName'] = match['Player2FirstName'] + ' ' + match['Player2LastName'] if not player['SurnameFirst'] else match['Player2LastName'] + ' ' + match['Player2FirstName']
                match['Player2Photo'] = player['Photo']
                match['Player2Country'] = player['Nationality']
                match['Player2CountryPhoto'] = "http://www.snooker.org/res/scorekeeper/gfx/flags/icondrawer/16/" + player['Nationality'].replace(" ", "%20") + ".png"

        print(match['Player1FullName'] + ' ' + str(match['Score1']) + '-' + str(match['Score2']) + ' ' + match['Player2FullName'])

    mail_results(matches)


# Mail the results
def mail_results(matches):
    import yagmail

    print('Sending mail...')

    yag = yagmail.SMTP(os.environ.get('gmail_username'), os.environ.get('gmail_password'))
    contents = []
    html = '<h1>Your daily snooker results for ' + today.strftime('%d %B %Y') + '</h1>'

    # Create HTML table for each event
    for event in live_events:
        html += '<table><thead><tr><th colspan="6">' + event['name'] + '</th></tr></thead><tbody>'
        # Create table row for each match
        for match in matches:
            if match['EventID'] == event['id']:
                html += '<tr><td style="padding-right:20px">' + match['Round'] + '</td><td><img style="vertical-align:middle" src="http://www.snooker.org/res/scorekeeper/gfx/flags/icondrawer/16/' + match['Player1Country'] + '.png" alt="' + match['Player1Country'] + '"/></td><td>' + match['Player1FullName'] + '</td><td>' + str(match['Score1']) + '-' + str(match['Score2']) + '</td><td><img style="vertical-align:middle" src="http://www.snooker.org/res/scorekeeper/gfx/flags/icondrawer/16/' + match['Player2Country'] + '.png" alt="' + match['Player2Country'] + '"</td><td>' + match['Player2FullName'] + '</td></tr>'
        html += '</tbody></table>'

    contents.append(html)

    yag.send(os.environ.get('recipient'), 'Daily snooker results', contents)  # Send mail

    print('Done!')


# Initialize
get_season()
