# 🎬 YouTube Shorts Full Automation System

> Daily 2 Shorts — subah 8am + raat 9pm — fully automated
> Tu sirf CapCut mein 5 min de, baaki sab AI karta hai

---

## ⚡ How It Works

```
GitHub Actions (cron) 
  → Fetch world news (RSS)
  → Claude picks best story + writes Hinglish conspiracy script
  → Claude generates SEO pack (title, tags, description)
  → ElevenLabs generates Hindi voiceover MP3
  → Package saved as downloadable artifact
  → Telegram notification sent to you
  
YOU:
  → Download artifact from GitHub
  → Open CapCut, import voice.mp3
  → Add B-roll + auto captions (5 min)
  → Upload to YouTube with provided title/tags/description
```

---

## 🛠️ One-Time Setup (30 min total)

### Step 1 — GitHub Repo banao
```bash
git init yt-automation
cd yt-automation
# Copy all these files into folder
git add .
git commit -m "init"
git remote add origin https://github.com/PrinceThakurhub/yt-automation.git
git push -u origin main
```

### Step 2 — API Keys lo

| Key | Where se milega | Free? |
|-----|----------------|-------|
| `ANTHROPIC_API_KEY` | console.anthropic.com | Pay per use (~₹0.5/run) |
| `ELEVENLABS_API_KEY` | elevenlabs.io | Free 10k chars/month |
| `ELEVENLABS_VOICE_ID` | ElevenLabs → Voices | Free Hindi voice available |
| `YOUTUBE_API_KEY` | console.cloud.google.com | Free |
| `TELEGRAM_BOT_TOKEN` | @BotFather on Telegram | Free |
| `TELEGRAM_CHAT_ID` | @userinfobot on Telegram | Free |

### Step 3 — GitHub Secrets add karo

GitHub repo → Settings → Secrets and variables → Actions → New secret

Add these secrets:
```
ANTHROPIC_API_KEY      = sk-ant-...
ELEVENLABS_API_KEY     = ...
ELEVENLABS_VOICE_ID    = pNInz6obpgDQGcFmaJgB  (ya apna)
YOUTUBE_API_KEY        = AIza...
TELEGRAM_BOT_TOKEN     = 123456:ABC...
TELEGRAM_CHAT_ID       = your_chat_id
```

### Step 4 — YouTube OAuth (one time on PC)
```bash
pip install google-auth-oauthlib
python scripts/oauth_setup.py
# Browser khuleg → allow karo → token.json banega
```
Phir token.json ka poora content copy karo aur GitHub Secret mein daalo:
```
YOUTUBE_TOKEN_JSON = {full token.json content}
```

### Step 5 — ElevenLabs Hindi Voice
1. elevenlabs.io → Voice Library
2. Search "Hindi" ya "Indian"
3. Voice ID copy karo → GitHub Secret mein daalo

---

## 📅 Schedule

| Slot | IST Time | UTC (cron) |
|------|----------|------------|
| Morning | 8:00 AM | `30 2 * * *` |
| Night | 9:00 PM | `30 15 * * *` |

---

## 📲 Tera Daily Routine (5 min only)

1. **Telegram notification aayega** — "Short ready!"
2. **GitHub → Actions → Latest run → Artifacts** → Download zip
3. **CapCut open karo**:
   - `voice.mp3` import karo
   - B-roll/stock footage add karo (Pexels free hai)
   - Auto captions on karo
   - Export as 9:16 vertical
4. **YouTube Studio** → Upload → Paste title/tags from `CAPCUT_GUIDE.txt`
5. **Done!** ✅

---

## 💰 Monthly Cost Estimate

| Tool | Cost |
|------|------|
| Anthropic API | ~₹100-200/month (60 runs) |
| ElevenLabs | Free (10k chars) |
| GitHub Actions | Free (2000 min/month) |
| YouTube API | Free |
| **Total** | **~₹150-200/month** |

---

## 🔧 Customization

Edit `scripts/pipeline.py`:
- `RSS_FEEDS` → apne preferred news sources
- `CHANNEL_NICHE` → apna channel style
- `VOICE_ID` → apni ElevenLabs voice
- Script style → `generate_content()` function mein system prompt change karo

---

## ❓ Problems?

- **Pipeline failed?** → GitHub Actions → Logs check karo
- **Voice nahi bani?** → ElevenLabs quota check karo
- **YouTube upload nahi hua?** → OAuth token refresh karo (run `oauth_setup.py` again)
