import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

# Load the CSV
file_path = "updated_city_post_comment_stats.csv"
df = pd.read_csv(file_path)

# Calculate sentiment score excluding neutral posts/comments
def compute_sentiment_score(row):
    pos_total = row['post_positive'] + row['comment_positive']
    neg_total = row['post_negative'] + row['comment_negative']
    denominator = pos_total + neg_total
    if denominator == 0:
        return 0  # avoid division by zero
    return (pos_total - neg_total) / denominator

# Apply the function to each row
df["sentiment_score"] = df.apply(compute_sentiment_score, axis=1)

# Save to a new CSV
output_path = "city_sentiment_scored.csv"
df.to_csv(output_path, index=False)

print(f"Sentiment scores added and saved to {output_path}")

# Create a list to store all sentiment values (comments and posts)
sentiment_data = []

for _, row in df.iterrows():
    city = row["city"]

    # Comment sentiments
    sentiment_data.extend([{"city": city, "type": "comment", "sentiment": 1}] * int(row["comment_positive"]))
    sentiment_data.extend([{"city": city, "type": "comment", "sentiment": -1}] * int(row["comment_negative"]))

    # Normalized post sentiment (excluding neutrals)
    pos = row["post_positive"]
    neg = row["post_negative"]
    total = pos + neg
    post_score = 0 if total == 0 else (pos - neg) / total

    sentiment_data.append({"city": city, "type": "post", "sentiment": post_score})

sentiment_df = pd.DataFrame(sentiment_data)

# Plotting
plt.figure(figsize=(16, 6))
sns.violinplot(data=sentiment_df, x="city", y="sentiment", inner=None, color="skyblue")
sns.stripplot(data=sentiment_df[sentiment_df["type"] == "post"], x="city", y="sentiment",
              color="red", size=6, jitter=False, label="Post Sentiment")
plt.xticks(rotation=45)
plt.title("Sentiment Distribution per City (Comment Violin + Post Dot)")
plt.ylabel("Sentiment Score")
plt.xlabel("City")
plt.legend(title="Type", loc='center left', bbox_to_anchor=(1.02, 0.5), borderaxespad=0)
plt.tight_layout()

# Save and Show
plt.savefig("violin_with_post_sentiment.png", dpi=300)
plt.show()