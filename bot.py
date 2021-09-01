## https://www.youtube.com/watch?v=PTAkiukJK7E
#https://towardsdatascience.com/how-to-deploy-a-telegram-bot-using-heroku-for-free-9436f89575d2
# This is the psycopg2 documentation needed to manage the database
#https://www.psycopg.org/docs/sql.html

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import logging
from telegram.ext import (
    Updater,
    CommandHandler,
    ConversationHandler,
    CallbackContext,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
)
from datetime import *
from decouple import config
import os
import psycopg2
from calendar import monthrange

PORT = int(os.environ.get('PORT', '8443'))

API_KEY = "API_KEY"
# Configuring the database by connecting to my heroku postgres database
conn = psycopg2.connect(
                host='host',
                database='database',
                user='user',
                password='password',
)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS FREETIME(
            group_name text,
            user_name text,
            week text,

free_timeslots text)''')
conn.commit()

c.execute('''CREATE TABLE IF NOT EXISTS GROUPS(
            group_name text,
            group_password text)''')

conn.commit()
conn.close()

# Create the Updater and pass it your bot's token.
updater = Updater(token=API_KEY, use_context=True)

# Get the dispatcher to register handlers
dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

logger = logging.getLogger(__name__)

# Conversation for registering group and password
data = {'group': "", 'password': ""}
GROUP = 1
PASSWORD = 2

# Command Handler which starts conversation
def register(update, context):
    global data # to assign new dictionary to external/global variable

    # create new empty dictionary
    data = {'group': "", 'password': ""}

    update.message.reply_text("What is your group name?")

    # next state in conversation
    return GROUP

def get_group(update, context):
    data['group'] = update.message.text
    update.message.reply_text("What is your group password?")

    # next state in conversation
    return PASSWORD

def get_grouppw(update, context):
    data['password'] = update.message.text
    conn6 = psycopg2.connect(
                host='host',
                database='database',
                user='user',
                password='password',
    )
    c6 = conn6.cursor()
    c6.execute('''SELECT group_name FROM GROUPS''')
    names = c6.fetchall()
    groupnames = []
    for i in names:
        groupnames.append(i[0])
    if data['group'] in groupnames:
        c6.execute('''SELECT group_password FROM GROUPS WHERE group_name = (%s) ''', (data['group'],))
        pw = c6.fetchone()[0]
        if pw == data['password']:
            update.message.reply_text("You have successfully signed in to your group!")
        else:
            update.message.reply_text("Passwords do not match. Please register again.")
    else:
        c6.execute('''INSERT INTO GROUPS (group_name, group_password) VALUES (%s, %s)''', (data['group'], data['password']))
        update.message.reply_text("New group name and password registered!")

    conn6.commit()
    conn6.close()

    # end of conversation
    return ConversationHandler.END

def cancel(update, context):

    update.message.reply_text('canceled')

    # end of conversation
    return ConversationHandler.END

day = 0
freeslots = []
# Stages
FIRST, SECOND, THIRD = range(3)
# Callback data
Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday, Morning, Afternoon, Night = range(10)


def log(prevanswer, context, update):
    daysofweek = ["Monday", "Tuesday", "Wednesday", "Thursday", 'Friday', 'Saturday',
                  'Sunday', 'Morning', 'Afternoon', 'Night']
    query = update.callback_query
    if 6 < int(query.data) < 10:
        freeslot = prevanswer + " " + daysofweek[int(query.data)]
        freeslots.append(freeslot)
        freeslotstext = ""
        for i in freeslots:
            freeslotstext += i + ", "
        text = user.first_name + " is free on " + freeslotstext
        logger.info(text)
#        context.bot.send_message(text=text, chat_id=update.effective_message.chat_id)
    else:
        text = user.first_name + " is free on " + daysofweek[int(query.data)]
        logger.info(text)
    global day
    day = daysofweek[int(query.data)]

def start(update: Update, context: CallbackContext) -> int:
    """Send message on `/start`."""
    # Get user that sent /start and log his name
    # Send starting message
    text = """Welcome to WhenDavai? bot. This bot allows groups of people to input their free times within the span of 
    the coming week in order for the bot to identify common timeslots for the group. This facilitates planning for group
    meetings and activities as the bot automatically compiles the data and users would not need to manually compile them.
    
    To Use:
        1) /register : Enter your group name and password in order to obtain access to your own private group
        2) /start : Start the prompt to input free times for the next week. After inputting one timing, users may select 
        "Log another time slot" to select another time slot in which they are free. Once all free timeslots are logged 
        into the bot, select "Finish" to save your input into your group's bot database.
        3) /thisweekresult : Display who's free on all the timeslots for this week
        4) /nextweekresult : Display who's free on all the timeslots for next week
        5) /meet : Find out the day in which most people are free
        6) /edit : Edit your input if there are any last minute changes before the week begins"""


    context.bot.send_message(text=text, chat_id=update.effective_message.chat_id)
    global user
    user = update.message.from_user
    global freeslots
    freeslots = []
    logger.info("User %s started the conversation.", user.first_name)
    # Build InlineKeyboard where each button has a displayed text
    # and a string as callback_data
    # The keyboard is a list of button rows, where each row is in turn
    # a list (hence `[[...]]`).

    if data['group'] == "":
        update.message.reply_text("Please /register to your group to proceed")

    else:
        keyboard = [
            [
                InlineKeyboardButton("Monday", callback_data=str(Monday)),
                InlineKeyboardButton("Tuesday", callback_data=str(Tuesday)),
            ],
            [   InlineKeyboardButton("Wednesday", callback_data=str(Wednesday))],
            [
                InlineKeyboardButton("Thursday", callback_data=str(Thursday)),
                InlineKeyboardButton("Friday", callback_data=str(Friday)),
            ],
            [
                InlineKeyboardButton("Saturday", callback_data=str(Saturday)),
                InlineKeyboardButton("Sunday", callback_data=str(Sunday)),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        # Send message with text and appended InlineKeyboard
        update.message.reply_text("Choose a day you are free", reply_markup=reply_markup)
        # Tell ConversationHandler that we're in state `FIRST` now
        return FIRST


def edit(update: Update, context: CallbackContext) -> int:
    """Send message on `/start`."""
    # Get user that sent /start and log his name
    # Send starting message
    text = """Re-enter your edited free time slots. Similar to selecting your time slots at the beginning, press "Log another time slot" to select multiple frree time slots. Press "Finish" to save changes into the database."""
    context.bot.send_message(text=text, chat_id=update.effective_message.chat_id)
    global freeslots
    freeslots = []
    global user
    user = update.message.from_user
    keyboard = [
        [
            InlineKeyboardButton("Monday", callback_data=str(Monday)),
            InlineKeyboardButton("Tuesday", callback_data=str(Tuesday)),
        ],
        [   InlineKeyboardButton("Wednesday", callback_data=str(Wednesday))],
        [
            InlineKeyboardButton("Thursday", callback_data=str(Thursday)),
            InlineKeyboardButton("Friday", callback_data=str(Friday)),
        ],
        [
            InlineKeyboardButton("Saturday", callback_data=str(Saturday)),
            InlineKeyboardButton("Sunday", callback_data=str(Sunday)),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Send message with text and appended InlineKeyboard
    update.message.reply_text("Choose a day you are free", reply_markup=reply_markup)
    # Tell ConversationHandler that we're in state `FIRST` now
    return FIRST


def start_over(update: Update, context: CallbackContext) -> int:
    """Prompt same text & keyboard as `start` does but not as new message"""
    # Get CallbackQuery from Update
    query = update.callback_query
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Monday", callback_data=str(Monday)),
            InlineKeyboardButton("Tuesday", callback_data=str(Tuesday)),
        ],
        [   InlineKeyboardButton("Wednesday", callback_data=str(Wednesday))],
        [
            InlineKeyboardButton("Thursday", callback_data=str(Thursday)),
            InlineKeyboardButton("Friday", callback_data=str(Friday)),
        ],
        [
            InlineKeyboardButton("Saturday", callback_data=str(Saturday)),
            InlineKeyboardButton("Sunday", callback_data=str(Sunday)),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Instead of sending a new message, edit the message that
    # originated the CallbackQuery. This gives the feeling of an
    # interactive menu.
    query.edit_message_text(text="Choose a day you are free", reply_markup=reply_markup)
    return FIRST

def monday(update: Update, context: CallbackContext) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    log(day, context, update)
    query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Morning", callback_data=str(Morning)),
            InlineKeyboardButton("Afternoon", callback_data=str(Afternoon)),
            InlineKeyboardButton("Night", callback_data=str(Night)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="Monday, Choose a timing", reply_markup=reply_markup
    )
    return SECOND


def tuesday(update: Update, context: CallbackContext) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    log(day, context, update)
    query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Morning", callback_data=str(Morning)),
            InlineKeyboardButton("Afternoon", callback_data=str(Afternoon)),
            InlineKeyboardButton("Night", callback_data=str(Night)),

        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="Tuesday, Choose a timing", reply_markup=reply_markup
    )
    return SECOND


def wednesday(update: Update, context: CallbackContext) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    log(day, context, update)
    query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Morning", callback_data=str(Morning)),
            InlineKeyboardButton("Afternoon", callback_data=str(Afternoon)),
            InlineKeyboardButton("Night", callback_data=str(Night)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="Wednesday, Choose a timing", reply_markup=reply_markup
    )
    return SECOND


def thursday(update: Update, context: CallbackContext) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    log(day, context, update)
    query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Morning", callback_data=str(Morning)),
            InlineKeyboardButton("Afternoon", callback_data=str(Afternoon)),
            InlineKeyboardButton("Night", callback_data=str(Night)),

        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="Thursday, Choose a timing", reply_markup=reply_markup
    )
    return SECOND

def friday(update: Update, context: CallbackContext) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    log(day, context, update)
    query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Morning", callback_data=str(Morning)),
            InlineKeyboardButton("Afternoon", callback_data=str(Afternoon)),
            InlineKeyboardButton("Night", callback_data=str(Night)),

        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="Friday, Choose a timing", reply_markup=reply_markup
    )
    return SECOND

def saturday(update: Update, context: CallbackContext) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    log(day, context, update)
    query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Morning", callback_data=str(Morning)),
            InlineKeyboardButton("Afternoon", callback_data=str(Afternoon)),
            InlineKeyboardButton("Night", callback_data=str(Night)),

        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="Saturday, Choose a timing", reply_markup=reply_markup
    )
    return SECOND

def sunday(update: Update, context: CallbackContext) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    log(day, context, update)
    query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Morning", callback_data=str(Morning)),
            InlineKeyboardButton("Afternoon", callback_data=str(Afternoon)),
            InlineKeyboardButton("Night", callback_data=str(Night)),

        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="Sunday, Choose a timing", reply_markup=reply_markup
    )
    return SECOND

def morning(update: Update, context: CallbackContext) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    log(day, context, update)
    query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Finish", callback_data=str(Monday)),
            InlineKeyboardButton("Log another time slot", callback_data=str(Tuesday)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="Pick another time slot or leave", reply_markup=reply_markup
    )
    return THIRD

def afternoon(update: Update, context: CallbackContext) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    log(day, context, update)
    query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Finish", callback_data=str(Monday)),
            InlineKeyboardButton("Log another time slot", callback_data=str(Tuesday)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="Pick another time slot or leave", reply_markup=reply_markup
    )
    return THIRD

def night(update: Update, context: CallbackContext) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    log(day, context, update)
    query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Finish", callback_data=str(Monday)),
            InlineKeyboardButton("Log another time slot", callback_data=str(Tuesday)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="Pick another time slot or leave", reply_markup=reply_markup
    )
    return THIRD

def nameday(day):
    if day == "1":
        day += "st"
    elif day == "2":
        day += "nd"
    elif day == "3":
        day += "rd"
    else:
        day += "th"
    return day

def findindb(username, groupname, week1):
    conn1 = psycopg2.connect(
                host='host',
                database='database',
                user='user',
                password='password',
    )
    c1 = conn1.cursor()
    c1.execute('''SELECT user_name FROM FREETIME WHERE week = (%s) AND group_name = (%s)''', (week1, groupname))
    names = c1.fetchall()
    conn1.close()
    # fetchall() returns a list of tuples
    for i in names:
        if username in i:
            return True
    else:
        return False

def arraytotext(array):
    # This converts an array into text with elements separated by commas
    text = ""
    for i in array:
        if text == "":
            text += i
        else:
            text += ", " + i
    return text



def addtodb(username, freetimeslots, context, update):
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
              'November', 'December']
    # Sending this message on a sunday so must add one as the week planning timeslots for starts on monday
    # TODO program the msg to send every sunday
    dayofweek = datetime.today().weekday()
    daystonextmonday = 7 - dayofweek
    dayofnextmonday = str(date.today().day + daystonextmonday)
    month = months[date.today().month - 1]
    num_daysinmonth = monthrange(2021, date.today().month)[1]
    if int(dayofnextmonday) + 6 > num_daysinmonth:
        weeklater = str(int(dayofnextmonday) + 6 - num_daysinmonth)
    else:
        weeklater = str(int(dayofnextmonday) + 6)
    weektext = nameday(dayofnextmonday) + " to " + nameday(weeklater) + " " + month
    #text is the week for use in the database
    if findindb(user.first_name, data['group'], weektext) is True:
        return context.bot.send_message(text="You have already submitted your schedule for this week!", chat_id=update.effective_message.chat_id)

    if findindb(user.first_name, data['group'], weektext) is False:
        # if the slot for this person is not found in the db already, create a line in the db for it
        conn2 = psycopg2.connect(
                host='host',
                database='database',
                user='user',
                password='password',
        )
        c2 = conn2.cursor()
        c2.execute('''INSERT INTO FREETIME(group_name, user_name, week, free_timeslots)
            VALUES(%s, %s, %s, %s)''', (data['group'], username, weektext, arraytotext(freetimeslots)))
        conn2.commit()
        conn2.close()

def editdb(username, freetimeslots, context, update):
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
              'November', 'December']
    # Sending this message on a sunday so must add one as the week planning timeslots for starts on monday
    # TODO program the msg to send every sunday
    dayofweek = datetime.today().weekday()
    daystonextmonday = 7 - dayofweek
    dayofnextmonday = str(date.today().day + daystonextmonday)
    month = months[date.today().month - 1]
    num_daysinmonth = monthrange(2021, date.today().month)[1]
    if int(dayofnextmonday) + 6 > num_daysinmonth:
        weeklater = str(int(dayofnextmonday) + 6 - num_daysinmonth)
    else:
        weeklater = str(int(dayofnextmonday) + 6)
    weektext = nameday(dayofnextmonday) + " to " + nameday(weeklater) + " " + month
    #text is the week for use in the database
    if findindb(user.first_name, data['group'], weektext) is False:
        return context.bot.send_message(text="You have not yet submitted your free times for this week!", chat_id=update.effective_message.chat_id)
    if findindb(user.first_name, data['group'], weektext) is True:
        # if the slot for this person is not found in the db already, create a line in the db for it
        conn4 = psycopg2.connect(
                host='host',
                database='database',
                user='user',
                password='password',
        )
        c4 = conn4.cursor()
        c4.execute('''UPDATE freetime SET free_timeslots = (%s) WHERE (user_name, week, group_name) = (%s, %s, %s)''', (arraytotext(freetimeslots), username, weektext, data['group']))
        conn4.commit()
        conn4.close()

def end(update: Update, context: CallbackContext) -> int:
    """Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over.
    """
    query = update.callback_query
    query.answer()
    freeslotstext = arraytotext(freeslots)
    text = user.first_name + " is free on " + freeslotstext + "."
    context.bot.send_message(text=text, chat_id=update.effective_message.chat_id)
    addtodb(user.first_name, freeslots, context, update)
    query.edit_message_text(text="Thank you for filling in!")

    return ConversationHandler.END


def endedit(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    freeslotstext = arraytotext(freeslots)
    text = user.first_name + " is free on " + freeslotstext + "."
    context.bot.send_message(text=text, chat_id=update.effective_message.chat_id)
    editdb(user.first_name, freeslots, context, update)
    query.edit_message_text(text="Your input has been updated!")

    return ConversationHandler.END

def nextweekresult(update: Update, context: CallbackContext) -> int:
    """Send message on `/result`."""
    # Get user that sent /start and log his name
    if data['group'] == "":
        update.message.reply_text("Please /register to your group to proceed")
    else:
        mondaymorning = []
        mondayafternoon = []
        mondaynight = []
        tuesdaymorning = []
        tuesdayafternoon = []
        tuesdaynight = []
        wednesdaymorning = []
        wednesdayafternoon = []
        wednesdaynight = []
        thursdaymorning = []
        thursdayafternoon = []
        thursdaynight = []
        fridaymorning = []
        fridayafternoon = []
        fridaynight = []
        saturdaymorning = []
        saturdayafternoon = []
        saturdaynight = []
        sundaymorning = []
        sundayafternoon = []
        sundaynight = []


        months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
                  'November', 'December']
        # Sending this message on a sunday so must add one as the week planning timeslots for starts on monday
        # TODO program the msg to send every sunday
        dayofweek = datetime.today().weekday()
        daystonextmonday = 7 - dayofweek

        month = months[date.today().month - 1]
        num_daysinmonth = monthrange(2021, date.today().month)[1]
        if date.today().day + daystonextmonday > num_daysinmonth:
            spillovertonextmonth = num_daysinmonth - date.today().day + daystonextmonday
            dayofnextmonday = spillovertonextmonth
        else:
            dayofnextmonday = str(date.today().day + daystonextmonday)

        if int(dayofnextmonday) + 6 > num_daysinmonth:
            weeklater = str(int(dayofnextmonday) + 6 - num_daysinmonth)
        else:
            weeklater = str(int(dayofnextmonday) + 6)
        weektext = nameday(dayofnextmonday) + " to " + nameday(weeklater) + " " + month
        conn3 = psycopg2.connect(
                host='host',
                database='database',
                user='user',
                password='password',
        )
        c3 = conn3.cursor()
        c3.execute('''SELECT user_name, free_timeslots FROM FREETIME WHERE week = (%s) AND group_name = (%s)''', (weektext, data['group']))
        results = c3.fetchall()
        conn3.close()
        for row in results:
            name = row[0]
            freetimeslots = row[1]
            if "Monday Morning" in freetimeslots:
                mondaymorning.append(name)
            if "Monday Afternoon" in freetimeslots:
                mondayafternoon.append(name)
            if "Monday Night" in freetimeslots:
                mondaynight.append(name)
            if "Tuesday Morning" in freetimeslots:
                tuesdaymorning.append(name)
            if "Tuesday Afternoon" in freetimeslots:
                tuesdayafternoon.append(name)
            if "Tuesday Night" in freetimeslots:
                tuesdaynight.append(name)
            if "Wednesday Morning" in freetimeslots:
                wednesdaymorning.append(name)
            if "Wednesday Afternoon" in freetimeslots:
                wednesdayafternoon.append(name)
            if "Wednesday Night" in freetimeslots:
                wednesdaynight.append(name)
            if "Thursday Morning" in freetimeslots:
                thursdaymorning.append(name)
            if "Thursday Afternoon" in freetimeslots:
                thursdayafternoon.append(name)
            if "Thursday Night" in freetimeslots:
                thursdaynight.append(name)
            if "Friday Morning" in freetimeslots:
                fridaymorning.append(name)
            if "Friday Afternoon" in freetimeslots:
                fridayafternoon.append(name)
            if "Friday Night" in freetimeslots:
                fridaynight.append(name)
            if "Saturday Morning" in freetimeslots:
                saturdaymorning.append(name)
            if "Saturday Afternoon" in freetimeslots:
                saturdayafternoon.append(name)
            if "Saturday Night" in freetimeslots:
                saturdaynight.append(name)
            if "Sunday Morning" in freetimeslots:
                sundaymorning.append(name)
            if "Sunday Afternoon" in freetimeslots:
                sundayafternoon.append(name)
            if "Sunday Night" in freetimeslots:
                sundaynight.append(name)

        resulttext = """
        %s\n\n
        Monday Morning : %s \n
        Monday Afternoon : %s \n
        Monday Night : %s \n
        Tuesday Morning : %s \n
        Tuesday Afternoon : %s \n
        Tuesday Night : %s \n
        Wednesday Morning : %s \n
        Wednesday Afternoon : %s \n
        Wednesday Night : %s \n
        Thursday Morning : %s \n
        Thursday Afternoon : %s \n
        Thursday Night : %s \n
        Friday Morning : %s \n
        Friday Afternoon : %s \n
        Friday Night : %s \n
        Saturday Morning : %s \n
        Saturday Afternoon : %s \n
        Saturday Night : %s \n
        Sunday Morning : %s \n
        Sunday Afternoon : %s \n
        Sunday Night : %s"""

        update.message.reply_text(resulttext % (weektext, arraytotext(mondaymorning), arraytotext(mondayafternoon), arraytotext(mondaynight),
                                                arraytotext(tuesdaymorning), arraytotext(tuesdayafternoon),
                                                arraytotext(tuesdaynight), arraytotext(wednesdaymorning), arraytotext(wednesdayafternoon),
                                                arraytotext(wednesdaynight), arraytotext(thursdaymorning),
                                                arraytotext(thursdayafternoon), arraytotext(thursdaynight), arraytotext(fridaymorning),
                                                arraytotext(fridayafternoon), arraytotext(fridaynight),
                                                arraytotext(saturdaymorning), arraytotext(saturdayafternoon), arraytotext(saturdaynight),
                                                arraytotext(sundaymorning), arraytotext(sundayafternoon),
                                                arraytotext(sundaynight)))
        return FIRST


def thisweekresult(update: Update, context: CallbackContext) -> int:
    """Send message on `/result`."""
    # Get user that sent /start and log his name
    if data['group'] == "":
        update.message.reply_text("Please /register to your group to proceed")
    else:
        mondaymorning = []
        mondayafternoon = []
        mondaynight = []
        tuesdaymorning = []
        tuesdayafternoon = []
        tuesdaynight = []
        wednesdaymorning = []
        wednesdayafternoon = []
        wednesdaynight = []
        thursdaymorning = []
        thursdayafternoon = []
        thursdaynight = []
        fridaymorning = []
        fridayafternoon = []
        fridaynight = []
        saturdaymorning = []
        saturdayafternoon = []
        saturdaynight = []
        sundaymorning = []
        sundayafternoon = []
        sundaynight = []


        months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
                  'November', 'December']
        # Sending this message on a sunday so must add one as the week planning timeslots for starts on monday
        # TODO program the msg to send every sunday
        dayofweek = datetime.today().weekday()
        thismonday = dayofweek

        month = months[date.today().month - 1]
        num_daysinlastmonth = monthrange(2021, date.today().month-1)[1]
        if date.today().day - thismonday < 0:
            spillovertolastmonth = num_daysinlastmonth + date.today().day - thismonday
            dayofthismonday = str(spillovertolastmonth)
        else:
            dayofthismonday = str(date.today().day - thismonday)

        if int(dayofthismonday) + 6 > num_daysinlastmonth:
            weeklater = str(int(dayofthismonday) + 6 - num_daysinlastmonth)
        else:
            weeklater = str(int(dayofthismonday) + 6)
        weektext = nameday(dayofthismonday) + " to " + nameday(weeklater) + " " + month
        conn3 = psycopg2.connect(
                host='host',
                database='database',
                user='user',
                password='password',
        )
        c3 = conn3.cursor()
        c3.execute('''SELECT user_name, free_timeslots FROM FREETIME WHERE week = (%s) AND group_name = (%s)''', (weektext, data['group']))
        results = c3.fetchall()
        conn3.close()
        for row in results:
            name = row[0]
            freetimeslots = row[1]
            if "Monday Morning" in freetimeslots:
                mondaymorning.append(name)
            if "Monday Afternoon" in freetimeslots:
                mondayafternoon.append(name)
            if "Monday Night" in freetimeslots:
                mondaynight.append(name)
            if "Tuesday Morning" in freetimeslots:
                tuesdaymorning.append(name)
            if "Tuesday Afternoon" in freetimeslots:
                tuesdayafternoon.append(name)
            if "Tuesday Night" in freetimeslots:
                tuesdaynight.append(name)
            if "Wednesday Morning" in freetimeslots:
                wednesdaymorning.append(name)
            if "Wednesday Afternoon" in freetimeslots:
                wednesdayafternoon.append(name)
            if "Wednesday Night" in freetimeslots:
                wednesdaynight.append(name)
            if "Thursday Morning" in freetimeslots:
                thursdaymorning.append(name)
            if "Thursday Afternoon" in freetimeslots:
                thursdayafternoon.append(name)
            if "Thursday Night" in freetimeslots:
                thursdaynight.append(name)
            if "Friday Morning" in freetimeslots:
                fridaymorning.append(name)
            if "Friday Afternoon" in freetimeslots:
                fridayafternoon.append(name)
            if "Friday Night" in freetimeslots:
                fridaynight.append(name)
            if "Saturday Morning" in freetimeslots:
                saturdaymorning.append(name)
            if "Saturday Afternoon" in freetimeslots:
                saturdayafternoon.append(name)
            if "Saturday Night" in freetimeslots:
                saturdaynight.append(name)
            if "Sunday Morning" in freetimeslots:
                sundaymorning.append(name)
            if "Sunday Afternoon" in freetimeslots:
                sundayafternoon.append(name)
            if "Sunday Night" in freetimeslots:
                sundaynight.append(name)

        resulttext = """
        %s\n\n
        Monday Morning : %s \n
        Monday Afternoon : %s \n
        Monday Night : %s \n
        Tuesday Morning : %s \n
        Tuesday Afternoon : %s \n
        Tuesday Night : %s \n
        Wednesday Morning : %s \n
        Wednesday Afternoon : %s \n
        Wednesday Night : %s \n
        Thursday Morning : %s \n
        Thursday Afternoon : %s \n
        Thursday Night : %s \n
        Friday Morning : %s \n
        Friday Afternoon : %s \n
        Friday Night : %s \n
        Saturday Morning : %s \n
        Saturday Afternoon : %s \n
        Saturday Night : %s \n
        Sunday Morning : %s \n
        Sunday Afternoon : %s \n
        Sunday Night : %s"""

        update.message.reply_text(resulttext % (weektext, arraytotext(mondaymorning), arraytotext(mondayafternoon), arraytotext(mondaynight),
                                                arraytotext(tuesdaymorning), arraytotext(tuesdayafternoon),
                                                arraytotext(tuesdaynight), arraytotext(wednesdaymorning), arraytotext(wednesdayafternoon),
                                                arraytotext(wednesdaynight), arraytotext(thursdaymorning),
                                                arraytotext(thursdayafternoon), arraytotext(thursdaynight), arraytotext(fridaymorning),
                                                arraytotext(fridayafternoon), arraytotext(fridaynight),
                                                arraytotext(saturdaymorning), arraytotext(saturdayafternoon), arraytotext(saturdaynight),
                                                arraytotext(sundaymorning), arraytotext(sundayafternoon),
                                                arraytotext(sundaynight)))
        return FIRST

def mostpeople(number, most):
    if number > most:
        most = number
    else:
        most = most
    return most

# The command that will print the date in which most people in the group are free
def meet(update: Update, context: CallbackContext) -> int:
    """Send message on `/result`."""
    # Get user that sent /start and log his name
    if data['group'] == "":
        update.message.reply_text("Please /register to your group to proceed")

    else:

        mondaymorning = []
        mondayafternoon = []
        mondaynight = []
        tuesdaymorning = []
        tuesdayafternoon = []
        tuesdaynight = []
        wednesdaymorning = []
        wednesdayafternoon = []
        wednesdaynight = []
        thursdaymorning = []
        thursdayafternoon = []
        thursdaynight = []
        fridaymorning = []
        fridayafternoon = []
        fridaynight = []
        saturdaymorning = []
        saturdayafternoon = []
        saturdaynight = []
        sundaymorning = []
        sundayafternoon = []
        sundaynight = []


        months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
                  'November', 'December']
        # Sending this message on a sunday so must add one as the week planning timeslots for starts on monday
        dayofweek = datetime.today().weekday()
        daystonextmonday = 7 - dayofweek

        month = months[date.today().month - 1]
        num_daysinmonth = monthrange(2021, date.today().month)[1]
        if date.today().day + daystonextmonday > num_daysinmonth:
            spillovertonextmonth = num_daysinmonth - date.today().day + daystonextmonday
            dayofnextmonday = spillovertonextmonth
        else:
            dayofnextmonday = str(date.today().day + daystonextmonday)

        if int(dayofnextmonday) + 6 > num_daysinmonth:
            weeklater = str(int(dayofnextmonday) + 6 - num_daysinmonth)
        else:
            weeklater = str(int(dayofnextmonday) + 6)
        weektext = nameday(dayofnextmonday) + " to " + nameday(weeklater) + " " + month
        conn5 = psycopg2.connect(
                host='host',
                database='database',
                user='user',
                password='password',
        )
        c5 = conn5.cursor()
        c5.execute('''SELECT user_name, free_timeslots FROM FREETIME WHERE week = (%s) AND group_name = (%s)''', (weektext, data['group']))
        results = c5.fetchall()
        conn5.close()
        for row in results:
            name = row[0]
            freetimeslots = row[1]
            if "Monday Morning" in freetimeslots:
                mondaymorning.append(name)
            if "Monday Afternoon" in freetimeslots:
                mondayafternoon.append(name)
            if "Monday Night" in freetimeslots:
                mondaynight.append(name)
            if "Tuesday Morning" in freetimeslots:
                tuesdaymorning.append(name)
            if "Tuesday Afternoon" in freetimeslots:
                tuesdayafternoon.append(name)
            if "Tuesday Night" in freetimeslots:
                tuesdaynight.append(name)
            if "Wednesday Morning" in freetimeslots:
                wednesdaymorning.append(name)
            if "Wednesday Afternoon" in freetimeslots:
                wednesdayafternoon.append(name)
            if "Wednesday Night" in freetimeslots:
                wednesdaynight.append(name)
            if "Thursday Morning" in freetimeslots:
                thursdaymorning.append(name)
            if "Thursday Afternoon" in freetimeslots:
                thursdayafternoon.append(name)
            if "Thursday Night" in freetimeslots:
                thursdaynight.append(name)
            if "Friday Morning" in freetimeslots:
                fridaymorning.append(name)
            if "Friday Afternoon" in freetimeslots:
                fridayafternoon.append(name)
            if "Friday Night" in freetimeslots:
                fridaynight.append(name)
            if "Saturday Morning" in freetimeslots:
                saturdaymorning.append(name)
            if "Saturday Afternoon" in freetimeslots:
                saturdayafternoon.append(name)
            if "Saturday Night" in freetimeslots:
                saturdaynight.append(name)
            if "Sunday Morning" in freetimeslots:
                sundaymorning.append(name)
            if "Sunday Afternoon" in freetimeslots:
                sundayafternoon.append(name)
            if "Sunday Night" in freetimeslots:
                sundaynight.append(name)

        daywithmostpseople = mostpeople(len(sundaynight), mostpeople(len(sundayafternoon), mostpeople(len(sundaymorning),
                                        mostpeople(len(saturdaynight), mostpeople(len(saturdayafternoon), mostpeople(len(saturdaymorning),
                                        mostpeople(len(fridaynight), mostpeople(len(fridayafternoon), mostpeople(len(fridaymorning),
                                        mostpeople(len(thursdaynight), mostpeople(len(thursdayafternoon), mostpeople(len(thursdaymorning),
                                        mostpeople(len(wednesdaynight), mostpeople(len(wednesdayafternoon), mostpeople(len(wednesdaymorning),
                                        mostpeople(len(tuesdaynight), mostpeople(len(tuesdayafternoon), mostpeople(len(tuesdaymorning),
                                        mostpeople(len(mondaynight), mostpeople(len(mondayafternoon), mostpeople(len(mondaymorning), 0)))))))))))))))))))))
        logger.info(daywithmostpseople)
        dayswithmost = []
        if len(mondaymorning) == daywithmostpseople:
            dayswithmost.append("Monday Morning")
        if len(mondayafternoon) == daywithmostpseople:
            dayswithmost.append("Monday Afternoon")
        if len(mondaynight) == daywithmostpseople:
            dayswithmost.append("Monday Night")
        if len(tuesdaymorning) == daywithmostpseople:
            dayswithmost.append("Tuesday Morning")
        if len(tuesdayafternoon) == daywithmostpseople:
            dayswithmost.append("Tuesday Afternoon")
        if len(tuesdaynight) == daywithmostpseople:
            dayswithmost.append("Tuesday Night")
        if len(wednesdaymorning) == daywithmostpseople:
            dayswithmost.append("Wednesday Morning")
        if len(wednesdayafternoon) == daywithmostpseople:
            dayswithmost.append("Wednesday Afternoon")
        if len(wednesdaynight) == daywithmostpseople:
            dayswithmost.append("Wednesday Night")
        if len(thursdaymorning) == daywithmostpseople:
            dayswithmost.append("Thursday Morning")
        if len(thursdayafternoon) == daywithmostpseople:
            dayswithmost.append("Thursday Afternoon")
        if len(thursdaynight) == daywithmostpseople:
            dayswithmost.append("Thursday Night")
        if len(fridaymorning) == daywithmostpseople:
            dayswithmost.append("Friday Morning")
        if len(fridayafternoon) == daywithmostpseople:
            dayswithmost.append("Friday Afternoon")
        if len(fridaynight) == daywithmostpseople:
            dayswithmost.append("Friday Night")
        if len(saturdaymorning) == daywithmostpseople:
            dayswithmost.append("Saturday Morning")
        if len(saturdayafternoon) == daywithmostpseople:
            dayswithmost.append("Saturday Afternoon")
        if len(saturdaynight) == daywithmostpseople:
            dayswithmost.append("Saturday Night")
        if len(sundaymorning) == daywithmostpseople:
            dayswithmost.append("Sunday Morning")
        if len(sundayafternoon) == daywithmostpseople:
            dayswithmost.append("Sunday Afternoon")
        if len(sundaynight) == daywithmostpseople:
            dayswithmost.append("Sunday Night")

        mostdaystext = ""
        for u in dayswithmost:
            if mostdaystext == "":
                mostdaystext += u
            else:
                mostdaystext += ", " + u
        update.message.reply_text(f"Your group can have a meeting of {daywithmostpseople} members on {mostdaystext}")
        return FIRST

# Setup conversation handler with the states FIRST and SECOND
# Use the pattern parameter to pass CallbackQueries with specific
# data pattern to the corresponding handlers.
# ^ means "start of line/string"
# $ means "end of line/string"
# So ^ABC$ will only allow 'ABC'
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start),],
    states={
        FIRST: [
            CallbackQueryHandler(monday, pattern='^' + str(Monday) + '$'),
            CallbackQueryHandler(tuesday, pattern='^' + str(Tuesday) + '$'),
            CallbackQueryHandler(wednesday, pattern='^' + str(Wednesday) + '$'),
            CallbackQueryHandler(thursday, pattern='^' + str(Thursday) + '$'),
            CallbackQueryHandler(friday, pattern='^' + str(Friday) + '$'),
            CallbackQueryHandler(saturday, pattern='^' + str(Saturday) + '$'),
            CallbackQueryHandler(sunday, pattern='^' + str(Sunday) + '$'),

        ],
        SECOND: [
            CallbackQueryHandler(morning, pattern='^' + str(Morning) + '$'),
            CallbackQueryHandler(afternoon, pattern='^' + str(Afternoon) + '$'),
            CallbackQueryHandler(night, pattern='^' + str(Night) + '$'),

        ],
        THIRD: [
            CallbackQueryHandler(end, pattern='^' + str(Monday) + '$'),
            CallbackQueryHandler(start_over, pattern='^' + str(Tuesday) + '$'),
        ],
    },
    fallbacks=[CommandHandler('start', start)],
    )
conv_handler1 = ConversationHandler(
    entry_points=[CommandHandler('edit', edit), ],
    states={
        FIRST: [
            CallbackQueryHandler(monday, pattern='^' + str(Monday) + '$'),
            CallbackQueryHandler(tuesday, pattern='^' + str(Tuesday) + '$'),
            CallbackQueryHandler(wednesday, pattern='^' + str(Wednesday) + '$'),
            CallbackQueryHandler(thursday, pattern='^' + str(Thursday) + '$'),
            CallbackQueryHandler(friday, pattern='^' + str(Friday) + '$'),
            CallbackQueryHandler(saturday, pattern='^' + str(Saturday) + '$'),
            CallbackQueryHandler(sunday, pattern='^' + str(Sunday) + '$'),

        ],
        SECOND: [
            CallbackQueryHandler(morning, pattern='^' + str(Morning) + '$'),
            CallbackQueryHandler(afternoon, pattern='^' + str(Afternoon) + '$'),
            CallbackQueryHandler(night, pattern='^'     + str(Night) + '$'),

        ],
        THIRD: [
            CallbackQueryHandler(endedit, pattern='^' + str(Monday) + '$'),
            CallbackQueryHandler(start_over, pattern='^' + str(Tuesday) + '$'),
        ],
    },
    fallbacks=[CommandHandler('edit', edit)],
    )
conv_handler2 = ConversationHandler(
   entry_points=[CommandHandler('register', register)],
   states={
       GROUP: [
           CommandHandler('cancel', cancel),  # has to be before MessageHandler to catch `/cancel` as command, not as `title`
           MessageHandler(Filters.text, get_group)
       ],
       PASSWORD: [
           CommandHandler('cancel', cancel),  # has to be before MessageHandler to catch `/cancel` as command, not as `text`
           MessageHandler(Filters.text, get_grouppw)
       ],
   },
   fallbacks=[CommandHandler('cancel', cancel)]
)

# Add ConversationHandler to dispatcher that will be used for handling updates
dispatcher.add_handler(conv_handler)
dispatcher.add_handler(conv_handler1)
dispatcher.add_handler(conv_handler2)
dispatcher.add_handler(CommandHandler('nextweekresult', nextweekresult))
dispatcher.add_handler(CommandHandler('thisweekresult', thisweekresult))
dispatcher.add_handler(CommandHandler('meet', meet))


# Schedule the bot tho remind the user for input every sunday
# j = updater.job_queue
# j.run_daily(start, days=(6,), time=time(hour=14, minute=00, second=00))

# Start the Bot
# updater.start_polling()
# When hosting the bot 24/7, we must use webhooks instead of polling as webhooks alert the bot to return a reply
# whereas polling makes the bot query in regular intervals for input by user
updater.start_webhook(listen="0.0.0.0",
                      port=int(PORT),
                      url_path=API_KEY)
updater.bot.setWebhook('https://damp-brook-02881.herokuapp.com/' + API_KEY)

# Run the bot until you press Ctrl-C or the process receives SIGINT,
# SIGTERM or SIGABRT. This should be used most of the time, since
# start_polling() is non-blocking and will stop the bot gracefully.
updater.idle()


#https://towardsdatascience.com/how-to-deploy-a-telegram-bot-using-heroku-for-free-9436f89575d2 follow this to host on heroku
