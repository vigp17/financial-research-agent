"""
HMM Regime Detection Tool — Connects the Market Regime Detection project
to the Financial Research Agent.

This tool loads your pre-trained HMM model and scaler, fetches recent
market data, computes the same 5 features your model was trained on,
and predicts the current market regime.

Features (must match training exactly):
  1. log_return    — daily log return
  2. vol_21d       — 21-day rolling std of log returns
  3. vol_ratio     — vol_5d / vol_21d (short vs long-term volatility)
  4. rsi           — 14-day Relative Strength Index
  5. ma_distance   — (Close - SMA20) / SMA20
"""

import os
import pickle
import numpy as np
import pandas as pd
import yfinance as yf

# === CONFIGURATION ===
# Path to your HMM project's saved models
# Update this if your project is in a different location
HMM_PROJECT_PATH = os.path.expanduser("~/Desktop/MLProjects/market-regime-detection")
MODEL_PATH = os.path.join(HMM_PROJECT_PATH, "models", "hmm_model.pkl")
SCALER_PATH = os.path.join(HMM_PROJECT_PATH, "models", "scaler.pkl")

# Regime labels — mapped from your project's regime characteristics
# These are ordered by the regime number from your trained model (0-4)
# You may need to adjust these labels based on your model's output
REGIME_LABELS = {
    0: "Strong Bull",
    1: "Calm Bull",
    2: "Neutral",
    3: "Bear / High Volatility",
    4: "Crisis",
}


# === TOOL SCHEMA ===

REGIME_TOOL_SCHEMA = {
    "name": "detect_market_regime",
    "description": (
        "Detect the current market regime using a pre-trained Hidden Markov Model. "
        "The HMM was trained on 20 years of S&P 500 data and identifies 5 regimes: "
        "Strong Bull, Calm Bull, Neutral, Bear/High Volatility, and Crisis. "
        "Returns the current regime, regime probabilities, and recent regime history. "
        "Use this tool to add regime context to any stock or market analysis."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": (
                    "Ticker to analyze. Default 'SPY' (S&P 500 ETF) since the model "
                    "was trained on S&P 500 data. Using SPY gives the most accurate "
                    "regime detection. Other tickers can be used but results are "
                    "approximate since the model was calibrated to S&P 500 dynamics."
                ),
            }
        },
        "required": [],
    },
}


# === FEATURE ENGINEERING ===
# These must EXACTLY match how features were computed during training

def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the 5 features the HMM model expects.
    Must match src/features.py from the training pipeline exactly.
    """
    # Feature 1: Log return
    df["log_return"] = np.log(df["Close"] / df["Close"].shift(1))

    # Volatility features (from volatility.py)
    df["vol_5d"] = df["log_return"].rolling(5).std()
    df["vol_21d"] = df["log_return"].rolling(21).std()

    # Feature 3: Volatility ratio (short-term vs long-term)
    df["vol_ratio"] = df["vol_5d"] / df["vol_21d"]

    # Feature 4: RSI (14-day)
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df["rsi"] = 100 - (100 / (1 + rs))

    # Feature 5: Distance from 20-day moving average
    ma_20 = df["Close"].rolling(20).mean()
    df["ma_distance"] = (df["Close"] - ma_20) / ma_20

    # Drop NaN rows (need at least 63 days of data for all features)
    df = df.dropna()

    return df


# === TOOL HANDLER ===

def detect_market_regime(ticker: str = "SPY") -> dict:
    """
    Load the pre-trained HMM model and predict the current market regime.
    """
    # --- Step 1: Check if model files exist ---
    if not os.path.exists(MODEL_PATH):
        return {
            "error": f"HMM model not found at {MODEL_PATH}. "
            f"Make sure the market-regime-detection project is at {HMM_PROJECT_PATH}"
        }
    if not os.path.exists(SCALER_PATH):
        return {
            "error": f"Scaler not found at {SCALER_PATH}. "
            f"Make sure the market-regime-detection project is at {HMM_PROJECT_PATH}"
        }

    try:
        # --- Step 2: Load the pre-trained model and scaler ---
        with open(MODEL_PATH, "rb") as f:
            hmm_model = pickle.load(f)
        with open(SCALER_PATH, "rb") as f:
            scaler = pickle.load(f)

        # --- Step 3: Fetch recent market data ---
        # Need enough history for rolling calculations (63+ days)
        stock = yf.Ticker(ticker)
        df = stock.history(period="6mo")

        if df.empty:
            return {"error": f"No data found for ticker '{ticker}'"}

        # --- Step 4: Compute features (same as training pipeline) ---
        feature_cols = ["log_return", "vol_21d", "vol_ratio", "rsi", "ma_distance"]
        df = compute_features(df)

        if len(df) < 10:
            return {"error": "Not enough data after feature computation"}

        # --- Step 5: Scale features using the SAME scaler from training ---
        X = scaler.transform(df[feature_cols])

        # --- Step 6: Predict regimes ---
        regimes = hmm_model.predict(X)
        regime_probs = hmm_model.predict_proba(X)

        # Current regime (most recent trading day)
        current_regime = int(regimes[-1])
        current_probs = regime_probs[-1]

        # Get number of states from the model
        n_states = hmm_model.n_components

        # Build regime labels (adjust if model has different number of states)
        labels = {}
        if n_states == 5:
            labels = REGIME_LABELS
        else:
            # Generic labels if model has different number of states
            labels = {i: f"Regime {i}" for i in range(n_states)}

        # --- Step 7: Build the result ---
        current_label = labels.get(current_regime, f"Regime {current_regime}")

        # Regime probabilities
        prob_breakdown = {
            labels.get(i, f"Regime {i}"): round(float(current_probs[i]) * 100, 1)
            for i in range(n_states)
        }

        # Recent regime history (last 10 trading days)
        recent_regimes = []
        for i in range(-min(10, len(regimes)), 0):
            date = df.index[i].strftime("%Y-%m-%d")
            regime = int(regimes[i])
            recent_regimes.append({
                "date": date,
                "regime": labels.get(regime, f"Regime {regime}"),
            })

        # Current market features (for context)
        latest = df.iloc[-1]
        current_features = {
            "log_return": round(float(latest["log_return"]) * 100, 3),
            "volatility_21d": round(float(latest["vol_21d"]) * 100, 2),
            "vol_ratio": round(float(latest["vol_ratio"]), 3),
            "rsi": round(float(latest["rsi"]), 1),
            "ma_distance_pct": round(float(latest["ma_distance"]) * 100, 2),
        }

        # Regime stability (how many of last 10 days in same regime)
        last_10 = regimes[-10:]
        stability = int(np.sum(last_10 == current_regime))

        # Transition matrix from the model
        transition_matrix = {}
        for i in range(n_states):
            from_label = labels.get(i, f"Regime {i}")
            transition_matrix[from_label] = {
                labels.get(j, f"Regime {j}"): round(float(hmm_model.transmat_[i, j]) * 100, 1)
                for j in range(n_states)
            }

        return {
            "ticker": ticker.upper(),
            "model_info": f"Gaussian HMM with {n_states} states, trained on 20 years of S&P 500 data",
            "current_regime": current_label,
            "regime_confidence_pct": prob_breakdown,
            "regime_stability": f"{stability}/10 days in current regime",
            "current_features": current_features,
            "recent_regime_history": recent_regimes,
            "transition_probabilities_from_current": transition_matrix.get(current_label, {}),
            "note": (
                "Regime detection is most accurate for SPY (S&P 500) since the model "
                "was trained on S&P 500 data. Results for other tickers are approximate."
                if ticker.upper() != "SPY"
                else "Model is running on its native index (S&P 500) — highest accuracy."
            ),
        }

    except Exception as e:
        return {"error": f"Regime detection failed: {str(e)}"}
