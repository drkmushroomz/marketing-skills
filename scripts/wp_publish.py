"""
Publish a blog post to jetfuel.agency WordPress via REST API.
Usage:
  python3 wp_publish.py --title "Title" --content-file content.html --slug "my-slug" \
    --categories "68,155" --tags "ecommerce" --excerpt "Meta description" --password "app pass"
"""
import argparse
import base64
import json
import requests
import sys

API_BASE = "https://jetfuel.agency/wp-json/wp/v2"
USERNAME = "edwin"
DEFAULT_AUTHOR = 1


def publish_post(title, content, slug=None, categories=None, tags=None,
                 excerpt=None, status="draft", author=1, password=None, featured_media=None):
    """Publish a post to WordPress."""
    if not password:
        print("Error: WordPress app password required", file=sys.stderr)
        sys.exit(1)

    creds = base64.b64encode(f"{USERNAME}:{password}".encode()).decode()
    headers = {
        "Authorization": f"Basic {creds}",
        "Content-Type": "application/json",
    }

    # Resolve tag names to IDs (create if they don't exist)
    tag_ids = []
    if tags:
        for tag_name in tags:
            tag_name = tag_name.strip()
            if not tag_name:
                continue
            # Search for existing tag
            resp = requests.get(f"{API_BASE}/tags", params={"search": tag_name}, headers=headers)
            existing = resp.json()
            if existing and isinstance(existing, list):
                # Find exact match
                match = next((t for t in existing if t["name"].lower() == tag_name.lower()), None)
                if match:
                    tag_ids.append(match["id"])
                    continue
            # Create new tag
            resp = requests.post(f"{API_BASE}/tags", json={"name": tag_name}, headers=headers)
            if resp.status_code == 201:
                tag_ids.append(resp.json()["id"])
                print(f"  Created tag: {tag_name} (ID: {resp.json()['id']})", file=sys.stderr)
            elif resp.status_code == 400 and "term_exists" in resp.text:
                # Tag exists with slightly different name
                tag_ids.append(resp.json().get("data", {}).get("term_id", 0))

    post_data = {
        "title": title,
        "content": content,
        "status": status,
        "author": author,
    }

    if slug:
        post_data["slug"] = slug
    if categories:
        post_data["categories"] = categories
    if tag_ids:
        post_data["tags"] = tag_ids
    if excerpt:
        post_data["excerpt"] = excerpt
    if featured_media:
        post_data["featured_media"] = featured_media

    resp = requests.post(f"{API_BASE}/posts", json=post_data, headers=headers)

    if resp.status_code == 201:
        data = resp.json()
        result = {
            "success": True,
            "post_id": data["id"],
            "title": data["title"]["rendered"],
            "slug": data["slug"],
            "status": data["status"],
            "edit_link": f"https://jetfuel.agency/wp-admin/post.php?post={data['id']}&action=edit",
            "preview_link": data["link"] + "?preview=true" if data["status"] == "draft" else data["link"],
            "categories": data.get("categories", []),
            "tags": data.get("tags", []),
        }
        return result
    else:
        return {
            "success": False,
            "status_code": resp.status_code,
            "error": resp.json().get("message", resp.text[:200]),
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Publish to jetfuel.agency WordPress")
    parser.add_argument("--title", required=True)
    parser.add_argument("--content", help="HTML content string")
    parser.add_argument("--content-file", help="Path to HTML content file")
    parser.add_argument("--slug", help="URL slug")
    parser.add_argument("--categories", help="Comma-separated category IDs")
    parser.add_argument("--tags", help="Comma-separated tag names")
    parser.add_argument("--excerpt", help="Meta description / excerpt")
    parser.add_argument("--status", default="draft", choices=["draft", "publish", "pending"])
    parser.add_argument("--author", type=int, default=DEFAULT_AUTHOR)
    parser.add_argument("--password", required=True, help="WordPress app password")
    parser.add_argument("--featured-media", type=int, help="Featured image media ID")

    args = parser.parse_args()

    # Get content
    content = args.content
    if args.content_file:
        with open(args.content_file, "r", encoding="utf-8") as f:
            content = f.read()

    if not content:
        print("Error: --content or --content-file required", file=sys.stderr)
        sys.exit(1)

    # Parse categories
    categories = None
    if args.categories:
        categories = [int(c.strip()) for c in args.categories.split(",")]

    # Parse tags
    tags = None
    if args.tags:
        tags = [t.strip() for t in args.tags.split(",")]

    result = publish_post(
        title=args.title,
        content=content,
        slug=args.slug,
        categories=categories,
        tags=tags,
        excerpt=args.excerpt,
        status=args.status,
        author=args.author,
        password=args.password,
        featured_media=args.featured_media,
    )

    print(json.dumps(result, indent=2))
