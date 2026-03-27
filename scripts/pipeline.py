"""
YouTube Shorts Full Automation Pipeline
Fetches news → Claude generates script+SEO → ElevenLabs voice → YouTube upload
"""

import os
import json
import time
import requests
import feedparser
from datetime import datetime
from anthropic import Anthropic

# ── CLIENTS ──────────────────────────────────────────────────────────────────
claude   = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
XI_KEY   = os.environ["ELEVENLABS_API_KEY"]
YT_KEY   = os.environ["YOUTUBE_API_KEY"]
VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")  # default Hindi voice

# ── CONFIG ───────────────────────────────────────────────────────────────────
RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",
    "https://www.thehindu.com/news/international/feeder/default.rss",
]

SLOT = os.environ.get("SLOT", "morning")   # "morning" or "night"
CHANNEL_NICHE = "Finance & Trading – conspiracy/spicy Hinglish news shorts"


# ═══════════════════════════════════════════════════════════════════════════
# STEP 1 — FETCH NEWS
# ═══════════════════════════════════════════════════════════════════════════
def fetch_news(max_items=30):
    stories = []
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]:
            stories.append({
                "title":   entry.get("title", ""),
                "summary": entry.get("summary", "")[:300],
                "source":  feed.feed.get("title", url),
            })
    print(f"[Step 1] Fetched {len(stories)} stories")
    return stories[:max_items]


# ═══════════════════════════════════════════════════════════════════════════
# STEP 2 — CLAUDE PICKS BEST STORY
# ═══════════════════════════════════════════════════════════════════════════
def pick_story(stories):
    stories_text = "\n".join([f"{i+1}. {s['title']} — {s['summary']}" 
                               for i, s in enumerate(stories)])
    
    msg = claude.messages.create(
        model="claude-opus-4-5",
        max_tokens=500,
        system="You are a viral YouTube Shorts strategist for a Finance & Trading channel targeting Indian youth. Pick stories with highest virality potential, especially those with a finance/economy angle or global power play.",
        messages=[{
            "role": "user",
            "content": f"""From these news stories, pick the SINGLE best one for a YouTube Short today ({SLOT} slot).

Stories:
{stories_text}

Reply in this exact JSON format (no markdown):
{{
  "index": <1-based number>,
  "title": "<original title>",
  "why": "<1 line reason>"
}}"""
        }]
    )
    
    raw = msg.content[0].text.strip()
    result = json.loads(raw)
    chosen = stories[result["index"] - 1]
    print(f"[Step 2] Picked: {chosen['title']}")
    print(f"         Why: {result['why']}")
    return chosen


# ═══════════════════════════════════════════════════════════════════════════
# STEP 3 — CLAUDE GENERATES FULL CONTENT PACK
# ═══════════════════════════════════════════════════════════════════════════
def generate_content(story):
    msg = claude.messages.create(
        model="claude-opus-4-5",
        max_tokens=2000,
        system=f"""You are a viral YouTube Shorts content creator for: {CHANNEL_NICHE}.
Style: Conspiracy angle, pure Hinglish, 'jo media nahi batata' vibe.
Audience: Indian youth 18-30, finance-curious, loves drama and hidden truths.""",
        messages=[{
            "role": "user",
            "content": f"""Create a complete YouTube Short content pack for this news story:

Title: {story['title']}
Summary: {story['summary']}
Source: {story['source']}

Return ONLY valid JSON (no markdown, no explanation):
{{
  "script": "<60-second Hinglish script with [PAUSE] markers, dramatic conspiracy angle, ends with 'Comment karo' CTA>",
  "yt_title": "<clickbait Hindi/Hinglish YouTube title under 70 chars>",
  "description": "<150 word Hindi/English description with keywords and timestamps>",
  "tags": ["tag1", "tag2", ...],
  "hashtags": ["#tag1", "#tag2", ...],
  "thumbnail_prompt": "<Midjourney/DALL-E prompt for thumbnail — dark dramatic background, bold text overlay, financial crisis vibes>",
  "thumbnail_text": "<3-5 bold Hindi words for thumbnail overlay>"
}}"""
        }]
    )
    
    raw = msg.content[0].text.strip()
    content = json.loads(raw)
    print(f"[Step 3] Content pack ready: {content['yt_title']}")
    return content


# ═══════════════════════════════════════════════════════════════════════════
# STEP 4 — ELEVENLABS VOICEOVER
# ═══════════════════════════════════════════════════════════════════════════
def generate_voice(script, output_path="voice.mp3"):
    # Clean script — remove stage directions
    clean_script = script.replace("[PAUSE]", "... ").replace("[HOOK]", "").replace("[CTA]", "")
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "xi-api-key": XI_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": clean_script,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.4,
            "similarity_boost": 0.85,
            "style": 0.6,
            "use_speaker_boost": True
        }
    }
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"[Step 4] Voice generated: {output_path}")
        return output_path
    else:
        raise Exception(f"ElevenLabs error: {response.status_code} — {response.text}")


# ═══════════════════════════════════════════════════════════════════════════
# STEP 5 — SAVE CAPCUT PACKAGE (script + voice + thumbnail prompt)
# ═══════════════════════════════════════════════════════════════════════════
def save_capcut_package(content, voice_path, slot):
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    folder = f"output/{ts}_{slot}"
    os.makedirs(folder, exist_ok=True)
    
    # Save script card for CapCut reference
    script_card = f"""
╔══════════════════════════════════════════════════════════╗
   CAPCUT PACKAGE — {slot.upper()} SHORT
   {datetime.now().strftime("%d %B %Y")}
╚══════════════════════════════════════════════════════════╝

📹 YOUTUBE TITLE:
{content['yt_title']}

🎙️ SCRIPT (read aloud or use voice.mp3):
{content['script']}

🖼️ THUMBNAIL TEXT (bold overlay):
{content['thumbnail_text']}

🖼️ THUMBNAIL AI PROMPT (paste in Midjourney/DALL-E):
{content['thumbnail_prompt']}

🔍 DESCRIPTION (copy to YouTube):
{content['description']}

🏷️ TAGS:
{', '.join(content['tags'])}

#️⃣ HASHTAGS:
{' '.join(content['hashtags'])}
"""
    
    with open(f"{folder}/CAPCUT_GUIDE.txt", "w", encoding="utf-8") as f:
        f.write(script_card)
    
    # Copy voice file
    if os.path.exists(voice_path):
        import shutil
        shutil.copy(voice_path, f"{folder}/voice.mp3")
    
    # Save metadata JSON for YouTube upload step
    with open(f"{folder}/metadata.json", "w", encoding="utf-8") as f:
        json.dump({
            "title": content["yt_title"],
            "description": content["description"],
            "tags": content["tags"],
            "category": "25",      # News & Politics
            "privacy": "private",  # stays private until you upload the video
            "slot": slot,
        }, f, ensure_ascii=False, indent=2)
    
    print(f"[Step 5] CapCut package saved → {folder}/")
    return folder


# ═══════════════════════════════════════════════════════════════════════════
# STEP 6 — YOUTUBE METADATA UPLOAD (video file uploaded manually via CapCut)
# ═══════════════════════════════════════════════════════════════════════════
def upload_to_youtube(metadata_path, video_path=None):
    """
    If video_path is provided → full upload via API
    Otherwise → saves metadata for manual upload
    Note: Full video upload requires OAuth2 (see oauth_setup.py)
    """
    with open(metadata_path) as f:
        meta = json.load(f)
    
    if not video_path or not os.path.exists(video_path):
        print(f"[Step 6] No video file yet — metadata ready for manual YouTube Studio upload")
        print(f"         Title: {meta['title']}")
        return
    
    # OAuth upload — runs after you've done oauth_setup.py once
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    creds = Credentials.from_authorized_user_file("token.json")
    youtube = build("youtube", "v3", credentials=creds)

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": meta["title"],
                "description": meta["description"],
                "tags": meta["tags"],
                "categoryId": meta["category"],
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False,
            }
        },
        media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True)
    )
    
    response = request.execute()
    video_id = response["id"]
    print(f"[Step 6] Uploaded! https://youtube.com/shorts/{video_id}")
    return video_id


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════
def main():
    print(f"\n{'='*60}")
    print(f"  YT AUTOMATION PIPELINE — {SLOT.upper()} — {datetime.now().strftime('%d %b %Y %H:%M')}")
    print(f"{'='*60}\n")
    
    # 1. Fetch news
    stories = fetch_news()
    
    # 2. Pick best story
    story = pick_story(stories)
    
    # 3. Generate full content pack
    content = generate_content(story)
    
    # 4. Generate ElevenLabs voiceover
    voice_path = generate_voice(content["script"])
    
    # 5. Save CapCut package
    folder = save_capcut_package(content, voice_path, SLOT)
    
    # 6. Upload metadata (video upload after CapCut edit)
    upload_to_youtube(f"{folder}/metadata.json")
    
    print(f"\n✅ DONE! Open folder: {folder}/")
    print(f"   → Import voice.mp3 into CapCut")
    print(f"   → Add B-roll + captions (5 min)")
    print(f"   → Upload to YouTube with CAPCUT_GUIDE.txt details\n")


if __name__ == "__main__":
    main()
