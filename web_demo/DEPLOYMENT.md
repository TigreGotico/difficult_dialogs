# Web Demo Deployment Guide

**Version:** 1.0  
**Last Updated:** 2026-03-30

---

## Quick Start

### Run Locally

```bash
# Install dependencies
pip install streamlit

# Run the demo
cd web_demo
streamlit run app.py
```

The demo will open in your browser at `http://localhost:8501`

---

## Deploy to Hugging Face Spaces

Hugging Face Spaces provides **free hosting** for Streamlit apps with no credit card required.

### Step 1: Create a Hugging Face Account

1. Go to https://huggingface.co/
2. Click "Sign Up" (top right)
3. Create account with GitHub or email

### Step 2: Create New Space

1. Click your profile picture → "New Space"
2. Fill in details:
   - **Space name:** `difficult-dialogs-demo`
   - **License:** MIT
   - **Space SDK:** Select **Streamlit**
   - **Visibility:** Public (recommended for demos)
3. Click "Create Space"

### Step 3: Upload Files

You have 3 options:

#### Option A: Git Push (Recommended)

```bash
# Clone your space
git clone https://huggingface.co/spaces/YOUR_USERNAME/difficult-dialogs-demo
cd difficult-dialogs-demo

# Copy files from web_demo directory
cp /path/to/difficult_dialogs/web_demo/* .

# Also copy the sample arguments (important!)
cp -r /path/to/difficult_dialogs/examples/sample_arguments .

# Commit and push
git add .
git commit -m "Initial commit: Difficult Dialogs demo"
git push
```

#### Option B: Web UI Upload

1. In your Space page, click "Files" → "Add file" → "Upload files"
2. Upload these files:
   - `app.py`
   - `requirements.txt`
3. Create a new folder `sample_arguments`
4. Upload all argument directories into `sample_arguments/`

#### Option C: GitHub Sync

1. Create a public GitHub repo with your demo files
2. In Hugging Face Space, go to "Settings" → "Linked Resources"
3. Click "Link GitHub repository"
4. Select your repo
5. Changes auto-sync!

### Step 4: Wait for Build

- Hugging Face will automatically build your Space
- Takes 2-5 minutes typically
- Status shows in top-right corner:
  - 🟡 Building → 🟢 Running

### Step 5: Share Your Demo

Once running, share the URL:
```
https://huggingface.co/spaces/YOUR_USERNAME/difficult-dialogs-demo
```

---

## File Structure

Your deployed Space should look like:

```
difficult-dialogs-demo/
├── app.py                    # Main Streamlit app
├── requirements.txt          # Dependencies (streamlit)
└── sample_arguments/         # Argument library
    ├── technology/
    │   ├── artificial_intelligence_will_benefit_humanity/
    │   ├── remote_work_increases_productivity/
    │   └── ...
    ├── science/
    │   └── ...
    ├── health/
    │   └── ...
    ├── philosophy/
    │   └── ...
    ├── society/
    │   └── ...
    └── education/
        └── ...
```

**Important:** The `sample_arguments` directory must be included or the demo won't work!

---

## Configuration Options

### Customize App Title

Edit `app.py`, line ~20:
```python
st.set_page_config(
    page_title="Your Custom Title",
    page_icon="🎯",  # Change emoji
    # ...
)
```

### Add More Arguments

Simply add new argument directories to `sample_arguments/`:
```bash
cp -r examples/sample_arguments/philosophy/new_argument \
      web_demo/sample_arguments/philosophy/
```

Then commit and push to Hugging Face.

### Change Default Policy

Edit `app.py`, line ~70:
```python
if "current_policy" not in st.session_state:
    st.session_state.current_policy = "Socratic (Questions)"  # Change default
```

### Add Custom CSS

Edit the `<style>` block in `app.py` (line ~30) to customize appearance.

---

## Troubleshooting

### Error: "No sample arguments found!"

**Cause:** Missing `sample_arguments` directory

**Fix:** Ensure you uploaded/copied the entire `sample_arguments/` folder with all subdirectories.

### Error: "ModuleNotFoundError: No module named 'difficult_dialogs'"

**Cause:** Import path issue

**Fix:** The web demo uses relative imports. Make sure `app.py` is in the root of your Space (not in a subfolder).

### Space Stuck in "Building" State

**Possible causes:**
1. Large file upload still in progress
2. Requirements installation failed
3. Syntax error in `app.py`

**Fix:**
- Check "Logs" tab for errors
- Verify `requirements.txt` has valid package names
- Test `app.py` locally first

### Demo Loads But No Arguments Appear

**Check:**
1. Are there actually directories in `sample_arguments/`?
2. Do they contain `.premise` files?
3. Is the path structure correct?

Run this to verify:
```bash
find sample_arguments -name "*.premise" | head -5
```

---

## Performance Optimization

### Reduce Initial Load Time

The demo loads all arguments on startup. With 32 arguments this is fast (~1s), but if you add more:

**Option 1:** Lazy loading (modify `load_sample_arguments()` to cache results)

**Option 2:** Pre-filter categories:
```python
# Only load specific categories
CATEGORIES_TO_INCLUDE = ["technology", "philosophy"]
```

### Handle More Concurrent Users

Hugging Face Spaces free tier:
- ✅ Unlimited visitors
- ⚠️ Single CPU core
- ⚠️ Limited RAM

For high traffic (>100 concurrent users):
- Upgrade to PRO ($9/month)
- Or deploy on alternative platforms (see below)

---

## Alternative Deployment Platforms

### 1. Streamlit Cloud (Free)

**URL:** https://streamlit.io/cloud

**Pros:**
- Official Streamlit hosting
- Free for public apps
- Easy GitHub integration

**Cons:**
- Requires public GitHub repo
- No custom domain on free tier

**Deploy:**
1. Push code to GitHub
2. Connect Streamlit Cloud to repo
3. Select `web_demo/app.py` as main script

### 2. Render (Free Tier)

**URL:** https://render.com

**Pros:**
- Free tier available
- Custom domains
- More control

**Cons:**
- Requires Dockerfile
- Slightly more complex setup

**Basic Dockerfile:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### 3. Railway (Trial Credits)

**URL:** https://railway.app

**Pros:**
- $5 free credits
- Easy deployment
- Auto-scaling

**Cons:**
- Not completely free long-term

### 4. Your Own Server

For complete control, deploy on VPS:

```bash
# Install
pip install streamlit

# Run as service
streamlit run app.py --server.port 80 --server.enableCORS false
```

Use systemd or supervisor to keep it running.

---

## Analytics & Monitoring

### Track Usage

Add to `app.py`:
```python
# Simple counter (stores in session state)
if "visit_count" not in st.session_state:
    st.session_state.visit_count = 0
st.session_state.visit_count += 1

with st.sidebar:
    st.metric("Session Visits", st.session_state.visit_count)
```

### Google Analytics

Add to Streamlit's HTML (advanced):
```python
import streamlit.components.v1 as components

components.html(
    """
    <!-- Google Analytics code here -->
    """,
    height=0,
)
```

---

## Embedding in Websites

### iframe Embed

Add to any website:
```html
<iframe 
    src="https://huggingface.co/spaces/YOUR_USERNAME/difficult-dialogs-demo"
    width="100%"
    height="800px"
    style="border: none;"
></iframe>
```

### WordPress

Use "Custom HTML" block with iframe code above.

### GitHub README

```markdown
### Try It Live!

[![Open in Hugging Face Spaces](https://huggingface.co/datasets/huggingface/badges/raw/main/open-in-hf-spaces-sm.svg)](https://huggingface.co/spaces/YOUR_USERNAME/difficult-dialogs-demo)
```

---

## Security Considerations

### What's Safe

✅ No user authentication needed (stateless demo)  
✅ No database writes (read-only argument loading)  
✅ No external API calls (runs offline)  
✅ No file uploads (user input only via chat)  

### Potential Concerns

⚠️ **Rate Limiting:** Hugging Face may throttle very high traffic  
⚠️ **Content Moderation:** User inputs aren't filtered (but aren't stored either)  
⚠️ **Intellectual Property:** Ensure arguments don't violate copyrights  

### Best Practices

1. **Don't store sensitive data** - Session state resets on refresh
2. **Validate user input** - Already done (policy handles gracefully)
3. **Use HTTPS** - Hugging Face provides this automatically
4. **Monitor usage** - Check Space logs periodically

---

## Updating Your Demo

### Push Updates

```bash
# Make changes locally
git add .
git commit -m "Updated: Added new policy option"
git push
```

Changes deploy automatically in 1-2 minutes.

### Force Rebuild

If something breaks:
1. Go to Space Settings
2. Click "Factory reboot"
3. Wait for rebuild

---

## Cost Breakdown

### Completely Free Option

- **Hugging Face Spaces (Community tier):** $0
  - ✅ Unlimited public spaces
  - ✅ 16GB storage
  - ✅ Shared CPU
  - ⚠️ Sleeps after inactivity (wakes on visit)

### Paid Options (If Needed)

- **Hugging Face PRO:** $9/month
  - ✅ Dedicated CPU
  - ✅ No sleep mode
  - ✅ Custom domains
  
- **Streamlit Cloud PRO:** Free for public, $29/month for private

- **VPS (DigitalOcean, Linode):** $5-10/month
  - ✅ Full control
  - ✅ Custom domain
  - ⚠️ Requires sysadmin knowledge

**Recommendation:** Start with free Hugging Face Spaces. Upgrade only if you hit limits.

---

## Success Metrics

Track these to measure demo success:

### Basic Metrics
- **Total visits:** Hugging Face shows in dashboard
- **Unique visitors:** Use analytics tool
- **Average session duration:** Estimate from chat interactions
- **Arguments tried:** Add counter per argument

### Engagement Metrics
```python
# Add to app.py
if "interactions" not in st.session_state:
    st.session_state.interactions = 0

# Increment on each user message
st.session_state.interactions += 1
```

### Conversion Goals
- GitHub stars from demo visitors
- PyPI downloads increase
- Community contributions
- Social media shares

---

## Marketing Your Demo

### Where to Share

1. **Reddit:**
   - r/MachineLearning
   - r/Python
   - r/ArtificialIntelligence
   - r/ChatBots

2. **Twitter/X:**
   - Post demo link with #AI #NLP #Python
   - Tag @huggingface

3. **LinkedIn:**
   - AI/ML groups
   - Python developer communities

4. **Hacker News:**
   - "Show HN: Interactive Argument Explorer"

5. **Discord/Slack:**
   - Python Discord
   - AI/ML community servers

### Sample Pitch

```
🎯 Try Difficult Dialogs - Interactive Argument Explorer!

Explore 30+ structured arguments on philosophy, science, 
technology, and more. Choose from 5 interaction styles:
- Socratic questioning
- Active debate
- Neutral exploration
- Evidence-based persuasion
- Silent presentation

✨ Runs entirely offline - no API calls!
✨ Open source - contribute on GitHub
✨ Zero dependencies - pure Python

Try it: https://huggingface.co/spaces/YOU/difficult-dialogs-demo
GitHub: https://github.com/difficult-dialogs/difficult_dialogs
```

---

## Advanced Customizations

### Add Authentication (Optional)

For private deployments:
```python
import streamlit_authenticator as stauth

# Add login before showing main app
authenticator = stauth.Authenticate(...)
name, auth_status, username = authenticator.login('Login', 'main')

if auth_status:
    main()  # Show demo
else:
    st.warning("Please login")
```

### Multi-Language Support

Add language selector:
```python
lang = st.sidebar.selectbox("Language", ["English", "Español", "Français"])

# Load translations
translations = load_translations(lang)
```

### Export Conversations

Add download button:
```python
if st.sidebar.button("Export Chat"):
    chat_text = "\n".join([f"{m['role']}: {m['content']}" 
                           for m in st.session_state.chat_history])
    st.download_button(
        label="Download Transcript",
        data=chat_text,
        file_name=f"dialog_{arg.name}.txt",
        mime="text/plain"
    )
```

### A/B Testing Policies

Randomly assign default policy to measure engagement:
```python
import random

if "assigned_policy" not in st.session_state:
    st.session_state.assigned_policy = random.choice(list(POLICIES.keys()))
```

---

## Support & Resources

### Documentation
- [Streamlit Docs](https://docs.streamlit.io/)
- [Hugging Face Spaces Guide](https://huggingface.co/docs/hub/spaces)
- [Difficult Dialogs POLICIES.md](../docs/POLICIES.md)

### Community Help
- [Streamlit Community Forum](https://discuss.streamlit.io/)
- [Hugging Face Forums](https://discuss.huggingface.co/)
- [GitHub Issues](https://github.com/difficult-dialogs/difficult_dialogs/issues)

### Troubleshooting Checklist

Before asking for help:
- [ ] Tested locally first
- [ ] Checked Hugging Face logs
- [ ] Verified `requirements.txt` syntax
- [ ] Confirmed `sample_arguments/` directory exists
- [ ] Tried factory reboot

---

## Next Steps After Deployment

1. ✅ **Share on social media**
2. ✅ **Add link to project README**
3. ✅ **Embed in blog posts**
4. ✅ **Include in conference talks**
5. ✅ **Use in educational settings**

### Future Enhancements

Consider adding:
- User accounts (save favorite arguments)
- Custom argument upload
- Policy comparison mode
- Export to PDF/JSON
- Multi-language support
- Voice input/output

---

*This guide is part of the Difficult Dialogs documentation suite.*

**Questions?** Open an issue on GitHub or ask in Hugging Face community forums.
