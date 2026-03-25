"""
Update AIOSEO SEO fields on jetfuel.agency via headless browser.
Uses Gutenberg's data dispatch to trigger AIOSEO's save via editPost.
"""
import argparse
import json
import sys
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

from playwright.sync_api import sync_playwright


def update_seo(post_id, title=None, description=None, keyphrase=None,
               og_title=None, og_description=None,
               wp_user='edwin', wp_pass=None):
    if not wp_pass:
        print("Error: WordPress password required", file=sys.stderr)
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1400, 'height': 1200})

        print("Logging in...", file=sys.stderr)
        page.goto('https://jetfuel.agency/wp-login.php')
        page.fill('#user_login', wp_user)
        page.fill('#user_pass', wp_pass)
        page.click('#wp-submit')
        page.wait_for_url('**/wp-admin/**', timeout=15000)

        print(f"Opening post {post_id}...", file=sys.stderr)
        page.goto(f'https://jetfuel.agency/wp-admin/post.php?post={post_id}&action=edit')
        page.wait_for_load_state('domcontentloaded', timeout=60000)
        page.wait_for_timeout(8000)

        # Update AIOSEO state and use Gutenberg's save mechanism
        result = page.evaluate('''async (args) => {
            const { title, description, keyphrase, ogTitle, ogDescription } = args;

            // Step 1: Modify AIOSEO's reactive currentPost object
            if (!window.aioseo || !window.aioseo.currentPost) {
                return { error: 'AIOSEO not found' };
            }

            const cp = window.aioseo.currentPost;
            const changes = {};

            if (title) { cp.title = title; changes.title = title; }
            if (description) { cp.description = description; changes.description = description; }
            if (keyphrase) {
                cp.keyphrases = {
                    focus: { keyphrase: keyphrase, score: 0, analysis: {} },
                    additional: cp.keyphrases?.additional || []
                };
                changes.keyphrase = keyphrase;
            }
            if (ogTitle) { cp.og_title = ogTitle; changes.og_title = ogTitle; }
            if (ogDescription) { cp.og_description = ogDescription; changes.og_description = ogDescription; }

            // Step 2: Find the hidden input 'aioseo-post-settings' and populate it
            // This is what AIOSEO reads on wp save_post hook
            const hiddenInput = document.querySelector('input[name="aioseo-post-settings"]');
            if (hiddenInput) {
                hiddenInput.value = JSON.stringify(cp);
                changes._hiddenInputSet = true;
            }

            // Step 3: Mark AIOSEO as loaded so its save_post handler processes the data
            const loadedInput = document.querySelector('input[name="aioseo loaded"]');
            if (loadedInput) {
                loadedInput.value = '1';
            }
            const updatesInput = document.querySelector('input[name="aioseo run updates"]');
            if (updatesInput) {
                updatesInput.value = '1';
            }

            // Step 4: Dispatch a Gutenberg save via wp.data
            // This triggers the actual WordPress save_post hook which AIOSEO listens to
            if (window.wp && wp.data && wp.data.dispatch) {
                try {
                    // Mark the post as dirty so the save button enables
                    wp.data.dispatch('core/editor').editPost({ meta: { _aioseo_save: Date.now().toString() } });

                    // Wait a beat then trigger save
                    await new Promise(r => setTimeout(r, 500));
                    await wp.data.dispatch('core/editor').savePost();

                    await new Promise(r => setTimeout(r, 3000));
                    return { success: true, changes: changes, method: 'gutenberg_dispatch' };
                } catch(e) {
                    return { error: e.message, method: 'gutenberg_failed', changes: changes };
                }
            }

            return { error: 'wp.data not available', changes: changes };
        }''', {
            'title': title,
            'description': description,
            'keyphrase': keyphrase,
            'ogTitle': og_title,
            'ogDescription': og_description,
        })

        print(f"Result: {json.dumps(result)}", file=sys.stderr)

        # Wait for save to complete
        page.wait_for_timeout(3000)

        browser.close()

    updated = []
    if title: updated.append('title')
    if description: updated.append('description')
    if keyphrase: updated.append('keyphrase')
    if og_title: updated.append('og_title')
    if og_description: updated.append('og_description')

    return {
        'success': result.get('success', False),
        'post_id': post_id,
        'updated': updated,
        'detail': result,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--post-id', type=int, required=True)
    parser.add_argument('--title')
    parser.add_argument('--description')
    parser.add_argument('--keyphrase')
    parser.add_argument('--og-title')
    parser.add_argument('--og-description')
    parser.add_argument('--wp-pass', required=True)
    args = parser.parse_args()

    result = update_seo(
        post_id=args.post_id, title=args.title,
        description=args.description, keyphrase=args.keyphrase,
        og_title=args.og_title, og_description=args.og_description,
        wp_pass=args.wp_pass,
    )
    print(json.dumps(result, indent=2))
