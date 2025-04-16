# Service health check script
# NOTE: run kubernetes/port-forward.sh before running this script

import requests
import concurrent.futures

BASE_URL = "http://localhost:8080"

NUM_REQUESTS = 50


def create_short_url(url):
    response = requests.post(f"{BASE_URL}/shorten", json={"url": url})
    return response.json()


def access_short_url(short_url):
    # use head request to avoid downloading entire content
    response = requests.head(f"{BASE_URL}/{short_url}", allow_redirects=False)
    return response.status_code, response.headers.get("Location")


def run_test():
    # create some short URLs
    print("Creating short URLs...")
    urls = [
        "https://www.example.com/page1",
        "https://www.example.com/page2",
        "https://www.example.com/page3",
        "https://www.example.com/page4",
        "https://www.example.com/page5",
    ]

    short_urls = []
    for url in urls:
        result = create_short_url(url)
        print(f"Original: {url}")
        print(f"Shortened: {result}")
        short_code = result.get("short_url", "").split("/")[-1]
        short_urls.append(short_code)

    # concurrent access to test load balancing
    print("\nTesting concurrent access to shortened URLs...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for _ in range(NUM_REQUESTS):
            for short_url in short_urls:
                futures.append(executor.submit(access_short_url, short_url))

        for future in concurrent.futures.as_completed(futures):
            status, location = future.result()
            print(f"Status: {status}, Redirects to: {location}")


if __name__ == "__main__":
    try:
        run_test()
    except requests.exceptions.RequestException as e:
        print(
            f"Could not run this test\nMake sure you run kubernetes/port-forward.sh before running this script\n\n{e}"
        )
