import lightbulb
import firebase_admin
from firebase_admin import credentials, firestore
from config import *

cred = credentials.Certificate(firebase_config)
app = firebase_admin.initialize_app(cred)
db = firestore.client()

rev_ref = db.collection(u'reviews')
sub_ref = db.collection(u'subjects')

plugin = lightbulb.Plugin("Add Review")

# Get all subject codes from the database
def get_subjects():
    all_subjects = []
    for doc in sub_ref.stream():
        subject_dict = doc.to_dict()
        all_subjects.append(subject_dict["subjectCode"])
    return all_subjects

@plugin.command
@lightbulb.option("review", "Please write a review here.")
@lightbulb.option("recommended", "Would you recommend this subject?", choices=["Yes", "No"])
@lightbulb.option("difficulty", "Rate the difficulty of the subject on a scale of 1-10", int, choices=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
@lightbulb.option("teaching_quality", "Rate the teaching quality of the subject on a scale of 1-10", int, choices=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
@lightbulb.option("interesting", "How interesting is the subject on a scale of 1-10?",  int, choices=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
@lightbulb.option("year_taken", "This is the year you took the subject.", int)
@lightbulb.option("semester_taken", "This is the semester you took the subject.", choices=["Semester 1", "Semester 2", "Summer", "Winter", "Year-Long"])
@lightbulb.option("lecturer", "This is the name of the lecturer")
@lightbulb.option("major", "This is your major.")
@lightbulb.option("subject_type", "Is this a core subject?", choices=["Core", "Elective", "Breadth"])
@lightbulb.option("subject_code", "This is the subject code.")
@lightbulb.command("add_review", "Submit a subject review.")
@lightbulb.implements(lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:

    # Check if the subject code entered is valid
    if ctx.options.subject_code in get_subjects():
        review = {
            u'difficulty': ctx.options.difficulty,
            u'interesting': ctx.options.interesting,
            u'lecturer': ctx.options.lecturer,
            u'major': ctx.options.major,
            u'recommended': ctx.options.recommended,
            u'reviewText': ctx.options.review,
            u'semesterTaken': ctx.options.semester_taken,
            u'subjectCode': ctx.options.subject_code,
            u'subjectType': ctx.options.subject_type,
            u'teachingQuality': ctx.options.teaching_quality,
            u'userID': None,
            u'username': 'Discord User: ' + str(ctx.author),
            u'year': ctx.options.year_taken,
        }
        db.collection(u'reviews').add(review)
        await ctx.respond(
            "**Review Author:** " + str(ctx.author) + "\n" +
            "**Subject Code:** " + ctx.options.subject_code + "\n" +
            "**Subject Type:** " + ctx.options.subject_type + "\n" +
            "**Major:** " + ctx.options.major + "\n" +
            "**Lecturer(s):** " + ctx.options.lecturer + "\n" +
            "**Semester Taken:** " + ctx.options.semester_taken + "\n" +
            "**Year Taken:** " + str(ctx.options.year_taken) + "\n" +
            "**Difficulty: ** " + str(ctx.options.difficulty) + "\n" +
            "**Interesting:** " + str(ctx.options.interesting) + "\n" +
            "**Teaching Quality:** " + str(ctx.options.teaching_quality) + "\n" +
            "**Recommended?:** " + ctx.options.recommended + "\n" +
            "**Review:** " + ctx.options.review
        )
    else:
        await ctx.author.send("There was an error in your review submission. Please enter a **valid** subject code.")

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)