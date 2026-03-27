"""
Run this ONCE on your PC to get YouTube OAuth token.
Then upload token.json as GitHub Secret.

Steps:
1. Go to console.cloud.google.com
2. Create project → Enable YouTube Data API v3
3. Create OAuth 2.0 credentials (Desktop app)
4. Download client_secret.json → put in this folder
5. Run: python oauth_setup.py
6. Browser opens → login → allow
7. token.json is created → add to GitHub Secrets
"""

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def main():
    flow = InstalledAppFlow.from_client_secrets_file(
        "client_secret.json", SCOPES
    )
    creds = flow.run_local_server(port=0)
    
    with open("token.json", "w") as f:
        f.write(creds.to_json())
    
    print("\n✅ token.json created!")
    print("   Now add it as GitHub Secret: YOUTUBE_TOKEN_JSON")
    print("   (copy the full contents of token.json)")

if __name__ == "__main__":
    main()
