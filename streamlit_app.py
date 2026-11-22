import datetime

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

# Show app title and description.
st.set_page_config(page_title="הזמנות רכש", page_icon="🛒", layout="wide")

# The interface is in Hebrew, so lay the page out right-to-left.
st.markdown(
    """
    <style>
    .stApp { direction: rtl; }
    .stApp [data-testid="stElementContainer"],
    .stApp [data-testid="stMarkdownContainer"],
    .stApp [data-testid="stWidgetLabel"],
    .stApp [data-testid="stMetric"],
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
    .stApp p, .stApp input, .stApp textarea { text-align: right; }
    .stApp [data-testid="stVegaLiteChart"],
    .stApp [data-testid="stMetricDelta"],
    .stApp [data-testid="stDataFrame"] { direction: ltr; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🛒 ניהול הזמנות רכש")
st.write(
    """
    מערכת לניהול הזמנות רכש. כאן אפשר ליצור הזמנת רכש חדשה, לעדכן הזמנות
    קיימות ולעקוב אחר היקף הרכש.
    """
)

# User-facing labels. The dataframe keeps English column names internally, and these
# labels are used wherever a column is shown to the user.
COLUMN_LABELS = {
    "ID": "מספר הזמנה",
    "Supplier": "ספק",
    "Department": "מחלקה",
    "Item": "תיאור הפריט",
    "Quantity": "כמות",
    "Unit Price": "מחיר ליחידה",
    "Total": "סכום כולל",
    "Status": "סטטוס",
    "Order Date": "תאריך הזמנה",
    "Delivery Date": "תאריך אספקה מבוקש",
}
STATUS_PENDING = "ממתינה לאישור"
STATUS_APPROVED = "אושרה"
STATUS_RECEIVED = "התקבלה"
STATUS_CANCELLED = "בוטלה"
STATUSES = [STATUS_PENDING, STATUS_APPROVED, STATUS_RECEIVED, STATUS_CANCELLED]
DEPARTMENTS = ["מערכות מידע", "תפעול", "שיווק", "כספים", "משאבי אנוש"]
MONTHS = ["ינו׳", "פבר׳", "מרץ", "אפר׳", "מאי", "יוני", "יולי", "אוג׳", "ספט׳", "אוק׳", "נוב׳", "דצמ׳"]
CURRENCY_FORMAT = "₪ %.2f"
# Tables are drawn left-to-right, so list the columns in reverse to get the first
# column on the right, as expected in Hebrew.
TABLE_COLUMN_ORDER = list(reversed(COLUMN_LABELS))


def format_currency(amount):
    return f"₪ {amount:,.0f}"


# Create a Pandas dataframe with some made-up existing purchase orders.
if "df" not in st.session_state:

    # Use a seeded generator for reproducibility.
    rng = np.random.default_rng(42)

    suppliers = [
        "אופיס פלוס בע״מ",
        "טכנו-מחשבים",
        "ריהוט הצפון",
        "דפוס המרכז",
        "ניקיון ואחזקה שירותים",
        "קפה ומשקאות ישראל",
        "אלקטרו-ציוד",
        "תוכנה וענן פתרונות",
    ]

    # Items with a typical unit price (in ILS).
    items = [
        ("מחשב נייד", 4200),
        ("מסך מחשב 27 אינץ׳", 950),
        ("כיסא משרדי ארגונומי", 780),
        ("שולחן עבודה מתכוונן", 1900),
        ("חבילת נייר A4", 22),
        ("טונר למדפסת", 310),
        ("רישיון תוכנה שנתי", 540),
        ("מקלדת ועכבר אלחוטיים", 180),
        ("חומרי ניקוי", 45),
        ("קפסולות קפה", 95),
        ("מקרן לחדר ישיבות", 2600),
        ("כרטיסי ביקור", 120),
    ]

    num_orders = 60
    item_indices = rng.integers(0, len(items), size=num_orders)
    order_dates = [
        datetime.date(2026, 1, 1) + datetime.timedelta(days=int(d))
        for d in rng.integers(0, 300, size=num_orders)
    ]
    data = {
        "ID": [f"PO-{i}" for i in range(1000 + num_orders, 1000, -1)],
        "Supplier": rng.choice(suppliers, size=num_orders),
        "Department": rng.choice(DEPARTMENTS, size=num_orders),
        "Item": [items[i][0] for i in item_indices],
        "Quantity": rng.integers(1, 21, size=num_orders),
        "Unit Price": [float(items[i][1]) for i in item_indices],
        "Status": rng.choice(STATUSES, size=num_orders, p=[0.3, 0.3, 0.3, 0.1]),
        "Order Date": order_dates,
        "Delivery Date": [
            d + datetime.timedelta(days=int(n))
            for d, n in zip(order_dates, rng.integers(7, 45, size=num_orders))
        ],
    }
    df = pd.DataFrame(data)
    df.insert(6, "Total", df["Quantity"] * df["Unit Price"])

    # Save the dataframe in session state (a dictionary-like object that persists across
    # page runs). This ensures our data is persisted when the app updates.
    st.session_state.df = df
    # Version of the orders table widget. It is bumped whenever a row is added, so the
    # table starts over with a clean edit state that matches the new row positions.
    st.session_state.editor_version = 0


# Show a section to create a new purchase order.
st.header("יצירת הזמנת רכש")

# We're adding orders via an `st.form` and some input widgets. If widgets are used
# in a form, the app will only rerun once the submit button is pressed.
with st.form("add_order_form", clear_on_submit=True):
    form_col1, form_col2 = st.columns(2)
    supplier = form_col1.text_input("ספק")
    department = form_col2.selectbox("מחלקה", DEPARTMENTS)
    item = st.text_area("תיאור הפריט")
    form_col3, form_col4, form_col5 = st.columns(3)
    quantity = form_col3.number_input("כמות", min_value=1, value=1, step=1)
    unit_price = form_col4.number_input(
        "מחיר ליחידה (₪)", min_value=0.0, value=0.0, step=10.0, format="%.2f"
    )
    delivery_date = form_col5.date_input(
        "תאריך אספקה מבוקש",
        value=datetime.date.today() + datetime.timedelta(days=14),
        min_value=datetime.date.today(),
        format="DD/MM/YYYY",
    )
    submitted = st.form_submit_button("יצירת הזמנה")

if submitted:
    if not supplier.strip() or not item.strip():
        st.error("יש למלא את שם הספק ואת תיאור הפריט.")
    else:
        # Make a dataframe for the new order and put it at the top of the dataframe in
        # session state.
        last_order_number = max(
            int(order_id.split("-")[1]) for order_id in st.session_state.df.ID
        )
        df_new = pd.DataFrame(
            [
                {
                    "ID": f"PO-{last_order_number + 1}",
                    "Supplier": supplier.strip(),
                    "Department": department,
                    "Item": item.strip(),
                    "Quantity": int(quantity),
                    "Unit Price": float(unit_price),
                    "Total": int(quantity) * float(unit_price),
                    "Status": STATUS_PENDING,
                    "Order Date": datetime.date.today(),
                    "Delivery Date": delivery_date,
                }
            ]
        )

        # Show a little success message.
        st.success("ההזמנה נוצרה! אלה פרטי ההזמנה:")
        st.dataframe(
            df_new,
            width="stretch",
            hide_index=True,
            column_order=TABLE_COLUMN_ORDER,
            column_config={
                **COLUMN_LABELS,
                "Unit Price": st.column_config.NumberColumn(
                    COLUMN_LABELS["Unit Price"], format=CURRENCY_FORMAT
                ),
                "Total": st.column_config.NumberColumn(
                    COLUMN_LABELS["Total"], format=CURRENCY_FORMAT
                ),
                "Order Date": st.column_config.DateColumn(
                    COLUMN_LABELS["Order Date"], format="DD/MM/YYYY"
                ),
                "Delivery Date": st.column_config.DateColumn(
                    COLUMN_LABELS["Delivery Date"], format="DD/MM/YYYY"
                ),
            },
        )
        st.session_state.df = pd.concat(
            [df_new, st.session_state.df], axis=0, ignore_index=True
        )
        st.session_state.editor_version += 1

# Show section to view and update existing orders in a table.
st.header("הזמנות קיימות")
st.write(f"מספר ההזמנות: `{len(st.session_state.df)}`")

st.info(
    "אפשר לעדכן הזמנה בלחיצה כפולה על תא. הסכום הכולל והנתונים שלמטה מתעדכנים "
    "אוטומטית. אפשר גם למיין את הטבלה בלחיצה על כותרות העמודות.",
    icon="✍️",
)

editor_key = f"orders_editor_{st.session_state.editor_version}"


def save_order_edits():
    """Write the edits made in the table back to the dataframe in session state."""
    df = st.session_state.df
    for row, changes in st.session_state[editor_key]["edited_rows"].items():
        for column, value in changes.items():
            if column in ("Order Date", "Delivery Date") and value is not None:
                value = datetime.date.fromisoformat(value[:10])
            df.at[df.index[row], column] = value
    df["Total"] = df["Quantity"] * df["Unit Price"]


# Show the orders dataframe with `st.data_editor`. This lets the user edit the table
# cells. Every edit is saved to session state by the `on_change` callback.
st.data_editor(
    st.session_state.df,
    key=editor_key,
    on_change=save_order_edits,
    width="stretch",
    hide_index=True,
    column_order=TABLE_COLUMN_ORDER,
    column_config={
        **COLUMN_LABELS,
        "Supplier": st.column_config.TextColumn(COLUMN_LABELS["Supplier"], required=True),
        "Department": st.column_config.SelectboxColumn(
            COLUMN_LABELS["Department"], options=DEPARTMENTS, required=True
        ),
        "Item": st.column_config.TextColumn(COLUMN_LABELS["Item"], required=True),
        "Quantity": st.column_config.NumberColumn(
            COLUMN_LABELS["Quantity"], min_value=1, step=1, required=True
        ),
        "Unit Price": st.column_config.NumberColumn(
            COLUMN_LABELS["Unit Price"],
            min_value=0.0,
            format=CURRENCY_FORMAT,
            required=True,
        ),
        "Total": st.column_config.NumberColumn(
            COLUMN_LABELS["Total"],
            help="כמות כפול מחיר ליחידה",
            format=CURRENCY_FORMAT,
        ),
        "Status": st.column_config.SelectboxColumn(
            COLUMN_LABELS["Status"],
            help="סטטוס ההזמנה",
            options=STATUSES,
            required=True,
        ),
        "Order Date": st.column_config.DateColumn(
            COLUMN_LABELS["Order Date"], format="DD/MM/YYYY"
        ),
        "Delivery Date": st.column_config.DateColumn(
            COLUMN_LABELS["Delivery Date"], format="DD/MM/YYYY", required=True
        ),
    },
    # The order number, the order date and the computed total can't be edited.
    disabled=["ID", "Total", "Order Date"],
)

# Show some metrics and charts about the orders.
st.header("סטטיסטיקה")

orders = st.session_state.df
active_orders = orders[orders.Status != STATUS_CANCELLED]
pending_orders = orders[orders.Status == STATUS_PENDING]
committed_orders = orders[orders.Status.isin([STATUS_APPROVED, STATUS_RECEIVED])]

# Show metrics side by side using `st.columns` and `st.metric`.
col1, col2, col3 = st.columns(3)
col1.metric(label="הזמנות ממתינות לאישור", value=len(pending_orders))
col2.metric(
    label="סכום ממתין לאישור", value=format_currency(pending_orders.Total.sum())
)
col3.metric(
    label="רכש מאושר (אושרה / התקבלה)",
    value=format_currency(committed_orders.Total.sum()),
)

# Show two Altair charts using `st.altair_chart`. Dates are converted to datetimes so
# that Altair can group them by month.
chart_data = active_orders.assign(**{"Order Date": pd.to_datetime(active_orders["Order Date"])})

st.write("")
st.write("##### היקף הרכש לפי חודש וסטטוס (₪, ללא הזמנות שבוטלו)")
monthly_plot = (
    alt.Chart(chart_data)
    .mark_bar()
    .encode(
        x=alt.X(
            "month(Order Date):O",
            title="חודש ההזמנה",
            axis=alt.Axis(labelExpr=f"{MONTHS}[month(datum.value)]", labelAngle=0),
        ),
        y=alt.Y("sum(Total):Q", title="סכום (₪)"),
        color=alt.Color("Status:N", title=COLUMN_LABELS["Status"]),
        tooltip=[
            alt.Tooltip("Status:N", title=COLUMN_LABELS["Status"]),
            alt.Tooltip("sum(Total):Q", title="סכום (₪)", format=",.0f"),
        ],
    )
    .configure_legend(
        orient="bottom", titleFontSize=14, labelFontSize=14, titlePadding=5
    )
)
st.altair_chart(monthly_plot, theme="streamlit")

st.write("##### היקף הרכש לפי ספק (₪, ללא הזמנות שבוטלו)")
supplier_plot = (
    alt.Chart(chart_data)
    .mark_bar()
    .encode(
        x=alt.X("sum(Total):Q", title="סכום (₪)"),
        y=alt.Y("Supplier:N", title=None, sort="-x", axis=alt.Axis(labelLimit=140)),
        tooltip=[
            alt.Tooltip("Supplier:N", title=COLUMN_LABELS["Supplier"]),
            alt.Tooltip("sum(Total):Q", title="סכום (₪)", format=",.0f"),
        ],
    )
)
st.altair_chart(supplier_plot, theme="streamlit")
