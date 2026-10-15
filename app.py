
import os
import re
import hmac
import json
import uuid
import hashlib
import sqlite3
from datetime import datetime, date
from pathlib import Path

import streamlit as st

# Configure application paths.
APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
UPLOAD_DIR = APP_DIR / "uploads"
DB_PATH = DATA_DIR / "sakhicycle.db"
DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)

# Configure the Streamlit page.
st.set_page_config(page_title="SakhiCycle", page_icon="🌸", layout="wide")

# Define interface translations.
I18N = {
    "English": {
        "home": "Home", "learn": "Learn", "quiz": "Knowledge quiz",
        "ask": "Ask anonymously", "track": "Check my question",
        "faq": "FAQs", "reminders": "Reminders", "admin": "Staff portal",
        "welcome": "Your trusted space to learn, ask and grow.",
        "subtitle": "Menstrual health education, without stigma.",
        "start_learning": "Start learning", "take_quiz": "Take a quiz",
        "ask_question": "Ask a question", "language": "Language",
        "privacy_text": "You can submit a question without creating an account. Avoid sharing names, addresses, school details or other identifying information.",
        "submit": "Submit question", "question": "Your question",
        "topic": "Topic", "age": "Age group (optional)",
        "attachment": "Optional image attachment",
        "consent": "I understand this is educational support and not a diagnosis or emergency service.",
        "ticket": "Your private tracking code",
        "ticket_help": "Save this code. It is needed to check the reply later.",
        "ticket_input": "Enter your tracking code", "check": "Check status",
        "no_question": "No question was found for that code.",
        "status": "Status", "reply": "Verified response",
        "login": "Staff login", "username": "Username", "password": "Password",
        "sign_in": "Sign in", "logout": "Log out",
        "queue": "Question moderation queue", "publish": "Publish response",
        "response": "Response", "lessons": "Learning modules",
        "not_medical": "This app provides general education, not individual diagnosis. For severe pain, very heavy bleeding, fainting, fever or urgent concerns, seek help from a qualified healthcare professional or local emergency service."
    },
    "हिन्दी": {
        "home": "होम", "learn": "सीखें", "quiz": "ज्ञान प्रश्नोत्तरी",
        "ask": "गुमनाम प्रश्न पूछें", "track": "अपने प्रश्न का उत्तर देखें",
        "faq": "सामान्य प्रश्न", "reminders": "रिमाइंडर", "admin": "स्टाफ पोर्टल",
        "welcome": "सीखने, पूछने और आगे बढ़ने के लिए आपका भरोसेमंद स्थान।",
        "subtitle": "बिना झिझक मासिक धर्म स्वास्थ्य की जानकारी।",
        "start_learning": "सीखना शुरू करें", "take_quiz": "प्रश्नोत्तरी लें",
        "ask_question": "प्रश्न पूछें", "language": "भाषा",
        "privacy_text": "आप बिना खाता बनाए प्रश्न पूछ सकती हैं। नाम, पता, स्कूल या पहचान बताने वाली जानकारी न दें।",
        "submit": "प्रश्न भेजें", "question": "आपका प्रश्न", "topic": "विषय",
        "age": "आयु वर्ग (वैकल्पिक)", "attachment": "वैकल्पिक चित्र",
        "consent": "मैं समझती हूँ कि यह शैक्षिक सहायता है, निदान या आपातकालीन सेवा नहीं।",
        "ticket": "आपका निजी ट्रैकिंग कोड",
        "ticket_help": "इस कोड को सुरक्षित रखें। उत्तर देखने के लिए इसकी आवश्यकता होगी।",
        "ticket_input": "ट्रैकिंग कोड दर्ज करें", "check": "स्थिति देखें",
        "no_question": "इस कोड के लिए कोई प्रश्न नहीं मिला।", "status": "स्थिति",
        "reply": "सत्यापित उत्तर", "login": "स्टाफ लॉगिन", "username": "यूज़रनेम",
        "password": "पासवर्ड", "sign_in": "लॉगिन करें", "logout": "लॉगआउट",
        "queue": "प्रश्न समीक्षा सूची", "publish": "उत्तर प्रकाशित करें",
        "response": "उत्तर", "lessons": "सीखने के मॉड्यूल",
        "not_medical": "यह ऐप सामान्य शैक्षिक जानकारी देता है, व्यक्तिगत निदान नहीं। गंभीर लक्षण होने पर योग्य स्वास्थ्यकर्मी से संपर्क करें।"
    },
    "ગુજરાતી": {
        "home": "હોમ", "learn": "શીખો", "quiz": "જ્ઞાન ક્વિઝ",
        "ask": "અનામિક પ્રશ્ન પૂછો", "track": "મારા પ્રશ્નનો જવાબ જુઓ",
        "faq": "સામાન્ય પ્રશ્નો", "reminders": "રિમાઇન્ડર્સ", "admin": "સ્ટાફ પોર્ટલ",
        "welcome": "શીખવા, પૂછવા અને આગળ વધવા માટે વિશ્વાસપૂર્ણ જગ્યા.",
        "subtitle": "સંકોચ વિના માસિક સ્વાસ્થ્યની માહિતી.",
        "start_learning": "શીખવાનું શરૂ કરો", "take_quiz": "ક્વિઝ લો",
        "ask_question": "પ્રશ્ન પૂછો", "language": "ભાષા",
        "privacy_text": "તમે ખાતું બનાવ્યા વિના પ્રશ્ન મોકલી શકો છો. નામ, સરનામું, શાળાની વિગતો અથવા ઓળખ આપતી માહિતી ન આપો.",
        "submit": "પ્રશ્ન મોકલો", "question": "તમારો પ્રશ્ન", "topic": "વિષય",
        "age": "ઉંમર જૂથ (વૈકલ્પિક)", "attachment": "વૈકલ્પિક છબી",
        "consent": "હું સમજું છું કે આ શૈક્ષણિક સહાય છે, નિદાન અથવા કટોકટી સેવા નથી.",
        "ticket": "તમારો ખાનગી ટ્રેકિંગ કોડ",
        "ticket_help": "આ કોડ સાચવી રાખો. જવાબ જોવા માટે તેની જરૂર પડશે.",
        "ticket_input": "ટ્રેકિંગ કોડ દાખલ કરો", "check": "સ્થિતિ જુઓ",
        "no_question": "આ કોડ માટે કોઈ પ્રશ્ન મળ્યો નથી.", "status": "સ્થિતિ",
        "reply": "ચકાસાયેલ જવાબ", "login": "સ્ટાફ લૉગિન", "username": "યૂઝરનેમ",
        "password": "પાસવર્ડ", "sign_in": "લૉગિન", "logout": "લૉગઆઉટ",
        "queue": "પ્રશ્ન સમીક્ષા યાદી", "publish": "જવાબ પ્રકાશિત કરો",
        "response": "જવાબ", "lessons": "શીખવાના મોડ્યુલ",
        "not_medical": "આ એપ સામાન્ય શૈક્ષણિક માહિતી આપે છે, વ્યક્તિગત નિદાન નહીં. ગંભીર લક્ષણો હોય તો યોગ્ય આરોગ્ય નિષ્ણાતનો સંપર્ક કરો."
    }
}

# Define educational learning modules.
LESSONS = [
    {
        "id": "cycle",
        "title": "Understanding the menstrual cycle",
        "topic": "Basics",
        "minutes": 5,
        "body": "The menstrual cycle is a natural process influenced by hormones. Cycle length and bleeding can vary, especially during the first few years after periods begin. Tracking dates can help you understand your own pattern. A period is not dirty, and bathing during menstruation is generally safe.",
        "points": [
            "A cycle is counted from the first day of one period to the first day of the next.",
            "Persistent or worrying changes deserve professional advice.",
            "Menstruation is a normal body function."
        ]
    },
    {
        "id": "products",
        "title": "Choosing and using menstrual products",
        "topic": "Products",
        "minutes": 4,
        "body": "Pads, tampons, menstrual cups and period underwear are options. Comfort, access to clean water and personal preference matter. Follow product instructions, change products regularly and wash your hands before and after changing.",
        "points": [
            "Choose a product that is comfortable and suitable for your needs.",
            "Wash your hands before and after changing products.",
            "Do not share reusable menstrual products."
        ]
    },
    {
        "id": "hygiene",
        "title": "Everyday menstrual hygiene",
        "topic": "Hygiene",
        "minutes": 4,
        "body": "Wash the external genital area gently with clean water. Avoid scented products and internal washing, which can cause irritation. Wash reusable products according to their instructions and dry them completely in a clean place.",
        "points": [
            "Internal washing is not needed.",
            "Clean hands and products help maintain hygiene.",
            "Seek medical advice for persistent itching or unusual discharge."
        ]
    },
    {
        "id": "myths",
        "title": "Myths versus facts",
        "topic": "Confidence",
        "minutes": 3,
        "body": "Menstruation is not a disease and does not make someone impure. People can usually exercise, bathe, study and participate in normal activities during a period, depending on comfort and health.",
        "points": [
            "Periods are a normal biological process.",
            "Bathing during menstruation is generally safe.",
            "Pain that disrupts daily life should not be ignored."
        ]
    },
    {
        "id": "disposal",
        "title": "Safe disposal and sustainability",
        "topic": "Environment",
        "minutes": 3,
        "body": "Wrap used disposable products and place them in an appropriate covered waste bin. Do not flush pads, wrappers or tampons down toilets. Follow local waste-management guidance.",
        "points": [
            "Never flush menstrual products down a toilet.",
            "Follow local disposal guidance.",
            "Clean reusable products as directed."
        ]
    },
    {
        "id": "when-help",
        "title": "When to seek trusted help",
        "topic": "Support",
        "minutes": 4,
        "body": "Speak with a qualified healthcare professional if periods repeatedly prevent normal activities, bleeding is unusually heavy, pain is severe, or you have concerns about your health. Seek urgent care for fainting, severe sudden pain or heavy bleeding with weakness.",
        "points": [
            "You deserve respectful care.",
            "Record symptoms and dates if helpful.",
            "This app cannot diagnose conditions."
        ]
    }
]

# Define quiz questions.
QUIZ = [
    {
        "q": "Which day is used as day one of a menstrual cycle?",
        "options": ["The last day of bleeding", "The first day of bleeding", "The middle of the month", "Any day you choose"],
        "answer": 1,
        "why": "Cycle day one is the first day of menstrual bleeding."
    },
    {
        "q": "Which is a good hygiene practice?",
        "options": ["Never wash during a period", "Wash hands before and after changing products", "Use scented products internally", "Share reusable products"],
        "answer": 1,
        "why": "Handwashing helps maintain hygiene."
    },
    {
        "q": "What should you do with a used disposable pad?",
        "options": ["Flush it", "Leave it in an open area", "Wrap it and put it in an appropriate bin", "Reuse it without cleaning"],
        "answer": 2,
        "why": "Wrap used products and use an appropriate waste bin."
    },
    {
        "q": "Which statement is accurate?",
        "options": ["Periods make someone impure", "Everyone has exactly the same cycle", "Bathing during a period is unsafe", "Menstruation is a normal body process"],
        "answer": 3,
        "why": "Menstruation is a normal biological process."
    },
    {
        "q": "If pain repeatedly stops daily activities, what is sensible?",
        "options": ["Ignore it forever", "Seek advice from a qualified healthcare professional", "Take any medicine a friend suggests", "Stop attending school"],
        "answer": 1,
        "why": "A clinician can assess disruptive pain and recommend suitable care."
    }
]

# Define frequently asked questions.
FAQS = [
    ("Is it okay to bathe during a period?", "Yes. Bathing and washing your hair during menstruation are generally safe."),
    ("Are irregular periods always a problem?", "Some variation can be common. Persistent or worrying changes should be discussed with a qualified healthcare professional."),
    ("Can I exercise during menstruation?", "Usually yes, if you feel comfortable. Rest when needed."),
    ("Does this app diagnose health conditions?", "No. SakhiCycle provides general education and is not a substitute for individual medical care.")
]

# Open a database connection.
def connect():
    connection = sqlite3.connect(DB_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection

# Create required database tables.
def init_db():
    with connect() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id TEXT PRIMARY KEY,
                ticket_hash TEXT NOT NULL,
                topic TEXT NOT NULL,
                age_group TEXT,
                language TEXT NOT NULL,
                question TEXT NOT NULL,
                attachment_path TEXT,
                status TEXT NOT NULL DEFAULT 'Pending',
                response TEXT,
                reviewer TEXT,
                created_at TEXT NOT NULL,
                answered_at TEXT
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                due_date TEXT NOT NULL,
                note TEXT,
                created_at TEXT NOT NULL
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                item_id TEXT,
                created_at TEXT NOT NULL
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS content (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                language TEXT NOT NULL DEFAULT 'English',
                active INTEGER NOT NULL DEFAULT 1,
                updated_at TEXT NOT NULL
            )
        """)
        count = connection.execute("SELECT COUNT(*) FROM content").fetchone()[0]
        if count == 0:
            now = datetime.utcnow().isoformat(timespec="seconds")
            for index, (title, body) in enumerate(FAQS, 1):
                connection.execute(
                    "INSERT INTO content VALUES (?, 'faq', ?, ?, 'English', 1, ?)",
                    (f"faq-{index}", title, body, now)
                )

# Return translated text.
def t(key):
    language = st.session_state.get("language", "English")
    return I18N.get(language, I18N["English"]).get(key, I18N["English"].get(key, key))

# Write an audit entry.
def log_action(actor, action, item_id=None):
    with connect() as connection:
        connection.execute(
            "INSERT INTO audit_log(actor, action, item_id, created_at) VALUES (?, ?, ?, ?)",
            (actor, action, item_id, datetime.utcnow().isoformat(timespec="seconds"))
        )

# Change pages through one shared navigation state.
def navigate(page):
    st.session_state.page = page
    st.rerun()

# Render the home page.
def render_home():
    st.title("🌸 SakhiCycle")
    st.subheader(t("welcome"))
    st.write(t("subtitle"))
    st.info(t("privacy_text"))

    first, second, third = st.columns(3)

    with first:
        st.metric("Learning modules", len(LESSONS))
        st.button(
            t("start_learning"),
            key="home_learn",
            use_container_width=True,
            on_click=navigate,
            args=("Learn",)
        )

    with second:
        st.metric("Quick knowledge check", f"{len(QUIZ)} questions")
        st.button(
            t("take_quiz"),
            key="home_quiz",
            use_container_width=True,
            on_click=navigate,
            args=("Knowledge quiz",)
        )

    with third:
        st.metric("Languages", "English · हिन्दी · ગુજરાતી")
        st.button(
            t("ask_question"),
            key="home_ask",
            use_container_width=True,
            on_click=navigate,
            args=("Ask anonymously",)
        )

    st.markdown("### Explore SakhiCycle")
    first_column, second_column = st.columns(2)

    with first_column:
        with st.container(border=True):
            st.markdown("#### 📘 Learn")
            st.write("Explore lessons on periods, menstrual products, hygiene and disposal.")
            st.button("Explore lessons", key="card_learn", use_container_width=True, on_click=navigate, args=("Learn",))
        with st.container(border=True):
            st.markdown("#### 🕊️ Anonymous support")
            st.write("Send a question without creating a personal account.")
            st.button("Ask anonymously", key="card_ask", use_container_width=True, on_click=navigate, args=("Ask anonymously",))

    with second_column:
        with st.container(border=True):
            st.markdown("#### 🧠 Quiz")
            st.write("Check what you know and learn from answer explanations.")
            st.button("Start quiz", key="card_quiz", use_container_width=True, on_click=navigate, args=("Knowledge quiz",))
        with st.container(border=True):
            st.markdown("#### 🔔 Reminders")
            st.write("Create reminders for product supplies or self-care.")
            st.button("Manage reminders", key="card_reminders", use_container_width=True, on_click=navigate, args=("Reminders",))

    st.warning(t("not_medical"))

# Render learning modules.
def render_learn():
    st.title("📘 " + t("lessons"))
    search = st.text_input("Search lessons")
    topics = sorted({lesson["topic"] for lesson in LESSONS})
    selected_topic = st.selectbox("Filter by topic", ["All"] + topics)

    filtered = [
        lesson for lesson in LESSONS
        if (selected_topic == "All" or lesson["topic"] == selected_topic)
        and search.lower() in (lesson["title"] + " " + lesson["body"]).lower()
    ]

    if not filtered:
        st.info("No lessons match your search.")

    for lesson in filtered:
        with st.container(border=True):
            st.markdown(f"### {lesson['title']}")
            st.caption(f"{lesson['topic']} · {lesson['minutes']} minutes")
            st.write(lesson["body"])
            with st.expander("Key learning points"):
                for point in lesson["points"]:
                    st.markdown(f"- {point}")

# Render the interactive quiz.
def render_quiz():
    st.title("🧠 " + t("quiz"))
    st.write("Choose an answer for each question and submit the quiz.")

    with st.form("quiz_form"):
        answers = []
        for index, item in enumerate(QUIZ):
            st.markdown(f"**{index + 1}. {item['q']}**")
            answer = st.radio(
                "Choose one answer",
                item["options"],
                key=f"quiz_answer_{index}",
                index=None,
                label_visibility="collapsed"
            )
            answers.append(answer)
        submitted = st.form_submit_button("Submit quiz", type="primary", use_container_width=True)

    if submitted:
        if any(answer is None for answer in answers):
            st.warning("Please answer every question before submitting.")
        else:
            score = sum(
                answer == item["options"][item["answer"]]
                for item, answer in zip(QUIZ, answers)
            )
            st.session_state.quiz_result = {
                "score": score,
                "answers": answers
            }

    if "quiz_result" in st.session_state:
        result = st.session_state.quiz_result
        score = result["score"]
        st.subheader(f"Your score: {score}/{len(QUIZ)}")
        st.progress(score / len(QUIZ))

        for index, item in enumerate(QUIZ):
            correct_answer = item["options"][item["answer"]]
            chosen_answer = result["answers"][index]
            if chosen_answer == correct_answer:
                st.success(f"Question {index + 1}: Correct")
            else:
                st.info(f"Question {index + 1}: Review this answer")
            st.write(f"Correct answer: {correct_answer}")
            st.caption(item["why"])

        if st.button("Try the quiz again", key="retry_quiz"):
            del st.session_state.quiz_result
            st.rerun()

# Save and validate an optional image.
def save_image(uploaded, ticket):
    if uploaded is None:
        return None

    if uploaded.size > 5 * 1024 * 1024:
        raise ValueError("Image must be 5 MB or smaller.")

    if uploaded.type not in ("image/jpeg", "image/png", "image/webp"):
        raise ValueError("Only JPEG, PNG or WebP images are accepted.")

    try:
        from PIL import Image
        image = Image.open(uploaded)
        image.verify()
        uploaded.seek(0)
        image = Image.open(uploaded).convert("RGB")
        output_path = UPLOAD_DIR / f"{ticket}.jpg"
        image.save(output_path, "JPEG", quality=85, optimize=True)
        return str(output_path.relative_to(APP_DIR))
    except Exception as exc:
        raise ValueError("The image could not be validated.") from exc

# Render anonymous question submission.
def render_ask():
    st.title("🕊️ " + t("ask"))
    st.info(t("privacy_text"))

    topics = [
        "Periods and the menstrual cycle",
        "Menstrual products",
        "Personal hygiene",
        "Myths versus facts",
        "Pain and common concerns",
        "Waste disposal",
        "Other"
    ]
    age_groups = ["Not provided", "Under 13", "13–15", "16–18", "19–24", "25+", "Prefer not to say"]

    with st.form("question_form", clear_on_submit=True):
        topic = st.selectbox(t("topic"), topics)
        age_group = st.selectbox(t("age"), age_groups)
        question = st.text_area(t("question"), max_chars=2500, height=160)
        attachment = st.file_uploader(t("attachment"), type=["jpg", "jpeg", "png", "webp"])
        consent = st.checkbox(t("consent"))
        submitted = st.form_submit_button(t("submit"), type="primary", use_container_width=True)

    if submitted:
        if not question.strip():
            st.error("Please enter your question.")
        elif not consent:
            st.error("Please confirm the educational-support notice.")
        elif re.search(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", question) or re.search(r"\b(?:\+?\d[\d\s()-]{8,}\d)\b", question):
            st.error("Please remove phone numbers and email addresses to protect your privacy.")
        else:
            ticket = uuid.uuid4().hex[:10].upper()
            try:
                attachment_path = save_image(attachment, ticket)
                salt = os.getenv("SAKHICYCLE_TICKET_SALT", "change-this-before-deployment")
                ticket_hash = hashlib.sha256((salt + ticket).encode()).hexdigest()

                with connect() as connection:
                    connection.execute(
                        """INSERT INTO questions
                        (id, ticket_hash, topic, age_group, language, question, attachment_path, status, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending', ?)""",
                        (
                            uuid.uuid4().hex,
                            ticket_hash,
                            topic,
                            None if age_group == "Not provided" else age_group,
                            st.session_state.language,
                            question.strip(),
                            attachment_path,
                            datetime.utcnow().isoformat(timespec="seconds")
                        )
                    )

                st.session_state.last_ticket = ticket
                log_action("anonymous", "question_submitted")
                st.success("Your question has been submitted for review.")
            except ValueError as exc:
                st.error(str(exc))

    if st.session_state.get("last_ticket"):
        st.subheader(t("ticket"))
        st.code(st.session_state.last_ticket)
        st.write(t("ticket_help"))

# Render private question status lookup.
def render_track():
    st.title("🔎 " + t("track"))
    ticket = st.text_input(t("ticket_input"), max_chars=10).strip().upper()

    if st.button(t("check"), type="primary"):
        if not re.fullmatch(r"[A-F0-9]{10}", ticket):
            st.error(t("no_question"))
            return

        salt = os.getenv("SAKHICYCLE_TICKET_SALT", "change-this-before-deployment")
        ticket_hash = hashlib.sha256((salt + ticket).encode()).hexdigest()

        with connect() as connection:
            item = connection.execute(
                "SELECT topic, status, response FROM questions WHERE ticket_hash = ?",
                (ticket_hash,)
            ).fetchone()

        if not item:
            st.error(t("no_question"))
        else:
            st.write(f"**{t('topic')}:** {item['topic']}")
            st.write(f"**{t('status')}:** {item['status']}")
            if item["status"] == "Answered" and item["response"]:
                st.subheader(t("reply"))
                st.write(item["response"])
                st.caption("This response is educational and is not a personal diagnosis.")
            elif item["status"] == "Escalated":
                st.warning("Your question has been referred for further review.")
            else:
                st.info("Your question is awaiting review.")

# Render FAQs from the database.
def render_faq():
    st.title("❔ " + t("faq"))
    with connect() as connection:
        rows = connection.execute(
            "SELECT title, body FROM content WHERE kind='faq' AND active=1 ORDER BY title"
        ).fetchall()

    for row in rows:
        with st.expander(row["title"]):
            st.write(row["body"])

# Render reminders.
def render_reminders():
    st.title("🔔 " + t("reminders"))
    st.caption("Do not enter sensitive personal details into reminders.")

    with st.form("reminder_form", clear_on_submit=True):
        label = st.text_input("Reminder title", max_chars=80)
        due_date = st.date_input("Reminder date", value=date.today())
        note = st.text_input("Optional note", max_chars=200)
        submitted = st.form_submit_button("Add reminder", type="primary")

    if submitted:
        if not label.strip():
            st.error("Enter a reminder title.")
        else:
            with connect() as connection:
                connection.execute(
                    "INSERT INTO reminders VALUES (?, ?, ?, ?, ?)",
                    (
                        uuid.uuid4().hex,
                        label.strip(),
                        due_date.isoformat(),
                        note.strip(),
                        datetime.utcnow().isoformat(timespec="seconds")
                    )
                )
            st.success("Reminder saved.")
            st.rerun()

    with connect() as connection:
        reminders = connection.execute(
            "SELECT id, label, due_date, note FROM reminders ORDER BY due_date"
        ).fetchall()

    st.subheader("Saved reminders")

    if not reminders:
        st.info("No reminders yet.")

    for reminder in reminders:
        with st.container(border=True):
            st.write(f"**{reminder['label']}** — {reminder['due_date']}")
            if reminder["note"]:
                st.caption(reminder["note"])
            if st.button("Delete", key=f"delete_{reminder['id']}"):
                with connect() as connection:
                    connection.execute("DELETE FROM reminders WHERE id = ?", (reminder["id"],))
                st.rerun()

# Read staff credentials from environment variables or Streamlit secrets.
def password_matches(username, password, role):
    configured_user = os.getenv(f"{role.upper()}_USERNAME", "")
    configured_password = os.getenv(f"{role.upper()}_PASSWORD", "")

    try:
        configured_user = st.secrets.get(f"{role.lower()}_username", configured_user)
        configured_password = st.secrets.get(f"{role.lower()}_password", configured_password)
    except Exception:
        pass

    return bool(
        configured_user
        and configured_password
        and hmac.compare_digest(username, configured_user)
        and hmac.compare_digest(password, configured_password)
    )

# Render the staff portal.
def render_admin():
    st.title("🛡️ " + t("admin"))

    if not st.session_state.get("staff_user"):
        st.subheader(t("login"))

        with st.form("staff_login"):
            username = st.text_input(t("username"))
            password = st.text_input(t("password"), type="password")
            role = st.selectbox("Role", ["admin", "moderator"])
            submitted = st.form_submit_button(t("sign_in"), type="primary")

        if submitted:
            if password_matches(username, password, role):
                st.session_state.staff_user = username
                st.session_state.staff_role = role
                log_action(username, "login")
                st.rerun()
            else:
                st.error("Login failed. Configure valid staff credentials first.")

        if not os.getenv("ADMIN_PASSWORD") and not os.getenv("MODERATOR_PASSWORD"):
            st.warning("Staff login requires credentials configured by the application administrator.")
        return

    username = st.session_state.staff_user
    role = st.session_state.staff_role
    st.write(f"Signed in as **{username}** · Role: **{role}**")

    if st.button(t("logout")):
        log_action(username, "logout")
        st.session_state.pop("staff_user", None)
        st.session_state.pop("staff_role", None)
        st.rerun()

    questions_tab, content_tab, analytics_tab, logs_tab = st.tabs(
        ["Questions", "Content", "Analytics", "Audit log"]
    )

    with questions_tab:
        with connect() as connection:
            questions = connection.execute(
                "SELECT * FROM questions ORDER BY created_at DESC"
            ).fetchall()

        if not questions:
            st.info("No questions submitted yet.")

        for item in questions:
            with st.expander(f"{item['status']} · {item['topic']} · {item['created_at'][:16]}"):
                st.write(item["question"])
                st.caption(f"Language: {item['language']} · Age group: {item['age_group'] or 'Not provided'}")

                if item["attachment_path"]:
                    image_path = APP_DIR / item["attachment_path"]
                    if image_path.exists():
                        st.image(str(image_path))

                if role == "admin":
                    statuses = ["Pending", "Answered", "Escalated", "Rejected"]
                    status = st.selectbox(
                        "Review status",
                        statuses,
                        index=statuses.index(item["status"]),
                        key=f"status_{item['id']}"
                    )
                    response = st.text_area(
                        t("response"),
                        value=item["response"] or "",
                        max_chars=5000,
                        key=f"response_{item['id']}"
                    )

                    if st.button(t("publish"), key=f"publish_{item['id']}"):
                        if status == "Answered" and not response.strip():
                            st.error("Add a response before marking this question as answered.")
                        else:
                            answered_at = datetime.utcnow().isoformat(timespec="seconds") if status == "Answered" else None
                            with connect() as connection:
                                connection.execute(
                                    "UPDATE questions SET status=?, response=?, reviewer=?, answered_at=? WHERE id=?",
                                    (status, response.strip() or None, username, answered_at, item["id"])
                                )
                            log_action(username, "question_reviewed", item["id"])
                            st.success("Question updated.")
                            st.rerun()
                else:
                    st.info("Moderator access is read-only in this starter version.")

    with content_tab:
        if role != "admin":
            st.info("Admin access is required to manage content.")
        else:
            with connect() as connection:
                faqs = connection.execute(
                    "SELECT id, title, body, active FROM content WHERE kind='faq' ORDER BY title"
                ).fetchall()

            for faq in faqs:
                with st.expander(faq["title"]):
                    title = st.text_input("Question", value=faq["title"], key=f"title_{faq['id']}")
                    body = st.text_area("Answer", value=faq["body"], key=f"body_{faq['id']}")
                    active = st.checkbox("Published", value=bool(faq["active"]), key=f"active_{faq['id']}")

                    if st.button("Save FAQ", key=f"save_{faq['id']}"):
                        with connect() as connection:
                            connection.execute(
                                "UPDATE content SET title=?, body=?, active=?, updated_at=? WHERE id=?",
                                (title.strip(), body.strip(), int(active), datetime.utcnow().isoformat(timespec="seconds"), faq["id"])
                            )
                        log_action(username, "faq_updated", faq["id"])
                        st.success("FAQ saved.")
                        st.rerun()

            with st.form("add_faq", clear_on_submit=True):
                new_title = st.text_input("New question")
                new_body = st.text_area("New answer")
                add = st.form_submit_button("Add FAQ")

            if add:
                if new_title.strip() and new_body.strip():
                    with connect() as connection:
                        connection.execute(
                            "INSERT INTO content VALUES (?, 'faq', ?, ?, 'English', 1, ?)",
                            (uuid.uuid4().hex, new_title.strip(), new_body.strip(), datetime.utcnow().isoformat(timespec="seconds"))
                        )
                    log_action(username, "faq_created")
                    st.rerun()
                else:
                    st.error("Enter both a question and answer.")

    with analytics_tab:
        with connect() as connection:
            total = connection.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
            pending = connection.execute("SELECT COUNT(*) FROM questions WHERE status='Pending'").fetchone()[0]
            answered = connection.execute("SELECT COUNT(*) FROM questions WHERE status='Answered'").fetchone()[0]
            topics = connection.execute("SELECT topic, COUNT(*) AS total FROM questions GROUP BY topic").fetchall()

        first, second, third = st.columns(3)
        first.metric("Total questions", total)
        second.metric("Pending", pending)
        third.metric("Answered", answered)

        if topics:
            st.bar_chart({row["topic"]: row["total"] for row in topics})

    with logs_tab:
        with connect() as connection:
            logs = connection.execute(
                "SELECT actor, action, item_id, created_at FROM audit_log ORDER BY created_at DESC LIMIT 200"
            ).fetchall()
        st.dataframe([dict(row) for row in logs], use_container_width=True, hide_index=True)

# Run the application.
def main():
    init_db()

    # Initialise navigation state before displaying controls.
    if "language" not in st.session_state:
        st.session_state.language = "English"

    if "page" not in st.session_state:
        st.session_state.page = "Home"

    pages = [
        "Home",
        "Learn",
        "Knowledge quiz",
        "Ask anonymously",
        "Check my question",
        "FAQs",
        "Reminders",
        "Staff portal"
    ]

    labels = {
        "Home": t("home"),
        "Learn": t("learn"),
        "Knowledge quiz": t("quiz"),
        "Ask anonymously": t("ask"),
        "Check my question": t("track"),
        "FAQs": t("faq"),
        "Reminders": t("reminders"),
        "Staff portal": t("admin")
    }

    # Keep the sidebar radio selection synchronised with button navigation.
    if "nav_page" not in st.session_state:
        st.session_state.nav_page = st.session_state.page

    if st.session_state.nav_page != st.session_state.page:
        st.session_state.nav_page = st.session_state.page

    with st.sidebar:
        st.markdown("# 🌸 SakhiCycle")
        language = st.selectbox(
            t("language"),
            list(I18N.keys()),
            key="language_selector",
            index=list(I18N.keys()).index(st.session_state.language)
        )
        st.session_state.language = language
        st.divider()

        selected = st.radio(
            "Navigation",
            pages,
            format_func=lambda page: labels[page],
            key="nav_page"
        )
        st.session_state.page = selected
        st.divider()
        st.caption("Educational resource · Not a diagnostic service")

    # Render the selected page.
    page = st.session_state.page

    if page == "Home":
        render_home()
    elif page == "Learn":
        render_learn()
    elif page == "Knowledge quiz":
        render_quiz()
    elif page == "Ask anonymously":
        render_ask()
    elif page == "Check my question":
        render_track()
    elif page == "FAQs":
        render_faq()
    elif page == "Reminders":
        render_reminders()
    elif page == "Staff portal":
        render_admin()

    st.divider()
    st.caption("SakhiCycle · Respectful, inclusive, privacy-aware menstrual health education")

# Start the app.
if __name__ == "__main__":
    main()
