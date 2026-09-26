import subprocess
import sys
import json
import os
from datetime import datetime, timezone


# ============================================================
# CONFIGURATION
# ============================================================

MARKET_WEIGHT = 0.60
NEWS_WEIGHT = 0.40

BUY_THRESHOLD = 60
SELL_THRESHOLD = -60

MIN_NEWS_CONFIDENCE = 60

OUTPUT_FILE = "latest_signal.json"


# ============================================================
# RUN MARKET ANALYZER
# ============================================================

def run_market_analyzer():

    print("=" * 65)
    print("RUNNING MARKET ANALYZER...")
    print("=" * 65)

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    try:

        result = subprocess.run(
            [sys.executable, "market_analyzer.py"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env
        )

    except Exception as e:

        print()
        print("MARKET ANALYZER FAILED:")
        print(e)

        return ""

    print(result.stdout)

    if result.returncode != 0:

        print("MARKET ANALYZER ERROR:")
        print(result.stderr)

    return result.stdout


# ============================================================
# RUN NEWS ANALYZER
# ============================================================

def run_news_analyzer():

    print("=" * 65)
    print("RUNNING NEWS ANALYZER...")
    print("=" * 65)

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    try:

        result = subprocess.run(
            [sys.executable, "news_analyzer.py"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env
        )

    except Exception as e:

        print()
        print("NEWS ANALYZER FAILED:")
        print(e)

        return ""

    print(result.stdout)

    if result.returncode != 0:

        print("NEWS ANALYZER ERROR:")
        print(result.stderr)

    return result.stdout


# ============================================================
# EXTRACT MARKET SCORE
# ============================================================

def extract_market_score(output):

    for line in output.splitlines():

        if "MARKET SCORE:" in line:

            try:

                value = line.split(
                    "MARKET SCORE:"
                )[-1].strip()

                return int(float(value))

            except ValueError:

                return None

    return None


# ============================================================
# EXTRACT NEWS JSON
# ============================================================

def extract_news_json(output):

    if not output:

        return None

    # --------------------------------------------------------
    # Try every JSON-looking block
    # --------------------------------------------------------

    start_positions = []

    for i, char in enumerate(output):

        if char == "{":

            start_positions.append(i)

    for start in start_positions:

        depth = 0
        in_string = False
        escape = False

        for i in range(
            start,
            len(output)
        ):

            char = output[i]

            if in_string:

                if escape:

                    escape = False

                elif char == "\\":

                    escape = True

                elif char == '"':

                    in_string = False

                continue

            if char == '"':

                in_string = True

            elif char == "{":

                depth += 1

            elif char == "}":

                depth -= 1

                if depth == 0:

                    candidate = output[
                        start:i + 1
                    ]

                    try:

                        data = json.loads(
                            candidate
                        )

                        if (
                            isinstance(data, dict)
                            and "news_score" in data
                        ):

                            return data

                    except json.JSONDecodeError:

                        pass

                    break

    return None


# ============================================================
# VALIDATE NEWS RESULT
# ============================================================

def validate_news_result(news):

    if not isinstance(
        news,
        dict
    ):

        return False

    required = [
        "asset",
        "direction",
        "news_score",
        "confidence"
    ]

    for field in required:

        if field not in news:

            return False

    if news["asset"] != "XAUUSD":

        return False

    if news["direction"] not in [
        "BULLISH",
        "BEARISH",
        "NEUTRAL"
    ]:

        return False

    try:

        score = float(
            news["news_score"]
        )

        confidence = float(
            news["confidence"]
        )

    except:

        return False

    if not -100 <= score <= 100:

        return False

    if not 0 <= confidence <= 100:

        return False

    return True


# ============================================================
# CONFIDENCE ADJUSTMENT
# ============================================================

def adjust_news_score(
    news_score,
    confidence
):

    """
    Reduce the impact of news when confidence is low.

    Example:

    Score +80
    Confidence 50%

    Adjusted score = +40
    """

    adjusted = (
        news_score *
        (confidence / 100)
    )

    return round(
        adjusted,
        2
    )


# ============================================================
# FINAL SCORE
# ============================================================

def calculate_final_score(
    market_score,
    news_score,
    confidence
):

    adjusted_news = adjust_news_score(
        news_score,
        confidence
    )

    final_score = (
        market_score * MARKET_WEIGHT
        +
        adjusted_news * NEWS_WEIGHT
    )

    final_score = max(
        -100,
        min(
            100,
            final_score
        )
    )

    return round(
        final_score,
        2
    )


# ============================================================
# FINAL DIRECTION
# ============================================================

def determine_direction(
    final_score,
    news_confidence
):

    # --------------------------------------------------------
    # Low confidence = neutral
    # --------------------------------------------------------

    if news_confidence < MIN_NEWS_CONFIDENCE:

        return "NEUTRAL"

    # --------------------------------------------------------
    # Strong bullish
    # --------------------------------------------------------

    if final_score >= BUY_THRESHOLD:

        return "BULLISH"

    # --------------------------------------------------------
    # Strong bearish
    # --------------------------------------------------------

    if final_score <= SELL_THRESHOLD:

        return "BEARISH"

    # --------------------------------------------------------
    # Otherwise neutral
    # --------------------------------------------------------

    return "NEUTRAL"


# ============================================================
# SAVE SIGNAL
# ============================================================

def save_signal(data):

    try:

        with open(
            OUTPUT_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False
            )

        print()
        print(
            "Signal saved to:",
            OUTPUT_FILE
        )

    except Exception as e:

        print()
        print(
            "Could not save signal:"
        )

        print(e)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 65)
    print("HAZEM AI NEWS TRADER - SIGNAL ENGINE V2")
    print("=" * 65)

    # ========================================================
    # MARKET
    # ========================================================

    market_output = run_market_analyzer()

    market_score = extract_market_score(
        market_output
    )

    if market_score is None:

        print()
        print("=" * 65)
        print(
            "ERROR: Could not extract MARKET SCORE"
        )
        print("=" * 65)

        return

    # ========================================================
    # NEWS
    # ========================================================

    news_output = run_news_analyzer()

    news_result = extract_news_json(
        news_output
    )

    if not validate_news_result(
        news_result
    ):

        print()
        print("=" * 65)
        print(
            "ERROR: Could not extract valid NEWS JSON"
        )
        print("=" * 65)

        return

    # ========================================================
    # NEWS VALUES
    # ========================================================

    news_score = float(
        news_result.get(
            "news_score",
            0
        )
    )

    news_direction = news_result.get(
        "direction",
        "NEUTRAL"
    )

    news_confidence = float(
        news_result.get(
            "confidence",
            0
        )
    )

    time_horizon = news_result.get(
        "time_horizon",
        "UNCLEAR"
    )

    reason = news_result.get(
        "reason",
        ""
    )

    key_factors = news_result.get(
        "key_factors",
        []
    )

    # ========================================================
    # ADJUST NEWS
    # ========================================================

    adjusted_news_score = adjust_news_score(
        news_score,
        news_confidence
    )

    # ========================================================
    # FINAL SCORE
    # ========================================================

    final_score = calculate_final_score(
        market_score,
        news_score,
        news_confidence
    )

    final_direction = determine_direction(
        final_score,
        news_confidence
    )

    # ========================================================
    # TIMESTAMP
    # ========================================================

    timestamp = datetime.now(
        timezone.utc
    ).isoformat()

    # ========================================================
    # FINAL RESULT
    # ========================================================

    signal = {

        "asset": "XAUUSD",

        "timestamp_utc": timestamp,

        "market_score": market_score,

        "news_score": news_score,

        "news_confidence": news_confidence,

        "adjusted_news_score":
            adjusted_news_score,

        "final_score": final_score,

        "market_weight": MARKET_WEIGHT,

        "news_weight": NEWS_WEIGHT,

        "direction": final_direction,

        "news_direction": news_direction,

        "time_horizon": time_horizon,

        "reason": reason,

        "key_factors": key_factors
    }

    # ========================================================
    # DISPLAY
    # ========================================================

    print()
    print("=" * 65)
    print("FINAL SIGNAL")
    print("=" * 65)

    print(
        "Asset:",
        signal["asset"]
    )

    print()

    print(
        "MARKET SCORE:",
        market_score
    )

    print(
        "NEWS SCORE:",
        news_score
    )

    print(
        "NEWS CONFIDENCE:",
        news_confidence
    )

    print(
        "ADJUSTED NEWS SCORE:",
        adjusted_news_score
    )

    print()

    print(
        "MARKET WEIGHT:",
        MARKET_WEIGHT
    )

    print(
        "NEWS WEIGHT:",
        NEWS_WEIGHT
    )

    print()

    print(
        "FINAL SCORE:",
        final_score
    )

    print(
        "FINAL DIRECTION:",
        final_direction
    )

    print()

    print(
        "NEWS DIRECTION:",
        news_direction
    )

    print(
        "TIME HORIZON:",
        time_horizon
    )

    print()

    print(
        "NEWS REASON:"
    )

    print(
        reason
    )

    print()

    print("=" * 65)

    if final_direction == "BULLISH":

        print(
            "SIGNAL STATUS: BULLISH"
        )

    elif final_direction == "BEARISH":

        print(
            "SIGNAL STATUS: BEARISH"
        )

    else:

        print(
            "SIGNAL STATUS: NEUTRAL"
        )

    print("=" * 65)

    # ========================================================
    # SAVE
    # ========================================================

    save_signal(signal)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()