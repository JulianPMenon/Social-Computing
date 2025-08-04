import json
from collections import Counter


# Set this to your city subreddit name (case-sensitive, no /r/)
CITY_SUBREDDIT = "pauper"
INPUT_FILE = f"{CITY_SUBREDDIT}_posts_sentiment.json"

# Load sentiment data
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    posts = json.load(f)

# Metrics to calculate:
# 1. Number of posts per sentiment
# 2. Number of comments per sentiment
# 3. Overall sentiment distribution (posts + comments)
# 4. Average number of comments per post
# 5. Percentage of positive, neutral, negative posts/comments

post_sentiments = [post.get("post_sentiment", "neutral") for post in posts]
comment_sentiments = []
num_comments = []
for post in posts:
    comments = post.get("comments", [])
    num_comments.append(len(comments))
    for c in comments:
        comment_sentiments.append(c.get("sentiment", "neutral"))

# Count sentiments
post_counts = Counter(post_sentiments)
comment_counts = Counter(comment_sentiments)
total_counts = Counter(post_sentiments + comment_sentiments)

total_posts = len(posts)
total_comments = len(comment_sentiments)
total_items = total_posts + total_comments

avg_comments_per_post = sum(num_comments) / total_posts if total_posts else 0


# Percentages
post_percent = {k: v / total_posts * 100 for k, v in post_counts.items()}
comment_percent = {k: v / total_comments * 100 for k, v in comment_counts.items()}
total_percent = {k: v / total_items * 100 for k, v in total_counts.items()}

# Sentiment score mapping
sentiment_score = {"negative": -1, "neutral": 0, "positive": 1}

# Mean score per post for related comments
mean_comment_scores = []
for post in posts:
    comments = post.get("comments", [])
    scores = [sentiment_score.get(c.get("sentiment", "neutral"), 0) for c in comments]
    mean_score = sum(scores) / len(scores) if scores else None
    mean_comment_scores.append(mean_score)

print("Mean sentiment score per post (comments only):")
for idx, score in enumerate(mean_comment_scores):
    print(f"Post {idx+1}: {score}")

print("--- Sentiment Metrics ---")
print(f"Total posts: {total_posts}")
print(f"Total comments: {total_comments}")
print(f"Average comments per post: {avg_comments_per_post:.2f}")
print()
print("Posts sentiment counts:", post_counts)
print("Posts sentiment percentages:", post_percent)
print()
print("Comments sentiment counts:", comment_counts)
print("Comments sentiment percentages:", comment_percent)
print()
print("Overall sentiment counts:", total_counts)
print("Overall sentiment percentages:", total_percent)
