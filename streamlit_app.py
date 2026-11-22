import datetime
import random

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

# Show app title and description.
st.set_page_config(page_title="פניות תמיכה", page_icon="🎫")

# The interface is in Hebrew, so lay the page out right-to-left.
st.markdown(
    """
    <style>
    .stApp { direction: rtl; }
    .stApp [data-testid="stVegaLiteChart"],
    .stApp [data-testid="stMetricDelta"],
    .stApp [data-testid="stDataFrame"] { direction: ltr; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🎫 פניות תמיכה")
st.write(
    """
    האפליקציה הזו מדגימה איך אפשר לבנות כלי פנימי ב-Streamlit. כאן אנחנו
    מיישמים תהליך עבודה של פניות תמיכה. המשתמש יכול ליצור פנייה, לערוך
    פניות קיימות ולצפות בנתונים סטטיסטיים.
    """
)

# User-facing labels. The dataframe keeps its English column names internally, and
# these labels are used wherever a column is shown to the user.
COLUMN_LABELS = {
    "ID": "מזהה",
    "Issue": "תיאור הבעיה",
    "Status": "סטטוס",
    "Priority": "עדיפות",
    "Date Submitted": "תאריך הגשה",
}
STATUSES = ["פתוחה", "בטיפול", "סגורה"]
PRIORITIES = ["גבוהה", "בינונית", "נמוכה"]
MONTHS = ["ינו׳", "פבר׳", "מרץ", "אפר׳", "מאי", "יוני", "יולי", "אוג׳", "ספט׳", "אוק׳", "נוב׳", "דצמ׳"]

# Create a random Pandas dataframe with existing tickets.
if "df" not in st.session_state:

    # Set seed for reproducibility.
    np.random.seed(42)

    # Make up some fake issue descriptions.
    issue_descriptions = [
        "בעיות קישוריות לרשת במשרד",
        "תוכנה קורסת בעת ההפעלה",
        "המדפסת אינה מגיבה לפקודות הדפסה",
        "השבתה של שרת הדואר האלקטרוני",
        "כשל בגיבוי הנתונים",
        "בעיות אימות בהתחברות",
        "ירידה בביצועי האתר",
        "זוהתה פרצת אבטחה",
        "תקלת חומרה בחדר השרתים",
        "עובד אינו מצליח לגשת לקבצים משותפים",
        "כשל בחיבור למסד הנתונים",
        "האפליקציה לנייד אינה מסנכרנת נתונים",
        "בעיות במערכת הטלפוניה (VoIP)",
        "בעיות חיבור VPN לעובדים מרחוק",
        "עדכוני מערכת גורמים לבעיות תאימות",
        "שטח האחסון בשרת הקבצים עומד להיגמר",
        "התראות ממערכת זיהוי החדירות",
        "שגיאות במערכת ניהול המלאי",
        "נתוני לקוחות אינם נטענים ב-CRM",
        "כלי שיתוף הפעולה אינו שולח התראות",
    ]

    # Generate the dataframe with 100 rows/tickets.
    data = {
        "ID": [f"TICKET-{i}" for i in range(1100, 1000, -1)],
        "Issue": np.random.choice(issue_descriptions, size=100),
        "Status": np.random.choice(STATUSES, size=100),
        "Priority": np.random.choice(PRIORITIES, size=100),
        "Date Submitted": [
            datetime.date(2023, 6, 1) + datetime.timedelta(days=random.randint(0, 182))
            for _ in range(100)
        ],
    }
    df = pd.DataFrame(data)

    # Save the dataframe in session state (a dictionary-like object that persists across
    # page runs). This ensures our data is persisted when the app updates.
    st.session_state.df = df


# Show a section to add a new ticket.
st.header("הוספת פנייה")

# We're adding tickets via an `st.form` and some input widgets. If widgets are used
# in a form, the app will only rerun once the submit button is pressed.
with st.form("add_ticket_form"):
    issue = st.text_area("תארו את הבעיה")
    priority = st.selectbox("עדיפות", PRIORITIES)
    submitted = st.form_submit_button("שליחה")

if submitted:
    # Make a dataframe for the new ticket and append it to the dataframe in session
    # state.
    recent_ticket_number = int(max(st.session_state.df.ID).split("-")[1])
    today = datetime.datetime.now().strftime("%m-%d-%Y")
    df_new = pd.DataFrame(
        [
            {
                "ID": f"TICKET-{recent_ticket_number+1}",
                "Issue": issue,
                "Status": STATUSES[0],
                "Priority": priority,
                "Date Submitted": today,
            }
        ]
    )

    # Show a little success message.
    st.write("הפנייה נשלחה! אלה פרטי הפנייה:")
    st.dataframe(
        df_new,
        use_container_width=True,
        hide_index=True,
        column_config=COLUMN_LABELS,
    )
    st.session_state.df = pd.concat([df_new, st.session_state.df], axis=0)

# Show section to view and edit existing tickets in a table.
st.header("פניות קיימות")
st.write(f"מספר הפניות: `{len(st.session_state.df)}`")

st.info(
    "אפשר לערוך את הפניות בלחיצה כפולה על תא. שימו לב שהתרשימים שלמטה "
    "מתעדכנים אוטומטית! אפשר גם למיין את הטבלה בלחיצה על כותרות העמודות.",
    icon="✍️",
)

# Show the tickets dataframe with `st.data_editor`. This lets the user edit the table
# cells. The edited data is returned as a new dataframe.
edited_df = st.data_editor(
    st.session_state.df,
    use_container_width=True,
    hide_index=True,
    column_config={
        **COLUMN_LABELS,
        "Status": st.column_config.SelectboxColumn(
            COLUMN_LABELS["Status"],
            help="סטטוס הפנייה",
            options=STATUSES,
            required=True,
        ),
        "Priority": st.column_config.SelectboxColumn(
            COLUMN_LABELS["Priority"],
            help="עדיפות הפנייה",
            options=PRIORITIES,
            required=True,
        ),
    },
    # Disable editing the ID and Date Submitted columns.
    disabled=["ID", "Date Submitted"],
)

# Show some metrics and charts about the ticket.
st.header("סטטיסטיקה")

# Show metrics side by side using `st.columns` and `st.metric`.
col1, col2, col3 = st.columns(3)
num_open_tickets = len(st.session_state.df[st.session_state.df.Status == STATUSES[0]])
col1.metric(label="מספר הפניות הפתוחות", value=num_open_tickets, delta=10)
col2.metric(label="זמן תגובה ראשונה (שעות)", value=5.2, delta=-1.5)
col3.metric(label="זמן פתרון ממוצע (שעות)", value=16, delta=2)

# Show two Altair charts using `st.altair_chart`.
st.write("")
st.write("##### סטטוס הפניות לפי חודש")
status_plot = (
    alt.Chart(edited_df)
    .mark_bar()
    .encode(
        x=alt.X(
            "month(Date Submitted):O",
            title="חודש",
            axis=alt.Axis(labelExpr=f"{MONTHS}[month(datum.value)]", labelAngle=0),
        ),
        y=alt.Y("count():Q", title="מספר הפניות"),
        xOffset="Status:N",
        color=alt.Color("Status:N", title=COLUMN_LABELS["Status"]),
    )
    .configure_legend(
        orient="bottom", titleFontSize=14, labelFontSize=14, titlePadding=5
    )
)
st.altair_chart(status_plot, use_container_width=True, theme="streamlit")

st.write("##### עדיפויות הפניות הנוכחיות")
priority_plot = (
    alt.Chart(edited_df)
    .mark_arc()
    .encode(
        theta="count():Q",
        color=alt.Color("Priority:N", title=COLUMN_LABELS["Priority"]),
    )
    .properties(height=300)
    .configure_legend(
        orient="bottom", titleFontSize=14, labelFontSize=14, titlePadding=5
    )
)
st.altair_chart(priority_plot, use_container_width=True, theme="streamlit")
