import os
import re
import minify_html
import rcssmin
import rjsmin

def build():
    if not os.path.exists('build'):
        os.makedirs('build')

    # 1. Load index.html
    with open('index.html', 'r') as f:
        content = f.read()

    # 2. Find and inline CSS
    def replace_css(match):
        href = match.group(1)
        if os.path.exists(href):
            print(f"Inlining and minifying CSS: {href}")
            with open(href, 'r') as f_css:
                css_content = f_css.read()
                return f'<style>{rcssmin.cssmin(css_content)}</style>'
        return match.group(0)

    content = re.sub(r'<link rel="stylesheet" href="(.*?)">', replace_css, content)

    # 3. Find and inline JS
    def replace_js(match):
        src = match.group(1)
        if os.path.exists(src):
            print(f"Inlining and minifying JS: {src}")
            with open(src, 'r') as f_js:
                js_content = f_js.read()
                # Minify with rjsmin
                minified_js = rjsmin.jsmin(js_content)
                # Be careful about </script> inside JS (though rare in minified output, still good practice)
                safe_js = minified_js.replace('</script>', r'<\/script>')
                return f'<script>{safe_js}</script>'
        return match.group(0)

    content = re.sub(r'<script src="(.*?)"[^>]*></script>', replace_js, content)

    # 4. Final HTML minification
    print("Minifying HTML...")
    try:
        minified_content = minify_html.minify(
            content,
            minify_css=True,
            minify_js=True
        )
    except Exception as e:
        print(f"HTML Minification failed: {e}. Falling back to unminified HTML.")
        minified_content = content

    with open('build/index.html', 'w') as f:
        f.write(minified_content)

    print(f"Build complete: build/index.html ({len(minified_content)} bytes)")
    print(f"Reduction: {len(content) - len(minified_content)} bytes")

if __name__ == '__main__':
    build()
