import requests
import time as ttime
from datetime import datetime, date, time, timedelta
from bs4 import BeautifulSoup
import json
import functools
import os

club_id = os.getenv('club_id')
strava_session_cookie = os.getenv('strava_session_cookie')
team_captain_america = os.getenv('team_captain_america').split(',')
team_iron_man = os.getenv('team_iron_man').split(',')

april_first_midnight_epoch_timestamp = 1617249600

class Activity():
    def __init__(self, userId, username, timestamp, duration, activity_type):
        self.userId = userId
        self.username = username
        self.timestamp = timestamp
        self.epoch_timestamp = ttime.mktime(timestamp.timetuple())
        self.duration = duration
        self.activity_type = activity_type

    def __eq__(self, other):
        if isinstance(other, Activity):
            return self.userId == other.userId and \
                self.username == other.username and \
                self.timestamp == other.timestamp and \
                self.epoch_timestamp == other.epoch_timestamp and \
                self.duration == other.duration and \
                self.activity_type == other.activity_type
        return False

    def __hash__(self):
        return hash((self.userId, self.username, self.timestamp, self.epoch_timestamp, self.duration, self.activity_type))

    def __repr__(self):
        return json.dumps(self.__dict__,default=str,indent=4)

def getActivitiesFromSoup( soup ):
    activityElements = soup.find_all( 'div', class_='entry-container' )
    activities = []

    for entryElements in activityElements:
        headerElements = entryElements.find('div', class_='entry-head')
        bodyElements = entryElements.find('div', class_='entry-body')

        activityDiv = headerElements.parent
        bodyDiv = bodyElements.parent

        activityType = bodyDiv.find('strong').find('a').text
        userId = activityDiv.find('a', class_='entry-athlete')['href'].split('/')[2]
        if activityDiv.find('time', class_='timestamp') is None:
            activityDateTime = activities[-1].timestamp
        else:
            activityDateTime = datetime.fromisoformat(activityDiv.find('time', class_='timestamp')['datetime'][:-4])

        name = next(activityDiv.find('a', class_='entry-athlete').strings).strip()
        durationElement = activityDiv.find('li', title='Time')
        parsed_duration = parseDurationFromTimeElement( durationElement )
        activity = Activity( userId, name, activityDateTime, parsed_duration, activityType )
        activities.append(activity)

    return activities

def getActivitiesPageContentFromStrava( lastActivityTimestamp=None ):
    cookies = {'_strava4_session': strava_session_cookie}
    uri = f"https://www.strava.com/clubs/{club_id}/feed?feed_type=club"

    if lastActivityTimestamp:
        uri += f'&before={lastActivityTimestamp}&cursor={lastActivityTimestamp}'

    return requests.get(uri, cookies=cookies).content

def parseDurationFromTimeElement( timeElement ):
    timeIterable = timeElement.strings
    timeList = zip(timeIterable, timeIterable)
    hour = 0
    minute = 0
    second = 0
    for el in timeList:
        if el[1] == 'h':
            hour = int(el[0])
        elif el[1] == 'm':
            minute = int(el[0])
        elif el[1] == 's':
            second = int(el[0])
    timeobj = time(hour=hour, minute=minute, second=second)
    return datetime.combine(date.min, timeobj) - datetime.min

def getActivitesSinceDefinedTime():
    last_epoch_timestamp = ttime.time()
    activities = []
    while( last_epoch_timestamp > april_first_midnight_epoch_timestamp ):
        pageContent = getActivitiesPageContentFromStrava(last_epoch_timestamp)
        soup = BeautifulSoup(pageContent, 'html.parser')
        activities += getActivitiesFromSoup( soup )
        last_epoch_timestamp = activities[-1].epoch_timestamp

    unique_activities = list(set(filter(lambda x: x.epoch_timestamp > april_first_midnight_epoch_timestamp ,activities)))
    return sorted(unique_activities, key = lambda x: x.epoch_timestamp)

def getTotalActivitiesDuration():
    return str(getDurationSum(getActivitesSinceDefinedTime()))

def getDurationSum( activityList ):
    if (len(activityList) == 0):
        return 0

    duration_list = map(lambda x: x.duration, activityList)
    return functools.reduce(lambda x, y: x+y, duration_list)

def getWeightedDurationSum( activityList ):
    if (len(activityList) == 0):
        return 0

    weighted_durations = [x.duration.total_seconds() * getActivityWeight(x.activity_type) for x in activityList]
    return timedelta(seconds=round(sum(weighted_durations)))

def getActivityWeight(activity_type):
    activityWords = activity_type.lower().split(' ')

    if "run" in activityWords:
        return 1.5
    elif "ride" in activityWords:
        return 1.25
    else:
        return 1.0

def getActivitiesByUsername( activityList ):
    activities_by_user = {}
    for activity in activityList:
        if activity.username not in activities_by_user.keys():
            activities_by_user[activity.username] = [activity]
        else:
            activities_by_user[activity.username].append(activity)

    return activities_by_user

def getTeamDurationTotals():
    activities = getActivitesSinceDefinedTime()

    captain_america_activies = [x for x in activities if x.userId in team_captain_america]
    iron_man_activies = [x for x in activities if x.userId in team_iron_man]

    total_captain_america_duration = getDurationSum(captain_america_activies)
    total_iron_man_duration = getDurationSum(iron_man_activies)
    weighted_captain_america_duration = getWeightedDurationSum(captain_america_activies)
    weighted_iron_man_duration = getWeightedDurationSum(iron_man_activies)

    totals = { 'Team Captain America Total Active Time': str(total_captain_america_duration),
             'Team Iron Man Total Active Time': str(total_iron_man_duration),
             'Team Captain America Weighted Active Time': str(weighted_captain_america_duration), 
             'Team Iron Man Weighted Active Time': str(weighted_iron_man_duration)}
    return json.dumps(totals,default=str,indent=4)

def getLeaderboardByTotalDuration():
    activities = getActivitesSinceDefinedTime()

    activities_by_user = getActivitiesByUsername(activities)
    ordered_user_totals_by_duration = sorted([(k, getDurationSum(v)) for k, v in activities_by_user.items()], key=lambda x: x[1],reverse=True)

    result_dict = {}
    for user_entry in ordered_user_totals_by_duration:
        result_dict[user_entry[0]] = user_entry[1]
    
    return json.dumps(result_dict,default=str,indent=4)

def getLeaderboardByWeightedDuration():
    activities = getActivitesSinceDefinedTime()

    activities_by_user = getActivitiesByUsername(activities)
    ordered_user_totals_by_duration = sorted([(k, getWeightedDurationSum(v)) for k, v in activities_by_user.items()], key=lambda x: x[1],reverse=True)

    result_dict = {}
    for user_entry in ordered_user_totals_by_duration:
        result_dict[user_entry[0]] = user_entry[1]
    
    return json.dumps(result_dict,default=str,indent=4)

def main():
    print("Unweighted Durations")
    print(getLeaderboardByTotalDuration())
    print("Weighted Durations")
    print(getLeaderboardByWeightedDuration())
    return

if "__main__" in __name__:
    main()