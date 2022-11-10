import os, re
import hikari, lightbulb
from firebase_admin import firestore
from config import *

db = firestore.client()

rev_ref = db.collection(u'reviews')
sub_ref = db.collection(u'subjects')

SUBJECT_CODE_REGEX = "Subject Code:.*\n"
SUBJECT_TYPE_REGEX = "Subject Type:.*\n"
MAJOR_REGEX = "Major:.*\n"
LECTURER_REGEX = "Lecturer.*\n"
SEMESTER_REGEX = "Semester.*\n"
YEAR_REGEX = "Year.*\n"
DIFFICULTY_REGEX = "Difficulty:.*\n"
INTERESTING_REGEX = "Interesting:.*\n"
TEACHING_REGEX = "Teaching Quality:.*\n"
RECOMMENDED_REGEX = "Recommended\\?:.*\n"
REVIEW_REGEX = "Review:.*"

SUBJECT_CODE = "Subject Code:"
SUBJECT_TYPE = "Subject Type:"
MAJOR = "Major:"
LECTURER = "Lecturer"
SEMESTER = "Semester"
YEAR = "Year"
DIFFICULTY = "Difficulty:"
INTERESTING = "Interesting:"
TEACHING = "Teaching Quality:"
RECOMMENDED = "Recommended?:"
REVIEW = "Review:"

EMPTY_FIELD = ""

SUBJECT_TYPE_CHOICES = ["Core", "Elective", "Breadth"]
SEMESTER_CHOICES = ["Semester 1", "Semester 2", "Summer", "Winter", "Year-Long"]
RECOMMENDED_CHOICES = ["Yes", "No"]
MIN_RATING = 1
MAX_RATING = 10


plugin = lightbulb.Plugin("Add Review Message")

def extract_field(msg_line):
    return msg_line[0].split(":")[1].strip()

# Get all subject codes from the database
def get_subjects():
    all_subjects = []
    for doc in sub_ref.stream():
        subject_dict = doc.to_dict()
        all_subjects.append(subject_dict["subjectCode"])
    return all_subjects

@plugin.listener(hikari.GuildMessageCreateEvent)
async def add_review_message(event: hikari.GuildMessageCreateEvent) -> None:

    if event.channel_id == int(os.environ.get("REVIEW_CHANNEL_ID")):

        # Remove all occurences of **
        review_message = event.content
        review_message = review_message.replace("**","")

        # Find the subject code
        subject_code = re.findall(SUBJECT_CODE_REGEX, review_message)
        if SUBJECT_CODE not in review_message:
            await event.author.send("There was an error in your review submission. Please enter a subject code.")
            await event.message.delete()
            return
        subject_code_v = extract_field(subject_code) 
        if subject_code_v == EMPTY_FIELD:
            await event.author.send("There was an error in your review submission. Please enter a subject code.")
            await event.message.delete()
            return
        if subject_code_v not in get_subjects():
            await event.author.send("There was an error in your review submission. Please enter a **valid** subject code.")
            await event.message.delete()
            return

        # Find the subject type
        subject_type = re.findall(SUBJECT_TYPE_REGEX, review_message)
        if SUBJECT_TYPE not in review_message:
            await event.author.send("There was an error in your review submission. Please enter a subject type.")
            await event.message.delete()
            return
        subject_type_v = extract_field(subject_type)
        if subject_type_v == EMPTY_FIELD:
            await event.author.send("There was an error in your review submission. Please enter a subject type.")
            await event.message.delete()
            return
        if subject_type_v not in SUBJECT_TYPE_CHOICES:
            await event.author.send("There was an error in your review submission. Please enter a subject type:\n- **Core**\n- **Elective**\n- **Breadth**")
            await event.message.delete()
            return
        
        # Find the major
        major = re.findall(MAJOR_REGEX, review_message)
        if MAJOR not in review_message:
            await event.author.send("There was an error in your review submission. Please enter a major.")
            await event.message.delete()
            return
        major_v = extract_field(major)
        if major_v == EMPTY_FIELD:
            await event.author.send("There was an error in your review submission. Please enter a major.")
            await event.message.delete()
            return

        # Find the lecturer(s)
        lecturer = re.findall(LECTURER_REGEX, review_message)
        if LECTURER not in review_message:
            await event.author.send("There was an error in your review submission. Please enter a lecturer.")
            await event.message.delete()
            return
        lecturer_v = extract_field(lecturer)
        if lecturer_v == EMPTY_FIELD:
            await event.author.send("There was an error in your review submission. Please enter a lecturer.")
            await event.message.delete()
            return

        # Find the semester
        semester = re.findall(SEMESTER_REGEX, review_message)
        if SEMESTER not in review_message:
            await event.author.send("There was an error in your review submission. Please enter a semester.")
            await event.message.delete()
            return
        semester_v = extract_field(semester)
        if semester_v == EMPTY_FIELD:
            await event.author.send("There was an error in your review submission. Please enter a semester.")
            await event.message.delete()
            return
        if semester_v not in SEMESTER_CHOICES:
            await event.author.send("There was an error in your review submission. Please enter a valid semester:\n- **Semester 1**\n- **Semester 2**\n- **Summer**\n- **Winter**\n- **Year-Long**")
            await event.message.delete()
            return

        # Find the year
        year = re.findall(YEAR_REGEX, review_message)
        if YEAR not in review_message:
            await event.author.send("There was an error in your review submission. Please enter a year.")
            await event.message.delete()
            return
        year_v = extract_field(year)
        if year_v == EMPTY_FIELD:
            await event.author.send("There was an error in your review submission. Please enter a year.")
            await event.message.delete()
            return
        if not year_v.isdigit():
            await event.author.send("There was an error in your review submission. Please enter a **valid** year.")
            await event.message.delete()
            return

        # Find the difficulty
        difficulty = re.findall(DIFFICULTY_REGEX, review_message)
        if DIFFICULTY not in review_message:
            await event.author.send("There was an error in your review submission. Please enter a difficulty.")
            await event.message.delete()
            return
        difficulty_v = extract_field(difficulty)
        if difficulty_v == EMPTY_FIELD:
            await event.author.send("There was an error in your review submission. Please enter a difficulty.")
            await event.message.delete()
            return
        if not difficulty_v.isdigit():
            await event.author.send("There was an error in your review submission. Please enter an integer between 1 and 10 for the difficulty rating.")
            await event.message.delete()
            return
        if int(difficulty_v) < MIN_RATING or int(difficulty_v) > MAX_RATING:
            await event.author.send("There was an error in your review submission. Please enter an integer between 1 and 10 for the difficulty rating.")
            await event.message.delete()
            return
    
        # Find the 'interesting' rating
        interesting = re.findall(INTERESTING_REGEX, review_message)
        if INTERESTING not in review_message:
            await event.author.send("There was an error in your review submission. Please enter a rating for 'Interesting'.")
            await event.message.delete()
            return
        interesting_v = extract_field(interesting)
        if interesting_v == EMPTY_FIELD:
            await event.author.send("There was an error in your review submission. Please enter a rating for 'Interesting'.")
            await event.message.delete()
            return
        if not interesting_v.isdigit():
            await event.author.send("There was an error in your review submission. Please enter an integer between 1 and 10 for the 'interesting' rating.")
            await event.message.delete()
            return
        if int(interesting_v) < MIN_RATING or int(interesting_v) > MAX_RATING:
            await event.author.send("There was an error in your review submission. Please enter an integer between 1 and 10 for the 'interesting' rating.")
            await event.message.delete()
            return
        
        
        # Find the teaching quality rating
        teaching = re.findall(TEACHING_REGEX, review_message)
        if TEACHING not in review_message:
            await event.author.send("There was an error in your review submission. Please enter a rating for the teaching quality.")
            await event.message.delete()
            return
        teaching_v = extract_field(teaching)
        if teaching_v == EMPTY_FIELD:
            await event.author.send("There was an error in your review submission. Please enter a rating for the teaching quality.")
            await event.message.delete()
            return
        if not teaching_v.isdigit():
            await event.author.send("There was an error in your review submission. Please enter an integer between 1 and 10 for the teaching quality rating.")
            await event.message.delete()
            return
        if int(teaching_v) < MIN_RATING or int(teaching_v) > MAX_RATING:
            await event.author.send("There was an error in your review submission. Please enter an integer between 1 and 10 for the teaching quality rating.")
            await event.message.delete()
            return
        
        # Find whether the subject is recommneded
        recommended = re.findall(RECOMMENDED_REGEX, review_message)
        if RECOMMENDED not in review_message:
            await event.author.send("There was an error in your review submission. Please state whether or not you would recommend this subject.")
            await event.message.delete()
            return
        recommended_v = extract_field(recommended)
        if recommended_v == EMPTY_FIELD:
            await event.author.send("There was an error in your review submission. Please state whether or not you would recommend this subject.")
            await event.message.delete()
            return
        if recommended_v not in RECOMMENDED_CHOICES:
            await event.author.send("There was an error in your review submission. Please select between the following options when recommending a subject:\n- **Yes**\n- **No**")
            await event.message.delete()
            return

        # Find the review
        review = re.findall(REVIEW_REGEX, review_message)
        if REVIEW not in review_message:
            await event.author.send("There was an error in your review submission. Please enter a review.")
            await event.message.delete()
            return
        review_v = extract_field(review)
        if review_v == EMPTY_FIELD:
            await event.author.send("There was an error in your review submission. Please enter a review.")
            await event.message.delete()
            return

        # Add review to database
        db_review = {
                u'difficulty': int(difficulty_v),
                u'interesting': int(interesting_v),
                u'lecturer': lecturer_v,
                u'major': major_v,
                u'recommended': recommended_v,
                u'reviewText': review_v,
                u'semesterTaken': semester_v,
                u'subjectCode': subject_code_v,
                u'subjectType': subject_type_v,
                u'teachingQuality': int(teaching_v),
                u'userID': None,
                u'username': 'Discord User: ' + str(event.author),
                u'year': int(year_v),
            }
        db.collection(u'reviews').add(db_review)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)