#!/usr/bin/env python3

import argparse
import asyncio
from collections import Counter
import aiohttp
import time
import sys


async def check_health(session, base_url):
    """Send request to the health endpoint and return pod info"""
    try:
        async with session.get(f"{base_url}/health") as response:
            if response.status == 200:
                data = await response.json()
                pod_name = data.get("pod_name", "unknown")
                return {
                    "success": True,
                    "pod_name": pod_name,
                    "redis_status": data.get("redis_status"),
                    "db_status": data.get("db_status"),
                }
            else:
                error_text = await response.text()
                return {
                    "success": False,
                    "status": response.status,
                    "error": error_text,
                }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def run_load_test(base_url, num_requests, concurrency):
    """Run load test with specified parameters"""
    connector = aiohttp.TCPConnector(limit=concurrency)
    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        print(f"Starting health endpoint load test")
        print(f"Base URL: {base_url}")
        print(f"Total requests: {num_requests}")
        print(f"Concurrency level: {concurrency}")

        # prepare a batch of `num_requests`
        tasks = [check_health(session, base_url) for _ in range(num_requests)]

        start_time = time.time()

        # dispatch requests
        results = await asyncio.gather(*tasks)

        end_time = time.time()
        total_time = end_time - start_time
        successful = [r for r in results if r.get("success")]
        failed = [r for r in results if not r.get("success")]

        # count pod distribution
        pod_distribution = Counter([r.get("pod_name", "unknown") for r in successful])
        redis_status = Counter([r.get("redis_status") for r in successful])
        db_status = Counter([r.get("db_status") for r in successful])

        print("\n=== Load Test Results ===")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Requests per second: {num_requests / total_time:.2f}")
        print(
            f"Successful requests: {len(successful)} ({len(successful) / num_requests * 100:.1f}%)"
        )
        print(
            f"Failed requests: {len(failed)} ({len(failed) / num_requests * 100:.1f}%)"
        )

        print("\n=== Pod Distribution ===")
        for pod, count in pod_distribution.items():
            print(f"{pod}: {count} requests ({count / len(successful) * 100:.1f}%)")

        print("\n=== Service Status ===")
        print(f"Redis status: {dict(redis_status)}")
        print(f"Database status: {dict(db_status)}")

        if failed:
            print("\n=== Failed Requests ===")
            error_types = Counter([r.get("error", "Unknown error") for r in failed])
            for error, count in error_types.items():
                print(f"{error}: {count} occurrences")


def main():
    parser = argparse.ArgumentParser(description="Load tester for pocketurl")
    parser.add_argument(
        "--url",
        default="http://localhost:5000",
        help="URL of the pocketurl service\nRun `minikube service pocketurl-service --url` to get the URL",
    )
    parser.add_argument(
        "--requests", type=int, default=1000, help="number of requests to send"
    )
    parser.add_argument(
        "--concurrency", type=int, default=10, help="number of concurrent requests"
    )

    args = parser.parse_args()

    if args.requests < 1:
        print("Error: Number of requests must be at least 1")
        sys.exit(1)

    if args.concurrency < 1:
        print("Error: Concurrency level must be at least 1")
        sys.exit(1)

    if args.concurrency > args.requests:
        print(
            f"Warning: Concurrency ({args.concurrency}) is greater than requests ({args.requests})"
        )
        print(f"Setting concurrency to {args.requests}")
        args.concurrency = args.requests

    try:
        asyncio.run(run_load_test(args.url, args.requests, args.concurrency))
    except KeyboardInterrupt:
        print("\nLoad test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during load test: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
