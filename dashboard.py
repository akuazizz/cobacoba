import pandas as pd
from pandas import DataFrame
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
import matplotlib.cm as cm
sns.set(style='dark')


# Helper function untuk Profil Demografis Pelanggan
def create_customer_profile_df(df):
    customer_profile = df.groupby(['customer_state', 'customer_city']).size().reset_index(name='customer_count')
    return customer_profile

# Helper function untuk Pola Pembelian Harian
def create_daily_orders_df(df: DataFrame) -> DataFrame:
    df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
    df['total_price'] = df.groupby('order_id')['price'].transform('sum')
    daily_orders_df = df.resample(rule='D', on='order_purchase_timestamp').agg({
        "order_id": "nunique",
        "total_price": "sum"
    }).reset_index()
    daily_orders_df.rename(columns={
        "order_id": "order_count",
        "total_price": "revenue"
    }, inplace=True)
    return daily_orders_df

# Helper function untuk Produk Paling Laris
def create_top_products_df(df: DataFrame) -> DataFrame:
    top_products = df.groupby(['product_category_name', 'product_id']).agg({'order_id': 'count', 'price': 'mean', 'freight_value': 'mean'}).reset_index()
    top_products = top_products.sort_values('order_id', ascending=False).head(10)
    return top_products

# Helper function untuk Kepuasan Pelanggan
def create_customer_satisfaction_df(df: DataFrame) -> DataFrame:
    customer_satisfaction = df.groupby('review_score').size().reset_index(name='order_id')
    return customer_satisfaction

# Helper function untuk Loyalitas Pelanggan
def create_rfm_df(df: DataFrame) -> DataFrame:
    df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
    df['total_price'] = df.groupby('order_id')['price'].transform('sum')
    rfm_df = df.groupby(by="customer_id", as_index=False).agg({
        "order_purchase_timestamp": "max", # mengambil tanggal order terakhir
        "order_id": "nunique",
        "total_price": "sum"
    })
    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]
    
    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df["order_purchase_timestamp"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)
    
    return rfm_df


# Memuat data dari file CSV yang telah dibersihkan
all_df = pd.read_csv("all_data.csv")

# Mendefinisikan kolom yang berisi tipe data datetime
datetime_columns = ["order_purchase_timestamp", "order_delivered_customer_date", "order_estimated_delivery_date"]
# Mengurutkan data berdasarkan tanggal pesanan
all_df.sort_values(by="order_purchase_timestamp", inplace=True)
all_df.reset_index(drop=True, inplace=True)
# Mengonversi kolom datetime menjadi tipe data datetime
for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column], errors='coerce')
# Verifikasi hasil konversi
print(all_df[datetime_columns].head())


# Langkah 3: Menambahkan widget date input di sidebar
st.sidebar.title("Nitaries Collection")

st.sidebar.image("2-removebg-preview.png", width=150)
st.write("")  # Add some whitespace
st.sidebar.write("Pilih Tanggal")
start_date = st.sidebar.date_input("Tanggal Mulai", all_df["order_purchase_timestamp"].min().date())
end_date = st.sidebar.date_input("Tanggal Akhir", all_df["order_purchase_timestamp"].max().date())

# Langkah 4: Memfilter data berdasarkan tanggal yang dipilih
filtered_df = all_df[(all_df["order_purchase_timestamp"].dt.date >= start_date) & 
                     (all_df["order_purchase_timestamp"].dt.date <= end_date)]

# Langkah 5: Membuat DataFrame yang dibutuhkan untuk visualisasi data
customer_profile = create_customer_profile_df(filtered_df)
daily_orders_df = create_daily_orders_df(filtered_df)
top_products = create_top_products_df(filtered_df)
customer_satisfaction = create_customer_satisfaction_df(filtered_df)
rfm_df = create_rfm_df(filtered_df)

# Langkah 6: Membuat visualisasi data
st.title("Nitaries Collection Dashboard :sparkles:")
st.write("")  # Add some whitespace
st.header("Daily Orders")
st.write("Berikut adalah jumlah pesanan dan total harga per hari yang telah difilter berdasarkan tanggal yang dipilih:")
# Create a figure with two subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 6))

# Bar chart for jumlah pesanan per hari
sns.lineplot(data=daily_orders_df, x='order_purchase_timestamp', y='order_count', color='skyblue', ax=ax1)
ax1.set_xlabel("Tanggal")
ax1.set_ylabel("Jumlah Pesanan")
ax1.set_title("Jumlah Pesanan per Hari")
ax1.tick_params(axis='x', rotation=45)

# Line chart for total harga per hari
sns.lineplot(data=daily_orders_df, x='order_purchase_timestamp', y='revenue', palette='Reds', ax=ax2)
ax2.set_xlabel("Tanggal")
ax2.set_ylabel("Total Harga")
ax2.set_title("Total Harga per Hari")
ax2.tick_params(axis='x', rotation=45)

# Show the plot
st.pyplot(fig)

# Top 10 Produk Paling Laris
st.header("Top 10 Produk Paling Laris")
st.write("")  # Add some whitespace

colors = cm.get_cmap("Purples")(np.linspace(0, 1, len(top_products)))
fig, ax = plt.subplots(figsize=(10, 6))
ax.pie(
    top_products['order_id'],
    labels=top_products['product_category_name'].astype(str).tolist(),
    autopct='%1.1f%%',
    startangle=90,
    colors=colors
)

# Top 10 Kota dengan Jumlah Pelanggan Terbanyak
st.header("Top 10 Kota dengan Jumlah Pelanggan Terbanyak")
st.write("")  # Add some whitespace

top_cities = customer_profile.sort_values('customer_count', ascending=False).head(10)
fig, ax = plt.subplots(figsize=(10, 6))
ax.bar(top_cities['customer_city'], top_cities['customer_count'], edgecolor='black', color='skyblue')
ax.set_xlabel("Kota")
ax.set_ylabel("Jumlah Pelanggan")
ax.set_title("Top 10 Kota dengan Jumlah Pelanggan Terbanyak")
plt.xticks(rotation=45)
st.pyplot(fig)

# Analisis RFM
st.header("Analisis RFM")
st.write("")  # Add some whitespace

fig, ax = plt.subplots(figsize=(10, 6))
sns.scatterplot(data=rfm_df, x='recency', y='frequency', hue='monetary', palette='Greens')
ax.set_xlabel("Recency")
ax.set_ylabel("Frequency")
ax.set_title("Analisis RFM")
st.pyplot(fig)

# Distribusi Skor Ulasan Pelanggan
st.header("Distribusi Skor Ulasan Pelanggan")
st.write("")  # Add some whitespace

fig, ax = plt.subplots(figsize=(10, 6))
sns.barplot(data=customer_satisfaction, x='review_score', y='order_id', palette='Blues')
ax.set_xlabel("Skor Ulasan")
ax.set_ylabel("Jumlah Pesanan")
ax.set_title("Distribusi Skor Ulasan Pelanggan")
st.pyplot(fig)
# Langkah 6: Membuat tabel untuk menampilkan data yang telah difilter
st.header("Tabel Data yang telah Difilter")
st.write(filtered_df)

# Langkah 7: Membuat tombol untuk mengunduh data yang telah difilter
st.write("Unduh Data yang telah Difilter")

@st.cache_data(ttl=3600)  # adjust the TTL (time to live) as needed
def convert_df_to_csv(filtered_df):
    return filtered_df.to_csv(index=False).encode('utf-8')

csv = convert_df_to_csv(filtered_df)

st.download_button(
    "Unduh Data",
    csv,
    "data.csv",
    "text/csv"
)