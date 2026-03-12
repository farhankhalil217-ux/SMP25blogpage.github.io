print("VERSION 18.0 - SOLAR METRIX (NEW GENAI SDK)")
import os, json, re, random, hashlib
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from google import genai

# ==========================================
# 1. CONFIGURATION & API KEYS
# ==========================================
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
client = genai.Client(api_key=GEMINI_API_KEY)

SEARCH_QUERIES = [
    "utility scale solar O&M optimization",
    "solar P50 P90 yield analysis",
    "bifacial solar module performance tracking",
    "solar dynamic soiling losses",
    "inverter clipping and DC/AC ratio solar",
    "solar irradiance modeling physics"
]

# ==========================================
# 2. THE SOLAR ENGINEER PROMPT
# ==========================================
SYSTEM_PROMPT = """
You are a Senior Solar Performance Engineer and Technical Writer for 'Solar Metrix', an advanced SaaS platform for solar yield simulation and physics modeling. 

Your job is to write a highly technical, engaging, and professional blog post based on the provided source data (which will either be a YouTube transcript or an Industry News brief). 

Target Audience: Solar asset managers, EPC engineers, and renewable energy investors.
Tone: Data-driven, authoritative, analytical, and slightly contrarian. Challenge outdated industry standards and advocate for dynamic, data-driven modeling.

Guidelines:
1. Do not act like a generic AI. Write like an industry veteran.
2. Use proper markdown (## for headings, bold text, bullet points).
3. Do not include a main # title (the publisher script will handle it). Start immediately with an engaging introductory paragraph.
4. Naturally weave in concepts like P50/P90 probability, O&M costs, albedo, clipping, or satellite data where relevant.
5. Do not explicitly mention that you are reacting to a video or an article. Present this as your own original Solar Metrix engineering analysis on a trending topic.
"""

def get_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([t['text'] for t in transcript_list])
    except Exception:
        return None

def get_latest_news(processed_list):
    print("Falling back to Google News RSS...")
    news_query = "solar+energy+technology+optimization"
    url = f"https://news.google.com/rss/search?q={news_query}&hl=en-US&gl=US&ceid=US:en"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req)
        xml_data = response.read()
        root = ET.fromstring(xml_data)
        
        for item in root.findall('./channel/item'):
            title = item.find('title').text
            description = item.find('description').text
            
            # Create a unique ID for the news article using a hash
            news_id = "news_" + hashlib.md5(title.encode('utf-8')).hexdigest()
            
            if news_id not in processed_list:
                content = f"Headline: {title}\n\nSummary/Context:\n{description}"
                return "Industry News Brief", news_id, title, content
    except Exception as e:
        print(f"News fetch failed: {e}")
        
    return None, None, None, None

def get_content():
    history_file = "processed_videos.txt"
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            processed = set(f.read().splitlines())
    else:
        processed = set()

    # 1. TRY YOUTUBE FIRST
    random.shuffle(SEARCH_QUERIES)
    for query in SEARCH_QUERIES:
        print(f"Searching YouTube for: {query}")
        try:
            request = youtube.search().list(q=query, part="snippet", type="video", maxResults=5, order="date", relevanceLanguage="en")
            response = request.execute()
            
            for item in response.get('items', []):
                vid_id = item['id']['videoId']
                if vid_id not in processed:
                    transcript = get_transcript(vid_id)
                    if transcript:
                        return "YouTube Transcript", vid_id, item['snippet']['title'], transcript
                    else:
                        with open(history_file, "a") as f:
                            f.write(vid_id + "\n")
                        processed.add(vid_id)
        except Exception as e:
            print(f"YouTube search error on '{query}': {e}")
            continue

    # 2. FALL BACK TO NEWS
    return get_latest_news(processed)

def generate_blog(source_type, title, data):
    prompt = f"{SYSTEM_PROMPT}\n\nSource Type: {source_type}\nTopic/Title: {title}\n\nData to analyze:\n{data[:15000]}"
    
    # NEW SDK SYNTAX
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    return response.text

def main():
    if not YOUTUBE_API_KEY or not GEMINI_API_KEY:
        print("CRITICAL: Missing API Keys!")
        return

    os.makedirs("drafts", exist_ok=True)
    
    source_type, item_id, title, data = get_content()
    
    if not source_type:
        print("No new videos OR news found today.")
        return
        
    print(f"Found new content via {source_type}: {title}")
    print("Generating Solar Metrix Article...")
    
    blog_content = generate_blog(source_type, title, data)
    
    safe_title = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"drafts/{date_str}-{safe_title[:40]}.md"
    
    display_title = title.split(' - ')[0] if source_type == "Industry News Brief" else title
    final_file_content = f"# {display_title}\n\n{blog_content}"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(final_file_content)
        
    with open("processed_videos.txt", "a") as f:
        f.write(item_id + "\n")
        
    print(f"Success! Saved to {filename}")

if __name__ == "__main__":
    main()
