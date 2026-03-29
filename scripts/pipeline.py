"""
YouTube Shorts Full Automation Pipeline
Fetches news → Gemini generates script+SEO → ElevenLabs voice → YouTube upload
"""

import os
import json
import time
import requests
import feedparser
from datetime import datetime

# ── CLIENTS ──────────────────────────────────────────────────────────────────
GEMINI_KEY = os.environ["GEMINI_API_KEY"]
XI_KEY     = os.environ["ELEVENLABS_API_KEY"]
VOICE_ID   = os.environ.get("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"

RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",
    "https://www.thehindu.com/news/international/feeder/default.rss",
]

SLOT = os.environ.get("SLOT", "morning")
CHANNEL_NICHE = "Finance & Trading - conspiracy/spicy Hinglish news shorts"

def ask_gemini(prompt):
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.9, "maxOutputTokens": 2000}
    }
    for attempt in range(3):
        r = requests.post(GEMINI_URL, json=payload)
        if r.status_code == 429:
            print(f"Rate limit hit, waiting 30s... (attempt {attempt+1})")
            time.sleep(30)
            continue
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    raise Exception("Gemini rate limit — 3 attempts failed")


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


def pick_story(stories):
    stories_text = "\n".join([f"{i+1}. {s['title']} — {s['summary']}"
                               for i, s in enumerate(stories)])
    prompt = f"""You are a viral YouTube Shorts strategist for a Finance & Trading channel targeting Indian youth.
Pick the SINGLE best story for a YouTube Short today ({SLOT} slot). Finance/economy angle preferred.

Stories:
{stories_text}

Reply ONLY in this JSON format (no markdown):
{{
  "index": <1-based number>,
  "title": "<original title>",
  "why": "<1 line reason>"
}}"""

    raw = ask_gemini(prompt).replace("```json","").replace("```","").strip()
    result = json.loads(raw)
    chosen = stories[result["index"] - 1]
    print(f"[Step 2] Picked: {chosen['title']}")
    return chosen


def generate_content(story):
    prompt = f"""You are a viral YouTube Shorts creator for: {CHANNEL_NICHE}
Style: Conspiracy angle, pure Hinglish, 'jo media nahi batata' vibe.
Audience: Indian youth 18-30, finance-curious, loves drama.

Create content pack for this story:
Title: {story['title']}
Summary: {story['summary']}

Return ONLY valid JSON (no markdown, no code fences):
{{
  "script": "<60-second Hinglish script, [PAUSE] markers, ends with Comment karo CTA>",
  "yt_title": "<clickbait Hinglish title under 70 chars>",
  "description": "<150 word Hindi/English description with keywords>",
  "tags": ["tag1","tag2","tag3","tag4","tag5","tag6","tag7","tag8","tag9","tag10"],
  "hashtags": ["#tag1","#tag2","#tag3","#tag4","#tag5"],
  "thumbnail_prompt": "<DALL-E prompt: dark dramatic background, bold text, financial crisis vibes>",
  "thumbnail_text": "<3-5 bold Hindi words for thumbnail>"
}}"""

    raw = ask_gemini(prompt).replace("```json","").replace("```","").strip()
    content = json.loads(raw)
    print(f"[Step 3] Content ready: {content['yt_title']}")
    return content


def generate_voice(script, output_path="voice.mp3"):
    clean = script.replace("[PAUSE]","... ").replace("[HOOK]","").replace("[CTA]","")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {"xi-api-key": XI_KEY, "Content-Type": "application/json"}
    payload = {
        "text": clean,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability":0.4,"similarity_boost":0.85,"style":0.6,"use_speaker_boost":True}
    }
    r = requests.post(url, json=payload, headers=headers)
    if r.status_code == 200:
        with open(output_path,"wb") as f: f.write(r.content)
        print(f"[Step 4] Voice generated: {output_path}")
        return output_path
    else:
        raise Exception(f"ElevenLabs error: {r.status_code} — {r.text}")


def save_capcut_package(content, voice_path, slot):
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    folder = f"output/{ts}_{slot}"
    os.makedirs(folder, exist_ok=True)

    guide = f"""
===========================================================
   CAPCUT PACKAGE — {slot.upper()} SHORT — {datetime.now().strftime("%d %B %Y")}
===========================================================

YOUTUBE TITLE:
{content['yt_title']}

SCRIPT (use voice.mp3):
{content['script']}

THUMBNAIL TEXT:
{content['thumbnail_text']}

THUMBNAIL PROMPT (paste in DALL-E):
{content['thumbnail_prompt']}

DESCRIPTION:
{content['description']}

TAGS: {', '.join(content['tags'])}

HASHTAGS: {' '.join(content['hashtags'])}
"""
    with open(f"{folder}/CAPCUT_GUIDE.txt","w",encoding="utf-8") as f: f.write(guide)

    if os.path.exists(voice_path):
        import shutil
        shutil.copy(voice_path, f"{folder}/voice.mp3")

    with open(f"{folder}/metadata.json","w",encoding="utf-8") as f:
        json.dump({"title":content["yt_title"],"description":content["description"],
                   "tags":content["tags"],"category":"25","privacy":"private","slot":slot},
                  f, ensure_ascii=False, indent=2)

    print(f"[Step 5] Package saved -> {folder}/")
    return folder


def main():
    print(f"\n{'='*60}")
    print(f"  YT PIPELINE — {SLOT.upper()} — {datetime.now().strftime('%d %b %Y %H:%M')}")
    print(f"{'='*60}\n")
    stories = fetch_news()
    story   = pick_story(stories)
    content = generate_content(story)
    voice   = generate_voice(content["script"])
    folder  = save_capcut_package(content, voice, SLOT)
    print(f"\nDONE! Folder: {folder}/")
    print("  -> Import voice.mp3 into CapCut")
    print("  -> Add B-roll + captions (5 min)")
    print("  -> Upload to YouTube with CAPCUT_GUIDE.txt\n")

if __name__ == "__main__":
    main()
