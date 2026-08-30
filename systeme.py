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

    # Search Functionality

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
            AND phone NOT IN(SELECT Phone FROM customers WHERE Status = 'incomplete')
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


            
            

# Incomplet Tab
with tab2:

    st.subheader("⏳ Incomplete Customers")

    # Fetching data for all brothers if at least one is incomplete
    mycursor.execute("""
        SELECT * FROM customers
        WHERE Phone IN (SELECT Phone FROM customers WHERE Status = 'incomplete')
        ORDER BY Phone, id
    """)

    incomplete_data = mycursor.fetchall()

    if not incomplete_data:
        st.info("No incomplete customers found.")
    else:
        df = pd.DataFrame(incomplete_data)
        grouped = df.groupby('Phone')

        # Looping through each group (Phone Number)
        for phone, family_group in grouped:
            
            # Check if it is a family or a single customer
            is_family = len(family_group) > 1
            family_total_price = 0.0
            
            # Show Family Header only if they are a family
            if is_family:
                st.markdown(f"###  Family (Phone Number: {phone})")
            
            # Looping through individuals
            for index, brother in family_group.iterrows():
                customer_id = brother['id']
                name = brother['Name']
                status = brother['Status']
                
                # Handling Price
                current_price_db = brother['Total_Price']
                safe_price = float(current_price_db) if pd.notna(current_price_db) and current_price_db != "" else 0.0
                family_total_price += safe_price
                
                # Status format
                status_emoji = "✅ Ready" if status == 'complete' else "⏳ Incomplete"
                
                st.write(f"**{customer_id}. {name}** | Status: {status_emoji} | 💰 {safe_price} DH")
                
                # ==========================================
                # Actions: Only visible if the customer is Incomplete
                # ==========================================
                if status == 'incomplete':
                    
                    if st.button(f"✓ Complete {name}", key=f"complete_{customer_id}"):
                        update_sql = "UPDATE customers SET Status = 'complete' WHERE id = %s"
                        mycursor.execute(update_sql, (customer_id,))
                        mydb.commit()
                        st.rerun()

                    col1, col2 = st.columns(2)
                    with col1:
                        new_book_price = st.number_input(f"Add New Price for {name}:", min_value=0.0, step=1.0, key=f"new_price_{customer_id}")
                    with col2:
                        if st.button("➕ Update Total", key=f"update_btn_{customer_id}"):
                            updated_total = safe_price + new_book_price
                            update_sql = "UPDATE customers SET Total_Price = %s WHERE id = %s"
                            mycursor.execute(update_sql, (updated_total, customer_id))
                            mydb.commit()
                            st.rerun()
                
                # Small separator between brothers (only for families)
                if is_family:
                    st.write("---")

            # Show Total Family Price (only for families)
            if is_family:
                st.success(f"💰 **Total Family Price:** {family_total_price} DH")
            
            # Main divider between different customers/families
            st.divider()
# Historique tab
with tab3:

    st.subheader("📜 Historique")

    # 1. مربع البحث
    search_history = st.text_input(
        "Search by Name or Phone",
        placeholder="Type a name or phone number and press Enter...",
        key="search_history_bar"
    )

    # 2. تحديد نوع الاستعلام (بحث أم عرض الكل)
    if search_history:
        search_sql = """
            SELECT * FROM customers
            WHERE NotifiedAt IS NOT NULL
            AND (Name LIKE %s OR id LIKE %s)
            ORDER BY NotifiedAt DESC
        """
        search_val = f"%{search_history}%"
        mycursor.execute(search_sql, (search_val, search_val))
    else:
        mycursor.execute("""
            SELECT * FROM customers
            WHERE NotifiedAt IS NOT NULL
            ORDER BY NotifiedAt DESC
        """)

    history_data = mycursor.fetchall()

    # 3. عرض البيانات
    if not history_data:
        st.info("No records found.")
    else:
        for customer in history_data:
            customer_id = customer['id']
            name = customer['Name']
            phone = customer['Phone']
            notified_at = customer['NotifiedAt']
            current_price_db = customer['Total_Price']
            safe_current_price = float(current_price_db) if current_price_db is not None else 0.0


            st.write(f"**{customer_id}. {name}**")
            st.write(f"📱 {phone}")

            if notified_at:
                # تعديل التوقيت إذا لزم الأمر
                notified_at = notified_at + timedelta(hours=1)  
                st.write(
                    f"📅 {notified_at.strftime('%d/%m/%Y')} "
                    f"🕐 {notified_at.strftime('%H:%M:%S')}"
                )
                st.write("💰 **Finale Totale :**")
                st.write(f"**{safe_current_price}DH**"
                         )
            st.divider()
