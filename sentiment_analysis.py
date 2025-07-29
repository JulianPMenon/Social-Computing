import json
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification


# Set this to your city subreddit name (case-sensitive, no /r/)
CITY_SUBREDDIT = "pauper"
INPUT_FILE = f"{CITY_SUBREDDIT}_posts_text.json"
OUTPUT_FILE = f"{CITY_SUBREDDIT}_posts_sentiment.json"


# Load XLM-RoBERTa sentiment model
MODEL_NAME = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)


def rate_sentiment(text):
    if not text:
        return "neutral"
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=256)
    with torch.no_grad():
        outputs = model(**inputs)
        scores = outputs.logits.softmax(dim=1).squeeze().tolist()
        # XLM-RoBERTa: [negative, neutral, positive]
        sentiment_idx = scores.index(max(scores))
        if sentiment_idx == 0:
            return "negative"
        elif sentiment_idx == 1:
            return "neutral"
        else:
            return "positive"

def analyze_posts():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        posts = json.load(f)
    results = []
    for post in posts:
        post_text = post.get("body", "")
        post_sentiment = rate_sentiment(post_text)
        comments = post.get("comments", [])
        comment_sentiments = []
        def collect_comments(comments):
            sentiments = []
            for c in comments:
                body = c.get("body", "")
                sentiment = rate_sentiment(body)
                sentiments.append({"body": body, "sentiment": sentiment})
                if c.get("replies"):
                    sentiments.extend(collect_comments(c["replies"]))
            return sentiments
        comment_sentiments = collect_comments(comments)
        results.append({
            "title": post.get("title", ""),
            "body": post_text,
            "post_sentiment": post_sentiment,
            "comments": comment_sentiments
        })
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Sentiment analysis complete. Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    analyze_posts()
