import os, re
import hikari, lightbulb
from firebase_admin import firestore
from config import *

db = firestore.client()

rev_ref = db.collection(u'reviews')

SUBJECT_REGEX = "Subject.*:.*\n"
MAJOR_REGEX = "My.*:.*\n"
LECTURER_REGEX = "Lecturer.*\n"
DIFFICULTY_REGEX = "Difficulty:.*\/"
INTERESTING_REGEX = "How fun\/interesting you found it:.*\/"
TEACHING_REGEX = "Teaching.*:.*\/"
WHEN_REGEX = "When I took the subject:.*\n"
REVIEW_REGEX = "Review[\S\s]*"
AUTHOR_REGEX = "User:.*\n"

SUBJECT_CODE_REGEX = "[A-Z]{4}[0-9]{5}"
SEMESTER_REGEX = "Semester [0-9]"
YEAR_REGEX = "[0-9]{4}"

plugin = lightbulb.Plugin("Push Old Reviews")
channel = int(os.environ.get("REVIEW_CHANNEL_ID"))

def extract_field(msg_line):
    return msg_line[0].split(":", 1)[1].strip()

def push_review(subject_code_v, major_v, lecturer_v, difficulty_v, interesting_v, teaching_v, year_v, semester_v, review_v, author):
    
    # Check for null values in each field
    if subject_code_v == [] or subject_code_v == "":
        subject_code_v == None
    if major_v == [] or major_v == "":
        major_v == None
    if lecturer_v == [] or lecturer_v == "":
        lecturer_v == None
    if difficulty_v == [] or difficulty_v == 0:
        difficulty_v == None
    if interesting_v == [] or interesting_v == 0:
        interesting_v == None
    if teaching_v == [] or teaching_v == 0:
        teaching_v == None
    if year_v == [] or year_v == 0:
        year_v == None
    if semester_v == [] or semester_v == "":
        semester_v == None
    if review_v == [] or review_v == "":
        review_v == None

    # Check for duplicate records in databse
    query = rev_ref.where(
        u'difficulty', u'==', int(difficulty_v)
    ).where(
        u'interesting', u'==', int(interesting_v)
    ).where(
        u'lecturer', u'==', lecturer_v
    ).where(
        u'major', u'==', major_v
    ).where(
        u'semesterTaken', u'==', semester_v
    ).where(
        u'subjectCode', u'==', subject_code_v
    ).where(
        u'teachingQuality', u'==', int(teaching_v)
    ).where(
        u'year', u'==', int(year_v)
    ).where(
        u'username', u'==', 'Discord User: ' + str(author)
    ).stream()
    docs = [d for d in query]
    if len(docs) != 0:
        return
    
    # Push the review to the database
    db_review = {
        u'difficulty': int(difficulty_v),
        u'interesting': int(interesting_v),
        u'lecturer': lecturer_v,
        u'major': major_v,
        u'recommended': None,
        u'reviewText': review_v,
        u'semesterTaken': semester_v,
        u'subjectCode': subject_code_v,
        u'subjectType': None,
        u'teachingQuality': int(teaching_v),
        u'userID': None,
        u'username': 'Discord User: ' + str(author),
        u'year': int(year_v),
    }
    db.collection(u'reviews').add(db_review)    


@plugin.command
@lightbulb.command("push_old_reviews", "Push all old reviews")
@lightbulb.implements(lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:

    # Fetch all old messages
    history = ctx.app.rest.fetch_messages(channel)
    num_messages = 0
    messages = []
    async for msg in history:
         num_messages += 1
         messages.append(msg.content + "\n User: " + str(msg.author) + "\n")
    messages.reverse()
    messages = list(filter(None, messages))

    # Iterate through every message
    curr_msg = 1
    author = ""
    subject_code_v = ""
    major_v = ""
    lecturer_v = ""
    difficulty_v = 0
    interesting_v = 0
    teaching_v = 0
    semester_v = ""
    year_v = 0
    review_v = ""
    for msg in messages:
        msg = msg.replace("**", "")
        if msg.startswith("Subject"):

            if curr_msg == num_messages:
                push_review(subject_code_v, major_v, lecturer_v, difficulty_v, interesting_v, teaching_v, year_v, semester_v, review_v, author)
                return
            
            # Push previous review to database
            if curr_msg != 1:
                push_review(subject_code_v, major_v, lecturer_v, difficulty_v, interesting_v, teaching_v, year_v, semester_v, review_v, author)
        
            # Refresh buffers
            subject_code_v = ""
            major_v = ""
            lecturer_v = ""
            difficulty_v = 0
            interesting_v = 0
            teaching_v = 0
            semester_v = ""
            year_v = 0
            review_v = ""
            author = ""

            # Find author
            author = re.findall(AUTHOR_REGEX, msg)
            if author != []:
                author = extract_field(author)
            msg = msg.replace("\n User: " + str(author) + "\n", "")

            # Find subject code
            subject = re.findall(SUBJECT_REGEX, msg)[0]
            if subject != []:
                subject_code_v = re.findall(SUBJECT_CODE_REGEX, subject)
                if subject_code_v != []:
                    subject_code_v = subject_code_v[0]


            # Find major
            major_v = re.findall(MAJOR_REGEX, msg)
            if major_v != []:
                major_v = extract_field(major_v)

            # Find lecturer(s)
            lecturer_v = re.findall(LECTURER_REGEX, msg)
            if lecturer_v != []:
                lecturer_v = extract_field(lecturer_v)

            # Find difficulty rating
            difficulty_v = re.findall(DIFFICULTY_REGEX, msg)
            if difficulty_v != []:
                difficulty_v = float(extract_field(difficulty_v)[:-1])

            # Find interesting rating
            interesting_v = re.findall(INTERESTING_REGEX, msg)
            if interesting_v != []:
                interesting_v = float(extract_field(interesting_v)[:-1])

            # Find teaching quality rating
            teaching_v = re.findall(TEACHING_REGEX, msg)
            if teaching_v != []:
                teaching_v = float(extract_field(teaching_v)[:-1])

            # Find semester
            when = re.findall(WHEN_REGEX, msg)
            if when != []:
                semester_v = re.findall(SEMESTER_REGEX, when[0])[0]

            # Find year
            if when != []:
                year_v = re.findall(YEAR_REGEX, when[0])[0]

            # Find review
            review_v = re.findall(REVIEW_REGEX, msg)
            if review_v != []:
                review_v = extract_field(review_v)
        
        elif curr_msg == num_messages:
            msg = msg.replace("\n User: " + str(author) + "\n", "")
            review_v += "\n" + msg
            push_review(subject_code_v, major_v, lecturer_v, difficulty_v, interesting_v, teaching_v, year_v, semester_v, review_v, author)

        else:
            msg = msg.replace("\n User: " + str(author) + "\n", "")
            review_v += "\n" + msg

        curr_msg += 1

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)