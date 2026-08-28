import pandas as pd
import streamlit as st
from urllib.parse import quote
import mysql.connector
from datetime import datetime
from datetime import timedelta

def init_connection():
    return mysql.connector.connect(
        host=st.secrets["database"]["host"],
        port =st.secrets["database"]["port"],
        user=st.secrets["database"]["user"],
        password=st.secrets["database"]["password"],
        database=st.secrets["database"]["database"]
    )

mydb = init_connection()
mycursor = mydb.cursor(dictionary=True)

st.title('Al-Imane Library Systeme')

st.sidebar.header('New Customers +')
with st.sidebar.form("Add New Customer"):
    new_id = st.number_input(
    "Number of liste",
    min_value=1,
    step=1)
    name = st.text_input("Name")
    phone = st.text_input("Phone:(ex : 21267........)")
    status = st.selectbox("Status", ["complete", "incomplete"])
    current_price = st.number_input('Current Price', min_value=0.0, step=0.01)
    submitted = st.form_submit_button("Add Customer")

    if submitted:
        if not name:
            st.error("Please enter a name.")
        elif not phone:
            st.error("Please enter a phone number.")
        elif not (phone.startswith("212") and len(phone) == 12 and phone.isdigit()):
            st.error("Please enter a valid phone number.")
        else:
            sql = "INSERT INTO customers (id, Name, Phone, Status, Notified , Total_Price) VALUES (%s, %s, %s, %s, 0, %s)"
            val = (new_id,name, phone, status, current_price)
            mycursor.execute(sql, val)
            mydb.commit()
            st.success(f"Customer {name} added successfully!")

tab1, tab2, tab3 = st.tabs([
    "📚 Complete",
    "⏳ Incomplete",
    "📜 Historique"
])

with tab1:
    st.subheader("Customers Who Have Completed Their Registration")

    search = st.text_input(
        "Search by Name or Number of liste",
        placeholder="Type a name or number of liste to search..."
    )

    if search:

        search_sql = """
            SELECT * FROM customers
            WHERE Status = 'complete'
            AND Notified = 0
            AND (Name LIKE %s OR id LIKE %s)
        """

        search_values = f"%{search}%"

        mycursor.execute(
            search_sql,
            (search_values, search_values)
        )

    else:

        mycursor.execute("""
            SELECT * FROM customers
            WHERE Status = 'complete'
            AND Notified = 0
            ORDER BY id
        """)

    customer_data = mycursor.fetchall()

    if not customer_data:

        st.success("No customers have completed their registration.")

    else:

        for customer in customer_data:

            customer_id = customer['id']
            name = customer['Name']
            number = customer['id']
            phone = customer['Phone']
            current_price_db = customer['Total_Price']
            safe_current_price = float(current_price_db) if current_price_db is not None else 0.0

            # رسالة WhatsApp
            message = f"""السلام عليكم {name}،
لقد أصبحت لائحة الكتب التي طلبتها جاهزة.
المرجو الحضور إلى المكتبة لاستلامها.
شكراً."""

            whatssap_url = f"https://wa.me/{phone}?text={quote(message)}"

            st.write(f"**{number}. {name}**")
            st.write(
                "the book is complete and ready to be picked up"
            )

            # =========================
            # الأزرار
            # =========================

            col1, col2, col3, col4= st.columns(4)

            # WhatsApp
            with col1:
                st.link_button(
                    "Send Message on WhatsApp",
                    whatssap_url
                )

            # Delete
            with col2:

                with st.popover("Delete 🗑️"):

                    st.warning(
                        "Are you sure you want to delete this customer?"
                    )

                    col_yes, col_no = st.columns(2)

                    with col_yes:

                        if st.button(
                            "Yes",
                            key=f"yes_del_{customer_id}"
                        ):

                            delete_sql = """
                                DELETE FROM customers
                                WHERE id = %s
                            """

                            mycursor.execute(
                                delete_sql,
                                (customer_id,)
                            )

                            mydb.commit()
                            st.rerun()

                    with col_no:

                        if st.button(
                            "No",
                            key=f"no_del_{customer_id}"
                        ):
                            st.rerun()

            # Notified
            with col3:

                if st.button(
                    "Notified ✓",
                    key=f"notify_{customer_id}"
                ):

                    update_sql = """
                        UPDATE customers
                        SET Notified = 1,
                            NotifiedAt = %s
                        WHERE id = %s
                    """

                    mycursor.execute(
                        update_sql,
                        (datetime.now(), customer_id)
                    )

                    mydb.commit()

                    st.success(
                        f"{name} has been notified!"
                    )

                    st.rerun()

        # Price Show
            
            with col4:
                st.write("💰 **المجموع الحالي:**")
                st.write(f"**{safe_current_price} درهم**")
            st.divider()


            
            
#Incomplet Tab
with tab2:

    st.subheader("Incomplete Customers")

    mycursor.execute("""
        SELECT * FROM customers
        WHERE Status = 'incomplete'
        ORDER BY id
    """)

    incomplete_data = mycursor.fetchall()

    if not incomplete_data:
        st.info("No incomplete customers.")
    else:

        for customer in incomplete_data:

            customer_id = customer['id']
            name = customer['Name']
            phone = customer['Phone']
            # Importing db of price :
            current_price_db = customer['Total_Price']
            safe_current_price = float(current_price_db) if current_price_db is not None else 0.0


            st.write(f"**{customer_id}. {name}**")
            st.write("The customer's registration is incomplete.")
            st.write(f"💰 **المجموع الحالي:** {safe_current_price} درهم")

            if st.button(
                "✓ Complete",
                key=f"complete_{customer_id}"
            ):

                update_sql = """
                    UPDATE customers
                    SET Status = 'complete'
                    WHERE id = %s
                """

                mycursor.execute(
                    update_sql,
                    (customer_id,)
                )

                mydb.commit()
                st.rerun()
 

            col1 , col2 = st.columns(2)
            with col1:
                
                new_book_price = st.number_input("إضافة ثمن كتاب جديد:", min_value=0.0, step=1.0, key=f"new_price_{customer_id}")
            with col2:
                if st.button("➕ تحديث المجموع", key=f"update_btn_{customer_id}"):
                    safe_current_price = customer['Total_Price'] if customer['Total_Price'] is not None else 0.0
                    updated_total = safe_current_price + new_book_price
        

                    update_sql = "UPDATE customers SET Total_Price = %s WHERE id = %s"
                    mycursor.execute(update_sql, (updated_total, customer_id))
                    mydb.commit()
        
                    st.rerun()
            st.divider()

# Historique tab
with tab3:

    st.subheader("📜 Historique")

    mycursor.execute("""
        SELECT *
        FROM customers
        WHERE Notified IS NOT NULL
        ORDER BY NotifiedAt DESC
    """)

    history_data = mycursor.fetchall()

    if not history_data:
        st.info("No notifications have been sent yet.")
    else:

        for customer in history_data:

            customer_id = customer['id']
            name = customer['Name']
            phone = customer['Phone']
            notified_at = customer['NotifiedAt']

            st.write(f"**{customer_id}. {name}**")
            st.write(f"📱 {phone}")

            if notified_at:
                notified_at = notified_at + timedelta(hours=1)  # Adjusting for timezone if needed
                st.write(
                    f"📅 {notified_at.strftime('%d/%m/%Y')} "
                    f"🕐 {notified_at.strftime('%H:%M:%S')}"
                )

            st.divider()