import os
import sys
import requests

BASE_URL = "https://api.signa.so/v1"


def _auth_headers():
    """Build the auth header from the SIGNA_API_KEY environment variable."""
    api_key = os.environ.get("SIGNA_API_KEY")
    if not api_key:
        raise RuntimeError(
            "SIGNA_API_KEY environment variable not set. "
            "Run: export SIGNA_API_KEY=sig_xxx"
        )
    return {"Authorization": f"Bearer {api_key}"}


def search(query, offices=None, **filters):

    params = {"q": query}
    if offices:
        params["offices"] = offices
    params.update(filters)

    resp = requests.get(f"{BASE_URL}/trademarks", headers=_auth_headers(), params=params)
    resp.raise_for_status()
    return resp.json()


def get(trademark_id):

    resp = requests.get(f"{BASE_URL}/trademarks/{trademark_id}", headers=_auth_headers())
    resp.raise_for_status()
    return resp.json()


def get_media(url):

    resp = requests.get(url, headers=_auth_headers())
    resp.raise_for_status()

    content_type = resp.headers.get("Content-Type", "unknown")
    content_length = resp.headers.get("Content-Length", "unknown")
    print(f"  [get_media] status={resp.status_code} "
          f"content_type={content_type} content_length={content_length}")

    return resp.content


def paginate(query, offices=None, max_pages=5, **filters):

    all_records = []
    cursor = None
    page = 0

    while page < max_pages:
        params = {"q": query}
        if offices:
            params["offices"] = offices
        if cursor:
            params["cursor"] = cursor
        params.update(filters)

        resp = requests.get(f"{BASE_URL}/trademarks", headers=_auth_headers(), params=params)
        resp.raise_for_status()
        payload = resp.json()

        page_records = payload.get("data", [])
        all_records.extend(page_records)
        page += 1

        print(f"  [paginate] page={page} records={len(page_records)} "
              f"has_more={payload.get('has_more')} cursor={payload.get('pagination', {}).get('cursor')}")

        if not payload.get("has_more"):
            break
        cursor = payload.get("pagination", {}).get("cursor")
        if not cursor:
            # has_more is true but no cursor returned — stop rather than loop forever
            print("  [paginate] WARNING: has_more=True but no cursor returned. Stopping.")
            break

    return all_records


def main():
    """Demonstrating all four functions against a common query."""
    query = "apple"
    office = "uspto"

    print(f"=== search(query='{query}', offices='{office}') ===")
    results = search(query, offices=office)
    print(f"  {len(results.get('data', []))} records returned, "
          f"has_more={results.get('has_more')}")

    if not results.get("data"):
        print("No results to demo get()/get_media() with. Exiting.")
        return

    first_record = results["data"][0]
    record_id = first_record["id"]

    print(f"\n=== get(id='{record_id}') ===")
    record = get(record_id)
    print(f"  mark_text={record.get('mark_text')}  office_code={record.get('office_code')}")
    # Fields that should NOT appear on a single-record fetch, per Task 2 §1
    for field in ("relevance_score", "match_explanation", "highlights", "search_meta"):
        present = field in record or (field in first_record and field not in record)
        print(f"  '{field}' present on single-record response: {field in record}")

    print(f"\n=== get_media() ===")
    # Known quirk (Task 2): primary_image_url is often absent on the get() response even
    # when has_media=True — the image data moves to a media[] array instead. Check both,
    # explicitly, rather than silently falling back to the search record (which masked
    # this exact finding in an earlier version of this script).
    media_url = None
    if record.get("primary_image_url"):
        media_url = record["primary_image_url"]
        print(f"  using get() record's primary_image_url")
    elif record.get("media"):
        media_url = record["media"][0]["url"]
        print(f"  get() record has no primary_image_url despite has_media={record.get('has_media')}; "
              f"falling back to media[0].url from the get() response's own media[] array "
              f"(NOTE: is_primary on media[] entries is unreliable — see get() docstring)")
    else:
        print(f"  record {record_id} has no usable media field on the get() response "
              f"(has_media={record.get('has_media')}) — this itself is worth flagging if it recurs")

    if media_url:
        image_bytes = get_media(media_url)
        print(f"  downloaded {len(image_bytes)} bytes")

    print(f"\n=== paginate(query='{query}', offices='{office}', max_pages=3) ===")
    all_records = paginate(query, offices=office, max_pages=3)
    print(f"  total records collected across pages: {len(all_records)}")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except requests.HTTPError as e:
        print(f"API error: {e.response.status_code} — {e.response.text}", file=sys.stderr)
        sys.exit(1)
