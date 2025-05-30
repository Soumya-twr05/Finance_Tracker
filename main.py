import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import os
import json

category_file="categories.json"

st.set_page_config(page_title="Simple Finance App" , page_icon="💰", layout="wide")

if "categories" not in st.session_state:
    st.session_state.categories={
        "Uncategorized":[]
    }

if os.path.exists(category_file):
    with open(category_file,"r") as f:
        st.session_state.categories=json.load(f)
    
def save_categories():
    with open(category_file,"w") as f:
        json.dump(st.session_state.categories,f)

def categorize_transactions(df):
    df["Category"]="Uncategorized"

    for category,keywords in st.session_state.categories.items():
        if category =="Uncategorized" or not keywords:
            continue
        
        lowered_keywords=[keyword.lower().strip() for keyword in keywords]

        for idx,row in df.iterrows():
            details=row["Details"].lower().strip()
            if details in lowered_keywords:
                df.at[idx,"Category"]=category
    return df


def load_transactions(file):
    try:
        df=pd.read_csv(file)
        df.columns=[col.strip() for col in df.columns]
        df["Amount"]=df["Amount"].str.replace(",","").astype(float)
        df["Date"]=pd.to_datetime(df["Date"],format="mixed", dayfirst=True)
        # st.write(df)
        return categorize_transactions(df)
    except Exception as e:
        st.error(f"Error proccessing file:{str(e)}")    


def add__keyword_to_category(category,keyword):
    keyword=keyword.strip()
    if keyword and keyword not in st.session_state.categories(category):
        st.session_state.categories[category].append(keyword)
        save_categories()
        return True
    return False
        

def main():
    st.title("Simple Finance Dashboard")

    upload_file=st.file_uploader("Upload your transaction CSV file :",type=["csv"])

    if upload_file is not None:
        df=load_transactions(upload_file)

        if df is not None:
            debits_df=df[df["Debit/Credit"]=="Debit"].copy()
            credits_df=df[df["Debit/Credit"]=="Credit"].copy()
            
            st.session_state.debits_df=debits_df.copy()

            tab1, tab2=st.tabs(["Expence (Debits)","Payments (Credits)"])

            with tab1:
                new_category=st.text_input("New Category")
                add_button=st.button("Add Category")

                if add_button and new_category:
                    if new_category not in st.session_state.categories:
                        st.session_state.categories[new_category]=[]
                        save_categories()
                        st.success(f"Added a new category:{new_category}")
                        st.rerun()

                # st.write(debits_df)
                st.subheader("Your Expenses:")
                edited_df=st.data_editor(
                    st.session_state.debits_df[["Date","Details","Amount","Currency","Category","Debit/Credit"]],
                    column_config={
                        "Date":st.column_config.DateColumn("Date",format="DD/MM/YYYY"),
                        "Amount":st.column_config.NumberColumn("Amount",format="%.2f INR"),
                        "Category":st.column_config.SelectboxColumn(
                            "Categoty",
                            options=list(st.session_state.categories.keys())
                        )
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="category_editor"

                )

                save_button=st.button("Apply channges",type="primary")
                if save_button:
                    for idx, row in edited_df.iterrows():
                        new_category=row["Category"]
                        if new_category["category"]==st.session_state.debits_df.at[idx,"Category"]:
                            continue
                        details=row["Details"]
                        st.session_state.debits_df.at[idx,"Category"]=new_category
                        add__keyword_to_category(new_category,details)

                st.subheader('Expence Summary')
                category_total=st.session_state.debits_df.groupby("Category")["Amount"].sum().reset_index()       
                category_total=category_total.sort_values("Amount",ascending=True)

                st.dataframe(
                    category_total,
                    column_config={
                        "Amount":st.column_config.NumberColumn("Amount",format="%.2f INR")
                    },
                    use_container_width=True,
                    hide_index=True
                )

                fig=px.pie(
                    category_total,
                    values="Amount",
                    names="Category",
                    title="Expences by category"
                )
                st.plotly_chart(fig,use_container_width=True,)

            with tab2:
                st.write(credits_df)    

main()
