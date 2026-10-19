# bookstore-intelligence-scraper
Python web scraper (requests + BeautifulSoup + pandas) that turns books.toscrape.com into a clean dataset, then analyses prices and ratings and solves a £100 purchasing challenge.
I just built a web scraper that turns a competitor's online bookstore into a clean business dataset, and then used it to decide what a new bookstore should sell. 📚

Here's how it works:

1️⃣ Inspect the page: I found the title, price, star rating and stock status in the HTML (class names like price_color and star-rating).
2️⃣ Request + parse: Python's requests downloads each page and BeautifulSoup pulls out every book card.
3️⃣ Clean: star ratings are stored as words ("Three", "Five"), so I converted them to numbers 1–5 and prices to floats.
4️⃣ Scale: one reusable loop follows the "next" button through the catalogue, no copy-pasted code, with a short delay to be polite to the server.
5️⃣ Analyse: Pandas answers the business questions: priciest and cheapest books, average price, share in stock, rating distribution.
6️⃣ Optimise: given a £100 budget, a knapsack algorithm picks the books that maximise total star rating.

Biggest lesson: scraping is the easy part. The value comes from cleaning the data and turning it into a decision.


(Practiced on books.toscrape.com, a sandbox built for scraping.)

#Python #WebScraping #DataAnalytics #Pandas #BeautifulSoup #TextMining #DataScience
