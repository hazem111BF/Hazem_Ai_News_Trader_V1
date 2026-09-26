# Hazem AI News Trader V1

AI-powered XAUUSD trading alert system that combines real-time market data from MetaTrader 5, financial news analysis with Gemini AI, and Gmail notifications.

## Overview

Hazem AI News Trader V1 is a Python-based trading analysis system designed for XAUUSD (Gold).

The system:

- Collects real-time XAUUSD market data from MetaTrader 5
- Analyzes market conditions using technical indicators
- Collects recent financial news
- Uses Gemini AI to analyze financial news
- Combines market and news analysis into a final signal
- Sends new signals through Gmail
- Prevents duplicate Gmail alerts

## System Flow

```text
MetaTrader 5
     ↓
Market Data
     ↓
Market Analysis
     ↓
Financial News
     ↓
Gemini AI Analysis
     ↓
Signal Engine
     ↓
Signal Output
     ↓
Gmail Alert
```

## Main Technologies

- Python
- MetaTrader 5
- Gemini AI
- Google News RSS
- Gmail API
- Pandas
- Technical Analysis

## Current Status

**Version:** V1

**Mode:** Alert-Only / Demo Testing

The current version does **not** execute automatic trades.

Possible signals:

- BULLISH
- BEARISH
- NEUTRAL

The system is currently designed for analysis, testing, and alerts.

## Market Analysis

The market analysis component uses real-time XAUUSD data from MetaTrader 5.

The current analysis includes:

- EMA 20
- EMA 50
- ATR
- Price movement
- Candle structure

The market analyzer generates a market score representing the current technical conditions.

## News Analysis

The system collects recent financial news through Google News RSS.

Gemini AI analyzes the collected news and generates structured information including:

- News score
- Confidence
- Direction
- Time horizon
- Reason
- Key factors

The news analyzer also uses model fallback and retry handling to improve reliability when an AI model is temporarily unavailable.

## Signal Engine

The Signal Engine combines market analysis and news analysis.

Current weighting:

```text
Market Weight: 60%
News Weight:   40%
```

Conceptually:

```text
Final Score =
(Market Score × 0.60)
+
(Adjusted News Score × 0.40)
```

News confidence is considered when calculating the adjusted news contribution.

The final signal can be:

```text
BULLISH
BEARISH
NEUTRAL
```

## Gmail Alerts

Gmail is used as the notification system.

When a new signal is detected, the system can send an email containing information such as:

- Asset
- Direction
- Final score
- Market score
- News score
- News confidence
- Analysis reason

The system also includes duplicate alert protection.

## Security

Sensitive credentials are intentionally excluded from this repository.

The following files must remain local:

```text
.env
credentials.json
token.json
```

Never upload:

- API keys
- OAuth credentials
- OAuth tokens
- Gmail passwords
- MT5 account passwords
- Other private credentials

These files are excluded using `.gitignore`.

## Requirements

- Windows 10/11
- Python 3.12+
- MetaTrader 5
- MT5 demo account
- XAUUSD available through the broker
- Gemini API key
- Google account for Gmail API

## Installation

Clone the repository:

```bash
git clone https://github.com/hazem111BF/Hazem_Ai_News_Trader_V1.git
```

Enter the project directory:

```bash
cd Hazem_Ai_News_Trader_V1
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate the virtual environment on Windows:

```cmd
venv\Scripts\activate
```

Install the required Python packages:

```cmd
pip install -r requirements.txt
```

## Environment Configuration

Create a local `.env` file.

Example:

```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

Never commit the real `.env` file to GitHub.

## MetaTrader 5 Setup

1. Install MetaTrader 5.
2. Log in to your demo account.
3. Make sure XAUUSD is available.
4. Keep MetaTrader 5 running while using the system.
5. Make sure the Python environment can connect to MetaTrader 5.

The current version is designed for analysis and alert generation.

## Gmail API Setup

To enable Gmail alerts:

1. Create a Google Cloud project.
2. Enable the Gmail API.
3. Configure the OAuth consent screen.
4. Create a Desktop OAuth Client.
5. Download the OAuth credentials.
6. Save the credentials locally as:

```text
credentials.json
```

7. Run the Gmail test/setup script.
8. Authenticate with the Gmail account that should receive alerts.

After authentication, Google creates:

```text
token.json
```

Keep this file local and never upload it to GitHub.

## Running the System

Activate the virtual environment:

```cmd
venv\Scripts\activate
```

Run the complete system:

```cmd
python -u run_trader.py
```

The system will:

1. Connect to MetaTrader 5
2. Retrieve XAUUSD market data
3. Analyze market conditions
4. Retrieve financial news
5. Analyze news using Gemini AI
6. Calculate the final signal
7. Save the generated signal
8. Send a Gmail alert when a new signal is detected

## Testing

Test MetaTrader 5:

```cmd
python -u test_mt5.py
```

Test Gemini:

```cmd
python -u test_gemini.py
```

Test market data:

```cmd
python -u market_data.py
```

Test market analysis:

```cmd
python -u market_analyzer.py
```

Test financial news:

```cmd
python -u news_feed.py
```

## Project Structure

```text
Hazem_Ai_News_Trader_V1/
│
├── market_data.py
├── market_analyzer.py
│
├── news_feed.py
├── news_analyzer.py
├── real_news_analyzer.py
│
├── signal_engine.py
│
├── gmail_alert.py
├── send_signal_email.py
├── gmail_signal_bridge.py
│
├── run_trader.py
│
├── test_mt5.py
├── test_gemini.py
│
├── .gitignore
├── README.md
└── requirements.txt
```

Sensitive local files such as `.env`, `credentials.json`, and `token.json` are intentionally excluded from the repository.

## Current Safety Mode

The current version operates in:

**ALERT-ONLY MODE**

The system does not:

- Automatically open trades
- Automatically close trades
- Execute MT5 orders
- Manage live positions
- Trade real capital automatically

The current objective is to validate the system using real market data, financial news, AI analysis, and demo testing.

## Development Roadmap

Future development may include:

- Historical signal logging
- Forward testing
- Signal performance analysis
- More comprehensive market-regime detection
- Additional financial news sources
- Improved signal validation
- Walk-forward testing
- Paper-trading integration
- Additional risk-management research

Automatic trading should only be considered after extensive testing and validation.

## Disclaimer

This project is provided for educational, research, and software-development purposes.

It is not financial advice and does not guarantee profitable trading results.

Trading financial markets involves significant risk.

The current version is an alert-only system and does not execute trades automatically.

## Author

**Hazem Benfraj**

**Hazem AI News Trader V1**