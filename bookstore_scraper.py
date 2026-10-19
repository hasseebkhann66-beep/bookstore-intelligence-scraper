"""
Assignment 2 - The Bookstore Intelligence Mission
Scrapes https://books.toscrape.com/ and answers all required questions.

Run:   python bookstore_scraper.py            (scrapes 5 pages: Bonus 1)
       python bookstore_scraper.py --pages 3  (minimum requirement)
       python bookstore_scraper.py --all      (BOSS LEVEL: all 50 pages)

Needs: pip install requests beautifulsoup4 pandas matplotlib numpy
Outputs: competitor_books.csv, rating_counts.png, answers.md
"""
import argparse
import re
import time
from urllib.parse import urljoin

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE = "https://books.toscrape.com/catalogue/"
RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

# ---------------------------------------------------------------- Mission 1
# Reconnaissance notes (what the HTML looks like):
#   Product card : <article class="product_pod">
#   Title        : <h3><a title="FULL TITLE">  (link text is truncated, so use the title attribute)
#   Price        : <p class="price_color">£51.77</p>
#   Rating       : <p class="star-rating Three">  (rating word is the 2nd CSS class)
#   Availability : <p class="instock availability"> In stock </p>
#   Product link : <h3><a href="...">  (relative URL)


# ------------------------------------------------------- Missions 2 and 3
def parse_page(html, page_url):
    """Parse one catalogue page into a list of dict records."""
    soup = BeautifulSoup(html, "html.parser")
    records = []
    for card in soup.select("article.product_pod"):
        link = card.h3.a
        price_text = card.select_one("p.price_color").get_text(strip=True)
        rating_word = [c for c in card.select_one("p.star-rating")["class"]
                       if c != "star-rating"][0]
        records.append({
            "Title": link["title"],
            "Price": float(re.search(r"\d+\.\d+", price_text).group()),
            "Rating": RATING_MAP[rating_word],
            "Availability": card.select_one("p.availability").get_text(strip=True),
            "URL": urljoin(page_url, link["href"]),
        })
    has_next = soup.select_one("li.next") is not None
    return records, has_next


def scrape(max_pages=None, delay=0.5):
    """Loop over catalogue pages (one reusable loop, no copy-paste)."""
    all_records, page = [], 1
    while max_pages is None or page <= max_pages:
        url = f"{BASE}page-{page}.html"
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            break
        resp.encoding = "utf-8"          # avoids 'Â£' encoding glitches
        records, has_next = parse_page(resp.text, url)
        all_records.extend(records)
        print(f"Page {page}: {len(records)} books")
        if not has_next:
            break
        page += 1
        time.sleep(delay)                # be polite to the server
    return pd.DataFrame(all_records)


# ------------------------------------------------------------ Final challenge
def best_basket(df, budget=100.0):
    """0/1 knapsack: maximise total stars within budget (prices in pence).
    Ties are broken in favour of the lower total cost."""
    cost = (df["Price"] * 100).round().astype(int).to_numpy()
    val = df["Rating"].to_numpy()
    B = int(round(budget * 100))
    n = len(df)
    dp = np.zeros(B + 1, dtype=np.int64)
    keep = np.zeros((n, B + 1), dtype=bool)
    for i in range(n):
        c, v = cost[i], val[i]
        if c > B:
            continue
        cand = dp[:B + 1 - c] + v
        better = cand > dp[c:]
        keep[i, c:] = better
        dp[c:] = np.where(better, cand, dp[c:])
    # smallest spend that reaches the maximum score
    b = int(np.argmax(dp == dp.max()))
    chosen = []
    for i in range(n - 1, -1, -1):
        if keep[i, b]:
            chosen.append(i)
            b -= cost[i]
    return df.iloc[sorted(chosen)]


# ------------------------------------------------------------------- Main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=5)
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    df = scrape(None if args.all else args.pages)
    df.to_csv("competitor_books.csv", index=False)
    print(df.head(), "\n", df.dtypes, "\nRows:", len(df))

    out = []  # lines for answers.md
    def say(s=""):
        out.append(s)

    say(f"# Intelligence Analysis ({len(df)} books scraped)\n")

    exp = df.loc[df["Price"].idxmax()]
    say(f"1. **Most expensive:** {exp.Title} - £{exp.Price:.2f}")
    chp = df.loc[df["Price"].idxmin()]
    say(f"2. **Cheapest:** {chp.Title} - £{chp.Price:.2f}")
    say(f"3. **Average price:** £{df.Price.mean():.2f}")
    five = df[df.Rating == 5]
    say(f"4. **5-star books:** {len(five)}")
    in_stock = df.Availability.str.contains("In stock", case=False).mean() * 100
    say(f"5. **In stock:** {in_stock:.1f}%")
    top5 = df.sort_values(["Rating", "Price"], ascending=[False, True]).head(5)
    say("6. **Top 5 highest-rated** (ties broken by lower price; many books share 5 stars):")
    for _, r in top5.iterrows():
        say(f"   - {r.Title} - {r.Rating} stars, £{r.Price:.2f}")
    c5 = five.loc[five.Price.idxmin()]
    say(f"7. **Cheapest 5-star book:** {c5.Title} - £{c5.Price:.2f}")

    # Bonus 3 + 4
    counts = df.Rating.value_counts().reindex([1, 2, 3, 4, 5], fill_value=0)
    say("\n## Bonus 3 - books per rating\n")
    for k, v in counts.items():
        say(f"- {k} star: {v}")
    ax = counts.plot(kind="bar", color="steelblue", rot=0)
    ax.set_xlabel("Star rating"); ax.set_ylabel("Number of books")
    ax.set_title("Books per star rating")
    plt.tight_layout(); plt.savefig("rating_counts.png", dpi=150); plt.close()

    # CEO challenge
    basket = best_basket(df, 100.0)
    say("\n## CEO £100 Challenge\n")
    say("| Title | Price (£) | Rating |\n|---|---|---|")
    for _, r in basket.iterrows():
        say(f"| {r.Title} | {r.Price:.2f} | {r.Rating} |")
    say(f"\n**Total cost: £{basket.Price.sum():.2f} | "
        f"Total rating score: {basket.Rating.sum()} | Books: {len(basket)}**")
    say("(Solved exactly with 0/1 knapsack dynamic programming, not a greedy guess.)")

    # Business evidence for the recommendation
    avg5 = five.Price.mean() if len(five) else float("nan")
    avg_all = df.Price.mean()
    low_cost_high_rated = df[(df.Rating >= 4) & (df.Price < avg_all)]
    say("\n## Evidence for recommendation\n")
    say(f"- Share of books rated 4-5 stars: {(df.Rating >= 4).mean()*100:.1f}%")
    say(f"- Average price of 5-star books £{avg5:.2f} vs overall £{avg_all:.2f}")
    say(f"- Books rated 4+ and priced below the average: {len(low_cost_high_rated)}")
    say("\n## Business recommendation (edit with your own numbers)\n")
    say(f"I would prioritise books rated 4-5 stars and priced below the market average "
        f"of £{avg_all:.2f}: there are {len(low_cost_high_rated)} such books in the scraped "
        f"data, so they combine proven customer appeal with a price advantage. "
        f"5-star books average £{avg5:.2f} versus £{avg_all:.2f} overall, which tells us "
        f"whether a price premium for quality exists, and {in_stock:.0f}% of the competitor "
        f"catalogue is in stock, so we should stock the same high-rated titles reliably.")

    with open("answers.md", "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print("\n".join(out))


if __name__ == "__main__":
    main()
