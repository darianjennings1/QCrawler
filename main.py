# This code uses the Appium python-client can be installed from PyPi - "pip install Appium-Python-Client"
# Generates a (.db) file - SQlite Studio
# Code is set up (appPackage & appActivity) for 'Traccar Client' application

from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import TimeoutException
from appium import webdriver
from random import uniform
from abstraction import *
from read_and_write import output_file
from sqlDatabase import *
from ui_analysis import *
from execution import *
import sqlite3
from QLearningFunctions import *

sqliteConnection = sqlite3.connect('Application_Database.db')
cursor = sqliteConnection.cursor()
create_database()
done = False
prev_len = 0

# Retrieving the max rowNumber in order to continue the table
cursor.execute(
    "SELECT rowNumber FROM Application_Table WHERE (rowNumber = (SELECT MAX(rowNumber) FROM Application_Table))")
count = cursor.fetchone()

# If the rowNumber DNE then count = 0 otherwise start with the next iteration of the max rowNumber
if count is None:
    count = 0
else:
    count = count[0]
    count += 1

global index
# crashLogger will keep track of the testCases that lead to application crashes, testCase is reset if appended to crashLogger
crashLogger = []
testCase = []

# timer = time.time() + 60 * 20
# while time.time() < timer:
while not done:
    # Method that starts the application
    caps = {"platformName": "Android", "deviceName": "emulator-5554", "appPackage": "org.traccar.client",
            "appActivity": "org.traccar.client.Launcher", "platformVersion": "5.1.1",
            "noReset": True}

    try:
        driver = webdriver.Remote("http://localhost:4723/wd/hub", caps)
    except:
        print('Could not boot driver...')
        continue

    sqliteConnection = sqlite3.connect('Application_Database.db')
    cursor = sqliteConnection.cursor()

    while True:

        randNum = uniform(0.0, 1.0)
        home_button_probability = .05

        if randNum <= home_button_probability:
            # At the specified state, generate the home event
            current_state = get_current_state(driver)
            Selected_event = create_home_event('bb1e312877a55bb7ae166f4e0ba6d0bd84e360d6')
        else:
            try:
                current_state = get_current_state(driver)
                Current_Events = get_available_events(driver)
            except WebDriverException or TimeoutException as e:
                print('WebDriverException or TimeoutException occured, could not retrieve current state/events')
                continue

            D = Executor(driver, 3, " ")
            print("Successfully retrieved the current events")
            rowList = []
            # If the current state is new then add it to the table
            if not isKnownState(current_state['stateId']):
                print("Current State is a new state")
                for events in Current_Events:
                    insert_into(count, str(events['actions']), str(events['precondition']['stateId']), 0, 500, 5)
                    events['rowNumber'] = count
                    count += 1
                    rowList.append(count)
                print("This is the current_state['stateId'] " + str(current_state['stateId']))
                sqliteConnection.commit()

            elif isKnownState(current_state['stateId']):
                print("State is known, retrieving events & adding new (if any)")
                print(current_state['stateId'])

                # number of events in current events
                numOfEvents = len(Current_Events)
                print('Numbers of events in CurrentEvents: ' + str(numOfEvents))
                # number of events in the database with known stateID

                cursor.execute("SELECT rowNumber FROM Application_Table WHERE (EventKey = ?)",
                               [current_state['stateId']])
                rowNumber = cursor.fetchall()
                databaseEvents = len(rowNumber)
                print('Numbers of events in database: ' + str(databaseEvents))

                rowList = [row[0] for row in rowNumber]

                i = 0
                if numOfEvents != databaseEvents:
                    print("Database number of events != number of available events")
                    while numOfEvents != databaseEvents:
                        insert_into(count, str(Current_Events[numOfEvents]['actions']),
                                    str(Current_Events[numOfEvents]['precondition']['stateId']), 0, 500, 5)
                        numOfEvents -= 1
                        rowList.append(count)
                        count += 1

                for events in Current_Events:
                    events['rowNumber'] = rowList[i]
                    i += 1

                sqliteConnection.commit()

        # index is retrieving the literal rowNumber from the Sqlite database
        print("List of row numbers for the given stateID: " + str(rowList))
        index = getMaxValueEvent(current_state['stateId'])

        # selects event that matches pulled index (rowNumber) within the available current events
        for events in Current_Events:
            if events['rowNumber'] == index:
                Selected_event = events

        print("Executing selected event " + str(Selected_event['precondition']) + " at index: " + str(index))
        D.execute(Selected_event)

        # after execution, append each event to a testCase - will check if appended event leads to crash
        testCase.append(Selected_event)
        print('\n' * 2)

        cursor.execute("UPDATE Application_Table SET TimesExecuted = TimesExecuted + 1 WHERE (rowNumber= ?)",
                       [index])
        print("Updated the times executed in the database table at row " + str(index))
        sqliteConnection.commit()
        print('\n' * 2)

        newState = get_current_state(driver)
        app_state = driver.query_app_state('org.traccar.client')
        print(app_state)

        # Cases to see if it crashes or if it exits from the app
        if newState['stateId'] == 'crash':

            # Append the testCase, contains events that led up to crash
            crashLogger.append(testCase)
            output_file(crashLogger)
            # empty list for next iteration
            testCase = []

            cursor.execute("UPDATE Application_Table SET Reward = 0, QValues = 0 WHERE (rowNumber= ?)", [index])
            print("Crash occurred, updated the reward and Q-Values in the table at row " + str(index))
            sqliteConnection.commit()
            break

        # If the application is not running
        elif app_state == 1:

            # Append the elements that lead up to the crash
            crashLogger.append(testCase)
            output_file(crashLogger)

            # Making an empty list for the events that we select
            testCase = []

            cursor.execute("UPDATE Application_Table SET Reward = 0, QValues = 0 WHERE (rowNumber= ?)", [index])
            print("Crash occurred, updated the reward and Q-Values to 0 in the table at row " + str(index))
            sqliteConnection.commit()

            break

        # If the application is running in the background, exited AUT
        elif (app_state == 3) or (app_state == 2):

            cursor.execute("UPDATE Application_Table SET QValues = 0, Reward = 0 WHERE (rowNumber= ?)", [index])
            print("Exited AUT, updated the QValue and reward to 0 in the table at row " + str(index))
            sqliteConnection.commit()
            break

        new_events = get_available_events(driver)
        gamma = calDiscountFactor(new_events)

        i = 0
        rowList = []
        # If the current state is new then add it to the table
        if not isKnownState(newState['stateId']):
            print("New current state is a new state")
            for n_events in new_events:
                insert_into(count, str(n_events['actions']), str(n_events['precondition']['stateId']), 0, 500, 5)
                n_events['rowNumber'] = count
                rowList.append(count)
                count = count + 1

        # if state already exists, pull those rowNumbers from the database by stateID, insert new events if there are any
        elif isKnownState(newState['stateId']):
            print("New state is known, retrieving events & adding new (if any)")
            print(current_state['stateId'])

            # number of events in current events
            numOfEvents = len(Current_Events)
            print('Numbers of events in CurrentEvents: ' + str(numOfEvents))
            # number of events in the database with known stateID
            databaseEvents = len(rowNumber)
            print('Numbers of events in database: ' + str(databaseEvents))

            cursor.execute("SELECT rowNumber FROM Application_Table WHERE (EventKey = ?)",
                           [current_state['stateId']])
            rowNumber = cursor.fetchall()
            rowList = [row[0] for row in rowNumber]

            i = 0
            if numOfEvents != databaseEvents:
                print("Database number of events != number of available events")
                while numOfEvents != databaseEvents:
                    insert_into(count, str(Current_Events[numOfEvents]['actions']),
                                str(Current_Events[numOfEvents]['precondition']['stateId']), 0, 500, 5)
                    numOfEvents -= 1
                    rowList.append(count)
                    count += 1

            for events in Current_Events:
                events['rowNumber'] = rowList[i]
                i += 1

            sqliteConnection.commit()

        print(
            "This is the list of rowNumber that is being pulled " + str(rowList) + " For this specific state: " + str(
                current_state['stateId']))
        print('\n' * 2)

        reward = getReward(index)

        # Getting the Maximum Value from the new_events
        maxValue = getMaxValue(newState['stateId'])

        # Getting the value from the Q_Value Function
        Q_Value = reward + gamma * maxValue

        # Giving the new Q value to the event
        print("This is the selected event: ")
        print(Selected_event)

        updateValues(Selected_event['rowNumber'], round(Q_Value, 2), reward)
        print("Successfully updated the Q-Value at row " + str(index) + " with the value of " + str(Q_Value))
        print('\n' * 2)
