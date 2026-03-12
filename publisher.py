print("VERSION 16.0 - SOLAR METRIX DARK THEME ENGINE")
import os, glob, markdown, re, shutil, random
from datetime import datetime

# We are targeting the new blog.html
HTML_FILE = "blog.html"

def process_drafts():
    if not os.path.exists("drafts"): return
    drafts = glob.glob("drafts/*.md")
    if not drafts: return

    os.makedirs("archive", exist_ok=True)
    
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        html_content = f.read()

    new_articles = ""
    drafts.sort()
    current_date = datetime.now().strftime("%b %d, %Y")

    for draft_path in drafts:
        with open(draft_path, "r", encoding="utf-8") as f:
            lines = f.read().split('\n')
        
        title = "Solar Industry Insight"
        for line in lines:
            if line.startswith('# ') or line.startswith('## '):
                title = line.replace('#', '').replace('**', '').strip()
                lines.remove(line)
                break
        
        body_html = markdown.markdown('\n'.join(lines).strip())
        art_id = "art-" + str(int(datetime.now().timestamp())) + str(random.randint(0,1000))

        # Solar Metrix Dark Mode Glass Panel Card
        new_articles += f'''
<article id="{art_id}" class="glass-panel p-8 md:p-12 scroll-mt-24 group hover:border-sky-500/50 transition-colors">
  <div class="flex items-center gap-3 mb-4 text-xs font-bold uppercase tracking-wider text-sky-400">
    <i data-lucide="zap" class="w-4 h-4"></i>
    <span>Solar Metrix Insight</span>
    <span class="w-1 h-1 rounded-full bg-slate-600"></span>
    <span class="text-slate-500">{current_date}</span>
  </div>
  <h2 class="text-3xl font-bold text-white mb-6 leading-tight">{title}</h2>
  <div class="prose prose-invert prose-sky max-w-none text-slate-300 leading-relaxed">
    {body_html}
  </div>
</article>
'''
        
        shutil.move(draft_path, os.path.join("archive", os.path.basename(draft_path)))
        print(f"Processed: {title}")

    # TARGET THE NEW HTML DIV
    ART_TARGET = '<div id="dynamic-articles-container" class="space-y-12 max-w-4xl mx-auto">'

    if ART_TARGET in html_content:
        # We inject right after the target div opening tag
        html_content = html_content.replace(ART_TARGET, ART_TARGET + '\n' + new_articles)
        print("Successfully injected Solar Metrix Articles.")
    else:
        print(f"CRITICAL: Could not find the <div> tag in {HTML_FILE}!")

    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)
    print("Success! Solar Metrix Blog Rebuilt.")

if __name__ == "__main__":
    process_drafts()
