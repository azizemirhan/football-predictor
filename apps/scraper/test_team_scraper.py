"""
Test script for SofaScore team data scraping
Example: Manchester City (team_id=17)
"""

import asyncio
import json
from scrapers.sofascore import SofascoreScraper


async def test_team_details():
    """Test scraping team basic details"""
    print("\n" + "="*80)
    print("Testing: Team Details")
    print("="*80)

    scraper = SofascoreScraper()
    details = await scraper.scrape(scrape_type="team_details", team_id=17)

    print(json.dumps(details, indent=2, ensure_ascii=False))
    print(f"\n✓ Team name: {details.get('name')}")
    print(f"✓ Venue: {details.get('venue', {}).get('name')}")
    print(f"✓ Manager: {details.get('manager', {}).get('name')}")


async def test_team_squad():
    """Test scraping team squad"""
    print("\n" + "="*80)
    print("Testing: Team Squad")
    print("="*80)

    scraper = SofascoreScraper()
    squad = await scraper.scrape(scrape_type="team_squad", team_id=17)

    print(f"\n✓ Total players: {len(squad)}")
    print("\nSample players:")
    for player in squad[:5]:
        print(f"  - {player.get('name')} ({player.get('position')}) - Jersey #{player.get('jersey_number')}")


async def test_team_matches():
    """Test scraping team matches"""
    print("\n" + "="*80)
    print("Testing: Team Matches (Last 5)")
    print("="*80)

    scraper = SofascoreScraper()
    matches = await scraper.scrape(scrape_type="team_matches", team_id=17, match_type="last", count=5)

    print(f"\n✓ Total matches: {len(matches)}")
    print("\nRecent matches:")
    for match in matches:
        home = match.get('home_team')
        away = match.get('away_team')
        score = f"{match.get('home_score', '?')}-{match.get('away_score', '?')}"
        print(f"  - {home} vs {away}: {score}")


async def test_team_transfers():
    """Test scraping team transfers"""
    print("\n" + "="*80)
    print("Testing: Team Transfers")
    print("="*80)

    scraper = SofascoreScraper()
    transfers = await scraper.scrape(scrape_type="team_transfers", team_id=17)

    print(f"\n✓ Transfers in: {len(transfers.get('transfers_in', []))}")
    print(f"✓ Transfers out: {len(transfers.get('transfers_out', []))}")

    if transfers.get('transfers_in'):
        print("\nRecent signings:")
        for transfer in transfers['transfers_in'][:3]:
            print(f"  - {transfer.get('player_name')} from {transfer.get('from_team')}")
            print(f"    Fee: {transfer.get('transfer_fee_description', 'N/A')}")


async def test_team_stats():
    """Test scraping team statistics"""
    print("\n" + "="*80)
    print("Testing: Team Statistics")
    print("="*80)

    scraper = SofascoreScraper()
    stats = await scraper.scrape(scrape_type="team_stats", team_id=17)

    print(json.dumps(stats, indent=2, ensure_ascii=False))


async def test_team_trophies():
    """Test scraping team trophies"""
    print("\n" + "="*80)
    print("Testing: Team Trophies")
    print("="*80)

    scraper = SofascoreScraper()

    # Note: trophies endpoint is called within scrape_complete_team_data
    # For individual testing, we'll need to call it directly
    await scraper.init_session()
    try:
        trophies = await scraper.scrape_team_trophies(17)
        print(f"\n✓ Total trophies: {len(trophies)}")

        if trophies:
            print("\nRecent trophies:")
            for trophy in trophies[:5]:
                print(f"  - {trophy.get('tournament_name')} ({trophy.get('season')})")
    finally:
        await scraper.close_session()


async def test_complete_team_data():
    """Test scraping ALL team data at once"""
    print("\n" + "="*80)
    print("Testing: COMPLETE Team Data (Manchester City)")
    print("="*80)

    scraper = SofascoreScraper()
    complete_data = await scraper.scrape(
        scrape_type="team_complete",
        team_id=17,
        include_player_stats=False  # Set to True to get detailed player stats (slower)
    )

    print("\n" + "-"*80)
    print("DATA SUMMARY")
    print("-"*80)

    # Team details
    team_name = complete_data.get('team_details', {}).get('name', 'N/A')
    venue = complete_data.get('team_details', {}).get('venue', {}).get('name', 'N/A')
    manager = complete_data.get('team_details', {}).get('manager', {}).get('name', 'N/A')

    print(f"\n✓ Team: {team_name}")
    print(f"✓ Venue: {venue}")
    print(f"✓ Manager: {manager}")

    # Squad
    squad_size = len(complete_data.get('squad', []))
    print(f"\n✓ Squad size: {squad_size} players")

    # Matches
    recent_matches = len(complete_data.get('recent_matches', []))
    upcoming_matches = len(complete_data.get('upcoming_matches', []))
    print(f"✓ Recent matches: {recent_matches}")
    print(f"✓ Upcoming matches: {upcoming_matches}")

    # Transfers
    transfers_in = len(complete_data.get('transfers', {}).get('transfers_in', []))
    transfers_out = len(complete_data.get('transfers', {}).get('transfers_out', []))
    print(f"✓ Transfers in: {transfers_in}")
    print(f"✓ Transfers out: {transfers_out}")

    # Trophies
    trophies = len(complete_data.get('trophies', []))
    print(f"✓ Trophies: {trophies}")

    # Save to file
    output_file = "/home/user/football-predictor/apps/scraper/manchester_city_complete.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(complete_data, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Complete data saved to: {output_file}")
    print(f"✓ File size: {len(json.dumps(complete_data))} bytes")

    return complete_data


async def main():
    """Run all tests"""
    print("\n")
    print("="*80)
    print("SOFASCORE TEAM DATA SCRAPER - COMPREHENSIVE TEST")
    print("Team: Manchester City (ID: 17)")
    print("="*80)

    try:
        # Individual component tests
        await test_team_details()
        await test_team_squad()
        await test_team_matches()
        await test_team_transfers()
        await test_team_stats()
        await test_team_trophies()

        # Complete data test
        await test_complete_team_data()

        print("\n" + "="*80)
        print("✓ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
