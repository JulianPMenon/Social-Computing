import json
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Add yars submodule to path
script_dir = os.path.dirname(os.path.abspath(__file__))
yars_path = os.path.join(script_dir, "yars", "yars")
sys.path.insert(0, yars_path)

from yars.src.yars.yars import YARS

def main():
    yars = YARS()
    subreddit = sys.argv[1] if len(sys.argv) > 1 else ""
    #subreddit = input("Enter subreddit name to scrape: ").strip()
    if not subreddit:
        print("Error: No subreddit name provided. Exiting.")
        sys.exit(1)
    limit = 50  # Number of posts to fetch
    posts = yars.fetch_subreddit_posts(subreddit, limit=limit, category="hot")
    print(f"Fetched {len(posts)} posts from r/{subreddit}")

    # For each post, fetch body and comments only
    post_details = []
    for post in posts:
        details = yars.scrape_post_details(post["permalink"])
        if details:
            post_details.append({
                "title": details["title"],
                "body": details["body"],
                "comments": details["comments"]
            })

    # Save to file with subreddit name in filename
    out_filename = f"{subreddit}_posts_text.json"
    with open(out_filename, "w", encoding="utf-8") as f:
        json.dump(post_details, f, ensure_ascii=False, indent=2)
    print(f"Saved scraped data to {out_filename}")

if __name__ == "__main__":
    main()

