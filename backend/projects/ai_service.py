import os
import json
import logging
from django.conf import settings
import google.generativeai as genai

logger = logging.getLogger(__name__)

# Configure Gemini if key is present
if getattr(settings, 'GEMINI_API_KEY', ''):
    genai.configure(api_key=settings.GEMINI_API_KEY)

def generate_social_assets(title, source_type, content_text, memory_settings=None, templates=None):
    """
    Call Gemini API to generate short-form social assets from long-form content.
    If no key is configured, fall back to a rich mock generator.
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    
    # Structure memory/preferences into the prompt
    memory_prompt = ""
    if memory_settings:
        brand_tone_val = memory_settings.get('BRAND_TONE')
        if isinstance(brand_tone_val, dict):
            brand_tone = brand_tone_val.get('tone', 'Professional, engaging, and authoritative')
        else:
            brand_tone = brand_tone_val or 'Professional, engaging, and authoritative'
            
        style_guide_val = memory_settings.get('STYLE_GUIDE')
        if isinstance(style_guide_val, dict):
            style_guide = style_guide_val.get('guide', 'Clear, clean formatting, limit emoji use')
        else:
            style_guide = style_guide_val or 'Clear, clean formatting, limit emoji use'
            
        preferred_hooks_val = memory_settings.get('PREFERRED_HOOKS')
        if isinstance(preferred_hooks_val, dict):
            preferred_hooks = preferred_hooks_val.get('hooks', '')
        else:
            preferred_hooks = preferred_hooks_val or ''
        
        memory_prompt = f"""
        Tone of Voice: {brand_tone}
        Style Guide: {style_guide}
        Preferred Hooks Style: {preferred_hooks}
        """


    # Structured prompt requesting JSON output
    prompt = f"""
    You are an expert social media copywriter and growth marketer.
    I want you to analyze the following long-form content text and generate structured short-form social-ready assets.

    Content Title: {title}
    Source Type: {source_type}
    
    {memory_prompt}
    
    Content text to analyze:
    {content_text[:8000]}  # Clip to 8000 chars for safety

    You MUST return a JSON object with the exact keys:
    1. "hooks": list of 3 high-engaging hook variations for video openers.
    2. "titles": list of 3 clickable video title variations.
    3. "captions": list of 3 caption options (shorts, reels, tiktok formats).
    4. "ctas": list of 3 call-to-action options (e.g. follow, comment, download link).
    5. "hashtags": list of 8 trending and relevant hashtags.
    6. "thumbnail_copy": list of 3 short, punchy texts to display on video thumbnails (max 4 words each).
    7. "scripts": list of 2 short video script scripts (under 60 seconds each), with visual prompts and spoken words.
    
    Ensure your output is valid JSON. Do not include markdown code block styling in the JSON output, start directly with the brackets.
    """

    if api_key:
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            text_response = response.text.strip()
            
            # Clean response if markdown wrappers exist
            if text_response.startswith("```json"):
                text_response = text_response[7:]
            if text_response.endswith("```"):
                text_response = text_response[:-3]
            text_response = text_response.strip()
            
            parsed_data = json.loads(text_response)
            logger.info("Successfully generated assets via Gemini API.")
            return parsed_data
        except Exception as e:
            logger.error(f"Gemini API generation failed: {str(e)}. Falling back to mock data.")
            # Fall through to mock generator

    # Mock Fallback Data Generator
    logger.info("Generating assets using mock content generator.")
    
    # Extract topics or keywords from title/content
    keywords = [x.lower() for x in title.split() if len(x) > 3][:3]
    kw_str = " ".join(keywords) or "content creation"
    
    mock_data = {
        "hooks": [
            f"Here's the secret to {kw_str} that no one is telling you...",
            f"Stop scrolling if you want to master {kw_str} today.",
            f"I analyzed 100 creators doing {kw_str}, and they all make this one mistake."
        ],
        "titles": [
            f"The Ultimate {title} Guide",
            f"Mastering {kw_str} in 60 Seconds",
            f"Why Your {title} is Failing (And How to Fix It)"
        ],
        "captions": [
            f"If you're struggling with {kw_str}, you need to watch this. Here is the step-by-step breakdown of how to improve your workflow. Save this video for later! 📈",
            f"The honest truth about {kw_str}. Let me know in the comments if you agree or disagree! 👇",
            f"Quick tip of the day: Stop overcomplicating your {kw_str}. Start small, iterate fast, and build consistency. Check out our bio for a full guide!"
        ],
        "ctas": [
            f"Follow for daily tips on {kw_str}!",
            "Leave a comment with your biggest challenge.",
            "Click the link in our bio to grab our free resource."
        ],
        "hashtags": [
            f"#{x.replace(' ', '')}" for x in [kw_str, "viraltips", "creators", "growthmindset", "contentcreator", "marketingtips", "productivity", "viralops"]
        ],
        "thumbnail_copy": [
            "SECRET revealed!",
            "DO NOT miss this!",
            "Fix this now!"
        ],
        "scripts": [
            {
                "platform": "SHORTS",
                "script": "[Visual: Creator looking shocked at camera]\nSpeaker: Most creators are doing this completely wrong. They think it's about spending hours editing. But here's the reality: it's all about hook structure. You have exactly 3 seconds to catch attention. Optimize that, and you win. Follow for part 2!"
            },
            {
                "platform": "TIKTOK",
                "script": "[Visual: B-roll of coding/writing screens]\nSpeaker: Want to scale your output without burning out? Start repurposing. One long podcast can become 10 micro-assets. That's how top creators publish daily. Stop creating from scratch, start editing from what you already have."
            }
        ]
    }
    
    return mock_data
