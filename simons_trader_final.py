import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

st.set_page_config(layout="wide")
st.title("Sistema de Trading Estilo Jim Simons")

default_symbols = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META',
    'NVDA', 'TSLA', 'NFLX', 'JPM', 'BAC',
    'V', 'MA', 'UNH', 'HD', 'DIS',
    'XOM', 'CVX', 'BABA', 'INTC', 'AMD'
]

symbols = st.multiselect("Selecciona hasta 20 acciones para analizar:", default_symbols, default=default_symbols[:5], max_selections=20)

if symbols:
    start_date = st.date_input("Fecha de inicio", value=pd.to_datetime("2023-01-01"))
    end_date = st.date_input("Fecha de fin", value=pd.to_datetime("2025-01-01"))
    initial_capital = st.number_input("Capital inicial para backtest ($):", min_value=1000, value=10000, step=1000)

    sma_short_range = st.slider("Periodo de SMA Corta:", 5, 50, 20)
    sma_long_range = st.slider("Periodo de SMA Larga:", 20, 200, 50)
    rsi_lower = st.slider("Límite inferior RSI:", 0, 50, 30)
    rsi_upper = st.slider("Límite superior RSI:", 50, 100, 70)

    for symbol in symbols:
        st.subheader(f"Análisis de {symbol}")
        data = yf.download(symbol, start=start_date, end=end_date)

        if data.empty:
            st.warning(f"No se encontraron datos para {symbol}")
            continue

        data['SMA_Short'] = data['Close'].rolling(window=sma_short_range).mean()
        data['SMA_Long'] = data['Close'].rolling(window=sma_long_range).mean()
        data['Momentum'] = data['Close'] - data['Close'].shift(10)

        delta = data['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        data['RSI'] = 100 - (100 / (1 + rs))

        fig, ax = plt.subplots(figsize=(12, 4))
        ax.plot(data['Close'], label='Cierre')
        ax.plot(data['SMA_Short'], label=f'SMA {sma_short_range}')
        ax.plot(data['SMA_Long'], label=f'SMA {sma_long_range}')
        ax.set_title(f"Precio y Medias Móviles de {symbol}")
        ax.legend()
        st.pyplot(fig)

        # Gráfico de Momentum
        try:
            if 'Momentum' in data.columns:
                momentum_chart_data = data[['Momentum']].dropna()
                st.line_chart(momentum_chart_data)
        except:
            st.warning("No se pudo graficar Momentum")

        # Gráfico de RSI
        try:
            if 'RSI' in data.columns:
                rsi_chart_data = data[['RSI']].dropna()
                st.line_chart(rsi_chart_data)
        except:
            st.warning("No se pudo graficar RSI")

        # Señales
                 # Señales de compra
        data['Signal'] = 0
        data.loc[
            (data['SMA_Short'] > data['SMA_Long']) &
            (data['RSI'] < rsi_upper) &
            (data['RSI'] > rsi_lower),
            'Signal'
        ] = 1

        # Cálculo de retornos de la estrategia
        data['Strategy_Return'] = data['Signal'].shift(1).fillna(0) * data['Close'].pct_change().fillna(0)
        data['Cumulative_Return'] = (1 + data['Strategy_Return']).cumprod()
        data['Portfolio_Value'] = initial_capital * data['Cumulative_Return']

        st.write(data[['Signal', 'Close']].head())
        
        signal = data['Signal'].shift(1).fillna(0)
        returns = data['Close'].pct_change().fillna(0)
        strategy_return = pd.Series(signal.values * returns.values, index=data.index)
        data['Strategy_Return'] = strategy_return

        data['Cumulative_Return'] = (1 + data['Strategy_Return']).cumprod()
        data['Portfolio_Value'] = initial_capital * data['Cumulative_Return']

        st.line_chart(data[['Portfolio_Value']].dropna(), use_container_width=True)

        # Botón para descargar CSV
        download_data = data[['Close', 'SMA_Short', 'SMA_Long', 'Momentum', 'RSI',
                              'Signal', 'Strategy_Return', 'Cumulative_Return', 'Portfolio_Value']].dropna()
        csv = download_data.to_csv().encode('utf-8')
        st.download_button(
            label="📥 Descargar datos en CSV",
            data=csv,
            file_name=f'{symbol}_estrategia.csv',
            mime='text/csv'
        )

        last_signal = data['Signal'].iloc[-1]
        if last_signal == 1:
            st.success("🔔 Señal ACTUAL de COMPRA basada en SMA y RSI optimizados")
        else:
            st.info("📉 Sin señal de compra en este momento")

        st.markdown("---")
else:
    st.info("Selecciona al menos una acción para comenzar.")
