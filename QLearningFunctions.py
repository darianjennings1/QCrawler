import math
import sqlite3


def calDiscountFactor(available_events):
    discount_factor = 0.9 * math.exp(-0.1 * (len(available_events) - 1))

    return discount_factor


def getReward(selectedEvent_index):
    # establishing the connection to the database
    sqliteConnection = sqlite3.connect('Application_Database.db')
    cursor = sqliteConnection.cursor()

    # Performs the SQL actions within the database
    cursor.execute("Select TimesExecuted FROM Application_Table WHERE RowNumber = ?", [selectedEvent_index])
    x = cursor.fetchone()
    # convert to integer
    res = int(''.join(map(str, x)))

    # one divided by the total number of times the event has been executed
    reward = 1 / res

    return round(reward, 2)


def getMaxValue(stateId):
    stateId = str(stateId)

    # Establishing the connection to the database
    sqliteConnection = sqlite3.connect('Application_Database.db')
    cursor = sqliteConnection.cursor()

    # Pulling the events from the table into a list
    cursor.execute("SELECT QValues FROM Application_Table WHERE (EventKey = ?)", [stateId])

    qValues = cursor.fetchall()
    print('Given this stateID: ' + str(stateId))
    print('Retrieved these qValue(s) for given stateID: ' + str(qValues))
    i = 0
    i = max(qValues)[0]

    cursor.close()

    return float(i)


def updateValues(Index_Of_Event, Q_Value, reward):
    # Establishing the connection to the database
    sqliteConnection = sqlite3.connect('Application_Database.db')
    cursor = sqliteConnection.cursor()

    cursor.execute("UPDATE Application_Table SET QValues = ?, Reward = ? WHERE RowNumber = ?",
                   [Q_Value, reward, Index_Of_Event])
    sqliteConnection.commit()

    # return Action, State_ID
