import random
import sqlite3
from QLearningFunctions import *


def create_database():
    try:
        sqliteConnection = sqlite3.connect('Application_Database.db')
        sqlite_create_table_query = '''CREATE TABLE Application_Table (
                                    RowNumber INTEGER NOT NULL,
                                    EventValue TEXT NOT NULL,
                                    EventKey TEXT NOT NULL,
                                    TimesExecuted INTEGER NOT NULL,
                                    QValues REAL NOT NULL, 
                                    Reward REAL
                                    );'''
        cursor = sqliteConnection.cursor()
        print("Successfully Connected to SQLite")

        cursor.execute(sqlite_create_table_query)
        sqliteConnection.commit()
        print("SQLite table created")

        cursor.close()

    except sqlite3.Error as error:
        print("Error while creating a sqlite table", error)
    finally:
        if (sqliteConnection):
            sqliteConnection.close()
            print("sqlite connection is closed")


def insert_into(rowID, eventValue, eventKey, timesExecuted, qValue, reward):
    try:
        sqliteConnection = sqlite3.connect('Application_Database.db')
        cursor = sqliteConnection.cursor()
        sqlite_insert_with_param = """INSERT INTO Application_Table
                              (RowNumber, EventValue, EventKey, TimesExecuted, QValues, Reward) 
                              VALUES (?, ?, ?, ?, ?, ?);"""

        data = (rowID, eventValue, eventKey, timesExecuted, qValue, reward)
        cursor.execute(sqlite_insert_with_param, data)
        sqliteConnection.commit()
        cursor.close()

    except sqlite3.Error as error:
        print("Failed to insert Python variable into sqlite table", error)
    finally:
        if (sqliteConnection):
            sqliteConnection.close()


def getMaxValueEvent(stateId):
    try:
        sqliteConnection = sqlite3.connect('Application_Database.db')
        cursor = sqliteConnection.cursor()

        maxQvalue = getMaxValue(stateId)
        # retrieve the rowNumbers where the Q-Value is max and at the specified StateID, returns a list of tuples
        cursor.execute("SELECT RowNumber FROM Application_Table WHERE (QValues = ?) AND (EventKey = ?)",
                       [maxQvalue, stateId])
        numbers = cursor.fetchall()
        # convert list of tuples -> list
        row_numbers = [i[0] for i in numbers]

        print('Getting maxValueEvent from these rowNumbers in database: \n' + str(row_numbers))
        maxRowNumber = random.choice(row_numbers)
        cursor.close()
        return maxRowNumber

    except sqlite3.Error as error:
        print("Failed to access data from sqlite table", error)
    finally:
        if (sqliteConnection):
            sqliteConnection.close()
            print("The SQLite connection is closed")


def isKnownState(stateId):
    sqliteConnection = sqlite3.connect('Application_Database.db')
    cursor = sqliteConnection.cursor()
    # Pull all stateID's from database table, returns a list of tuples
    cursor.execute("SELECT EventKey FROM Application_Table")

    stateList = cursor.fetchall()
    knownStates = [state[0] for state in stateList]

    # Checking to see if the stateId exists within the database table
    if stateId not in knownStates:
        return False
        # if the stateId is not within the known states, then it is a new state
    else:
        # if the stateId is within the table, we can obtain the rowNumbers from that stateID
        return True
