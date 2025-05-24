from bs4 import BeautifulSoup
import base64
import os
import requests
import json

OWNER = 'FancyOtter99'
REPO = 'Chat'
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')

tasks = [
    {'path': 'users.txt', 'url': 'https://chat-le5h.onrender.com/secret-users?key=letmein'},
    {'path': 'admins.json', 'url': 'https://chat-le5h.onrender.com/secret-roles?key=letmein'},
    {'path': 'user_items.json', 'url': 'https://chat-le5h.onrender.com/secret-items?key=letmein'},
]

def get_pre_content(html):
    print("Parsing HTML to extract <pre> content...")
    soup = BeautifulSoup(html, 'html.parser')
    pres = soup.find_all('pre')
    if not pres:
        print("⚠️ No <pre> tags found in HTML!")
    else:
        print(f"✅ Found {len(pres)} <pre> tags.")
    extracted = '\n\n'.join(pre.get_text() for pre in pres).strip()
    print(f"Extracted content length: {len(extracted)} characters.")
    return extracted

def get_file_sha(path):
    url = f'https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}'
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    print(f"Getting SHA for {path} from GitHub...")
    r = requests.get(url, headers=headers)
    print(f"GitHub SHA response status: {r.status_code}")
    if r.status_code == 200:
        sha = r.json().get('sha')
        print(f"Current SHA for {path}: {sha}")
        return sha
    else:
        print(f"⚠️ Could not get SHA for {path}. Response: {r.text}")
        return None

def update_github_file(content, path, sha=None):
    url = f'https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}'
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github+json'
    }
    message = f'Update {path} with extracted <pre> content'
    encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    data = {
        'message': message,
        'content': encoded_content
    }
    if sha:
        data['sha'] = sha

    print(f"Updating {path} on GitHub...")
    r = requests.put(url, headers=headers, json=data)
    print(f"GitHub PUT response status: {r.status_code}")
    try:
        print("GitHub response JSON:")
        print(json.dumps(r.json(), indent=2))
    except Exception as e:
        print("⚠️ Could not parse GitHub response as JSON:", e)
    if r.status_code in (200, 201):
        print(f"✅ {path} updated successfully on GitHub!")
    else:
        print(f"❌ Failed to update {path} on GitHub. Response: {r.text}")

def update_task(url, path):
    try:
        print(f"\n🔗 Fetching data from: {url}")
        r = requests.get(url)
        r.raise_for_status()
        print(f"✅ HTTP {r.status_code} OK for {url}")
        print("---- Raw HTML preview (first 300 characters) ----")
        print(r.text[:300] + '...' if len(r.text) > 300 else r.text)
        print("--------------------------------------------------")
        pre_content = get_pre_content(r.text)
        if not pre_content:
            print(f"⚠️ No content extracted from {url}. Skipping update for {path}.")
            return
        sha = get_file_sha(path)
        update_github_file(pre_content, path, sha)
    except Exception as e:
        print(f"❌ Error during update for {path}: {e}")

print("🚀 Starting update tasks with extra debugging...\n")
for task in tasks:
    update_task(task['url'], task['path'])
print("\n🎉 All tasks completed.")

