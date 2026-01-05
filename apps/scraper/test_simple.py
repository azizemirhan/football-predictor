"""
Simple test for SofaScore API endpoints
Direct API calls without using the full scraper infrastructure
"""

import asyncio
import httpx
import json


async def test_api_endpoints():
    """Test all team data endpoints directly"""

    BASE_URL = "https://api.sofascore.com/api/v1"
    TEAM_ID = 17  # Manchester City

    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        results = {}

        # 1. Team Details
        print("\n1. Testing: Team Details")
        try:
            url = f"{BASE_URL}/team/{TEAM_ID}"
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                team_name = data.get("team", {}).get("name")
                venue = data.get("team", {}).get("venue", {}).get("stadium", {}).get("name")
                print(f"   ✓ Team: {team_name}")
                print(f"   ✓ Venue: {venue}")
                results["team_details"] = data
            else:
                print(f"   ✗ Failed: {response.status_code}")
        except Exception as e:
            print(f"   ✗ Error: {e}")

        # 2. Team Players/Squad
        print("\n2. Testing: Team Players")
        try:
            url = f"{BASE_URL}/team/{TEAM_ID}/players"
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                players = data.get("players", [])
                print(f"   ✓ Players found: {len(players)}")
                results["players"] = data
            else:
                print(f"   ✗ Failed: {response.status_code}")
        except Exception as e:
            print(f"   ✗ Error: {e}")

        # 3. Recent Matches
        print("\n3. Testing: Recent Matches")
        try:
            url = f"{BASE_URL}/team/{TEAM_ID}/events/last/10"
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                events = data.get("events", [])
                print(f"   ✓ Recent matches: {len(events)}")
                results["recent_matches"] = data
            else:
                print(f"   ✗ Failed: {response.status_code}")
        except Exception as e:
            print(f"   ✗ Error: {e}")

        # 4. Upcoming Matches
        print("\n4. Testing: Upcoming Matches")
        try:
            url = f"{BASE_URL}/team/{TEAM_ID}/events/next/10"
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                events = data.get("events", [])
                print(f"   ✓ Upcoming matches: {len(events)}")
                results["upcoming_matches"] = data
            else:
                print(f"   ✗ Failed: {response.status_code}")
        except Exception as e:
            print(f"   ✗ Error: {e}")

        # 5. Transfers
        print("\n5. Testing: Transfers")
        try:
            url = f"{BASE_URL}/team/{TEAM_ID}/transfers"
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                transfers_in = data.get("transfersIn", [])
                transfers_out = data.get("transfersOut", [])
                print(f"   ✓ Transfers in: {len(transfers_in)}")
                print(f"   ✓ Transfers out: {len(transfers_out)}")
                results["transfers"] = data
            else:
                print(f"   ✗ Failed: {response.status_code}")
        except Exception as e:
            print(f"   ✗ Error: {e}")

        # 6. Team Statistics
        print("\n6. Testing: Team Statistics")
        try:
            url = f"{BASE_URL}/team/{TEAM_ID}/unique-tournament/17/season/current/statistics"
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✓ Statistics retrieved")
                results["statistics"] = data
            else:
                print(f"   ✗ Failed: {response.status_code}")
        except Exception as e:
            print(f"   ✗ Error: {e}")

        # 7. Trophies
        print("\n7. Testing: Trophies")
        try:
            url = f"{BASE_URL}/team/{TEAM_ID}/trophies"
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                trophies = data.get("trophies", [])
                print(f"   ✓ Trophies: {len(trophies)}")
                results["trophies"] = data
            else:
                print(f"   ✗ Failed: {response.status_code}")
        except Exception as e:
            print(f"   ✗ Error: {e}")

        # Save results
        output_file = "manchester_city_api_test.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Results saved to: {output_file}")
        print(f"✓ Total endpoints tested: {len(results)}")

        return results


if __name__ == "__main__":
    print("="*80)
    print("SOFASCORE API DIRECT TEST - Manchester City (ID: 17)")
    print("="*80)

    asyncio.run(test_api_endpoints())

    print("\n" + "="*80)
    print("TEST COMPLETED")
    print("="*80 + "\n")
