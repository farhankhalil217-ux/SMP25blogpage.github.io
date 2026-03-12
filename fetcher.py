import os, json, re
from datetime import datetime
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai

# ==========================================
# 1. CONFIGURATION & API KEYS
# ==========================================
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# ==========================================
# 2. SOLAR METRIX SEARCH QUERIES
# ==========================================
# The script will randomly pick one of these to search YouTube every day
SEARCH_QUERIES = [
    "utility scale solar O&M optimization",
    "solar P50 P90 yield analysis",
    "bifacial solar module performance tracking",
    "solar dynamic soiling losses",
    "inverter clipping and DC/AC ratio solar",
    "solar irradiance modeling physics"
]

# ==========================================
# 3. THE SOLAR ENGINEER PROMPT
# ==========================================
SYSTEM_PROMPT = """
You are a Senior Solar Performance Engineer and Technical Writer for 'Solar Metrix', an advanced SaaS platform for solar yield simulation and physics modeling. 

Your job is to write a highly technical, engaging, and professional blog post based on the provided video transcript. 

Target Audience: Solar asset managers, EPC engineers, and renewable energy investors.
Tone: Data-driven, authoritative, analytical, and slightly contrarian. Challenge outdated industry standards (like static degradation rates) and advocate for dynamic, data-driven modeling.

Guidelines:
1. Do not act like a generic AI. Write like an industry veteran.
2. Use proper markdown (## for headings, bold text, bullet points).
3. Do not include a main # title (the publisher script will handle it). Start immediately with an engaging introductory paragraph.
4. Naturally weave in concepts like P50/P90 probability, O&M costs, albedo, clipping, or satellite data where relevant.
5. Do not explicitly mention the YouTube video. Present these as your own original Solar Metrix engineering insights.
"""

def get_latest_video():
    import random
    query = random.choice(SEARCH_QUERIES)
    print(f"Searching YouTube for: {query}")
    
    request = youtube.search().list(
        q=query, part="snippet", type="video",
        maxResults=10, order="date", relevanceLanguage="en"
    )
    response = request.execute()
    
    # Load history
    history_file = "processed_videos.txt"
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            processed = f.read().splitlines()
    else:
        processed = []

    for item in response['items']:
        vid_id = item['id']['videoId']
        if vid_id not in processed:
            return vid_id, item['snippet']['title']
            
    return None, None

def get_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([t['text'] for t in transcript_list])
    except Exception as e:
        print(f"Transcript failed: {e}")
        return None

def generate_blog(title, transcript):
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    prompt = f"{SYSTEM_PROMPT}\n\nVideo Topic/Title: {title}\n\nTranscript Data to analyze:\n{transcript[:15000]}"
    
    response = model.generate_content(prompt)
    return response.text

def main():
    if not YOUTUBE_API_KEY or not GEMINI_API_KEY:
        print("Missing API Keys!")
        return

    os.makedirs("drafts", exist_ok=True)
    
    vid_id, title = get_latest_video()
    if not vid_id:
        print("No new solar videos found today.")
        return
        
    print(f"Found new video: {title}")
    transcript = get_transcript(vid_id)
    
    if not transcript:
        # Mark as processed even if it fails so it doesn't get stuck on a video with no captions
        with open("processed_videos.txt", "a") as f:
            f.write(vid_id + "\n")
        return

    print("Generating Solar Metrix Article...")
    blog_content = generate_blog(title, transcript)
    
    # Clean up title for filename
    safe_title = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"drafts/{date_str}-{safe_title[:40]}.md"
    
    # Prepend the title so publisher.py can read it
    final_file_content = f"# {title}\n\n{blog_content}"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(final_file_content)
        
    with open("processed_videos.txt", "a") as f:
        f.write(vid_id + "\n")
        
    print(f"Success! Saved to {filename}")

if __name__ == "__main__":
    main()
