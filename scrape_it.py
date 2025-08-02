import json
import os
import sys
import time
import random
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
# Add yars submodule to path
script_dir = os.path.dirname(os.path.abspath(__file__))
yars_path = os.path.join(script_dir, "yars", "yars")
sys.path.insert(0, yars_path)
from yars.src.yars.yars import YARS

def exponential_backoff(attempt, base_delay=1, max_delay=300):
    """Calculate exponential backoff delay with jitter"""
    delay = min(base_delay * (2 ** attempt), max_delay)
    # Add random jitter to avoid thundering herd
    jitter = random.uniform(0.1, 0.3) * delay
    return delay + jitter

def safe_request_with_retry(func, *args, max_retries=5, **kwargs):
    """Execute a function with exponential backoff retry logic"""
    for attempt in range(max_retries):
        try:
            result = func(*args, **kwargs)
            if result:  # If we got data, return it
                return result
            # If no data but no exception, wait and retry
            if attempt < max_retries - 1:
                delay = exponential_backoff(attempt)
                print(f"No data returned, retrying in {delay:.1f}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
        except Exception as e:
            if "rate limit" in str(e).lower() or "429" in str(e):
                if attempt < max_retries - 1:
                    delay = exponential_backoff(attempt, base_delay=60)  # Longer delay for rate limits
                    print(f"Rate limit hit, waiting {delay:.1f}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                else:
                    print(f"Max retries reached for rate limit: {e}")
                    return None
            else:
                print(f"Error occurred: {e}")
                if attempt < max_retries - 1:
                    delay = exponential_backoff(attempt)
                    time.sleep(delay)
                else:
                    return None
    return None

def prioritize_posts(posts, max_posts=1000):
    """Prioritize posts based on engagement metrics for sentiment analysis"""
    def calculate_importance_score(post):
        # Combine upvotes, comments, and awards for importance
        upvotes = post.get('upvotes', 0) or 0
        num_comments = post.get('num_comments', 0) or 0
        awards = post.get('total_awards_received', 0) or 0
        
        # Weighted scoring - comments are valuable for sentiment analysis
        score = upvotes + (num_comments * 3) + (awards * 10)
        return score
    
    # Sort by importance score
    sorted_posts = sorted(posts, key=calculate_importance_score, reverse=True)
    return sorted_posts[:max_posts]

def save_checkpoint(data, filename):
    """Save progress to avoid losing data on failures"""
    checkpoint_file = f"checkpoint_{filename}"
    with open(checkpoint_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Checkpoint saved to {checkpoint_file}")

def load_checkpoint(filename):
    """Load previous progress if available"""
    checkpoint_file = f"checkpoint_{filename}"
    if os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"Loaded checkpoint with {len(data)} posts")
            return data
        except:
            print("Failed to load checkpoint, starting fresh")
    return []

def main():
    yars = YARS()
    subreddit = sys.argv[1] if len(sys.argv) > 1 else ""
    
    if not subreddit:
        print("Error: No subreddit name provided. Exiting.")
        sys.exit(1)
    
    # Parameters
    initial_limit = 700  # Fetch more initially to have options for prioritization
    target_posts = 500   # Final number we want
    
    out_filename = f"{subreddit}_posts_text.json"
    
    # Check for existing checkpoint
    post_details = load_checkpoint(out_filename)
    
    if not post_details:  # If no checkpoint, fetch posts
        print(f"Fetching posts from r/{subreddit}...")
        
        # Try different categories to get diverse, important content
        categories = ["hot", "top"]  # Start with hot and top posts
        all_posts = []
        
        for category in categories:
            print(f"Fetching {category} posts...")
            posts = safe_request_with_retry(
                yars.fetch_subreddit_posts, 
                subreddit, 
                limit=initial_limit//len(categories), 
                category=category
            )
            
            if posts:
                all_posts.extend(posts)
                print(f"Fetched {len(posts)} {category} posts")
            
            # Rate limiting between categories
            time.sleep(random.uniform(2, 5))
        
        if not all_posts:
            print("Failed to fetch any posts. Exiting.")
            sys.exit(1)
        
        # Remove duplicates and prioritize
        seen_ids = set()
        unique_posts = []
        for post in all_posts:
            post_id = post.get('id', post.get('permalink', ''))
            if post_id not in seen_ids:
                seen_ids.add(post_id)
                unique_posts.append(post)
        
        print(f"Found {len(unique_posts)} unique posts")
        
        # Prioritize posts for sentiment analysis
        prioritized_posts = prioritize_posts(unique_posts, target_posts)
        print(f"Selected top {len(prioritized_posts)} posts for detailed scraping")
        
        # Scrape post details with rate limiting
        batch_size = 10  # Process in small batches
        for i in range(0, len(prioritized_posts), batch_size):
            batch = prioritized_posts[i:i+batch_size]
            print(f"Processing batch {i//batch_size + 1}/{(len(prioritized_posts)-1)//batch_size + 1}")
            
            for j, post in enumerate(batch):
                print(f"Scraping post {i+j+1}/{len(prioritized_posts)}: {post.get('title', 'Unknown')[:50]}...")
                
                details = safe_request_with_retry(
                    yars.scrape_post_details, 
                    post["permalink"]
                )
                
                if details:
                    post_details.append({
                        "title": details["title"],
                        "body": details["body"],
                        "comments": details["comments"],
                        "upvotes": post.get('upvotes', 0),
                        "num_comments": post.get('num_comments', 0),
                        "created_utc": post.get('created_utc', 0),
                        "permalink": post.get('permalink', '')
                    })
                    
                    # Save checkpoint every 10 posts
                    if len(post_details) % 10 == 0:
                        save_checkpoint(post_details, out_filename)
                
                # Rate limiting between posts
                time.sleep(random.uniform(1, 3))
            
            # Longer break between batches
            if i + batch_size < len(prioritized_posts):
                batch_delay = random.uniform(10, 20)
                print(f"Batch complete. Waiting {batch_delay:.1f}s before next batch...")
                time.sleep(batch_delay)
    
    # Save final results
    if post_details:
        with open(out_filename, "w", encoding="utf-8") as f:
            json.dump(post_details, f, ensure_ascii=False, indent=2)
        
        # Clean up checkpoint
        checkpoint_file = f"checkpoint_{out_filename}"
        if os.path.exists(checkpoint_file):
            os.remove(checkpoint_file)
        
        print(f"\nScraping complete!")
        print(f"Saved {len(post_details)} posts to {out_filename}")
        print(f"Data ready for sentiment analysis")
    else:
        print("No data was successfully scraped.")

if __name__ == "__main__":
    main()