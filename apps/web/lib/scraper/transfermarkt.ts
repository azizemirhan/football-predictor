import cheerio from 'cheerio';

export interface TransfermarktPlayer {
  jerseyNumber: string;
  name: string;
  position: string;
  birthDate: string;
  age: number | null;
  nationality: string;
  nationalityFlag?: string;
  height: string;
  foot: string;
  joinedDate: string;
  contractEnd: string;
  marketValue: string;
  profileUrl: string;
  imageUrl?: string;
  previousClub?: string;
}

export interface TransfermarktPlayerStat {
  name: string;
  position: string;
  goals?: number;
  assists?: number;
  imageUrl?: string;
}

export interface TransfermarktTransfer {
  playerName: string;
  position: string;
  age?: number;
  nationality?: string;
  fromClub?: string;
  toClub?: string;
  fee: string;
  type: 'in' | 'out';
  season?: string;
  imageUrl?: string;
}

export interface TransfermarktClubInfo {
  officialName: string;
  address: string;
  phone: string;
  website: string;
  founded: string;
  stadium: string;
  stadiumCapacity: string;
  squadSize: number;
  averageAge: string;
  foreigners: number;
  nationalPlayers: number;
  totalMarketValue: string;
  leagueRank: string;
  coachName: string;
  honours: { name: string; count: number }[];
}

export interface TransfermarktTeamData {
  name: string;
  logo: string;
  league: string;
  clubInfo: TransfermarktClubInfo;
  squad: TransfermarktPlayer[];
  topScorers: TransfermarktPlayerStat[];
  topAssists: TransfermarktPlayerStat[];
  transfers: {
    arrivals: TransfermarktTransfer[];
    departures: TransfermarktTransfer[];
    balance: {
      income: string;
      expenditure: string;
      balance: string;
    };
  };
}

// All English League Teams - Transfermarkt IDs (with aliases)
// Premier League (20 Teams) + Championship (24 Teams)
const TM_CLUB_IDS: Record<string, { id: number; slug: string }> = {
  // === PREMIER LEAGUE (2025-26) ===
  'Arsenal': { id: 11, slug: 'fc-arsenal' },
  'Aston Villa': { id: 405, slug: 'aston-villa' },
  'Villa': { id: 405, slug: 'aston-villa' },
  'Bournemouth': { id: 989, slug: 'afc-bournemouth' },
  'AFC Bournemouth': { id: 989, slug: 'afc-bournemouth' },
  'Brentford': { id: 1148, slug: 'fc-brentford' },
  'Brighton & Hove Albion': { id: 1237, slug: 'brighton-hove-albion' },
  'Brighton': { id: 1237, slug: 'brighton-hove-albion' },
  'Chelsea': { id: 631, slug: 'fc-chelsea' },
  'Crystal Palace': { id: 873, slug: 'crystal-palace' },
  'Everton': { id: 29, slug: 'fc-everton' },
  'Fulham': { id: 931, slug: 'fc-fulham' },
  'Ipswich Town': { id: 677, slug: 'ipswich-town' },
  'Ipswich': { id: 677, slug: 'ipswich-town' },
  'Liverpool': { id: 31, slug: 'fc-liverpool' },
  'Manchester City': { id: 281, slug: 'manchester-city' },
  'Man City': { id: 281, slug: 'manchester-city' },
  'Manchester United': { id: 985, slug: 'manchester-united' },
  'Man United': { id: 985, slug: 'manchester-united' },
  'Man Utd': { id: 985, slug: 'manchester-united' },
  'Newcastle United': { id: 762, slug: 'newcastle-united' },
  'Newcastle': { id: 762, slug: 'newcastle-united' },
  'Nottingham Forest': { id: 703, slug: 'nottingham-forest' },
  'Nottm Forest': { id: 703, slug: 'nottingham-forest' },
  'Southampton': { id: 180, slug: 'fc-southampton' },
  'Tottenham Hotspur': { id: 148, slug: 'tottenham-hotspur' },
  'Tottenham': { id: 148, slug: 'tottenham-hotspur' },
  'Spurs': { id: 148, slug: 'tottenham-hotspur' },
  'West Ham United': { id: 379, slug: 'west-ham-united' },
  'West Ham': { id: 379, slug: 'west-ham-united' },
  'Wolverhampton Wanderers': { id: 543, slug: 'wolverhampton-wanderers' },
  'Wolverhampton': { id: 543, slug: 'wolverhampton-wanderers' },
  'Wolves': { id: 543, slug: 'wolverhampton-wanderers' },
  
  // === CHAMPIONSHIP (2025-26) ===
  'Birmingham City': { id: 337, slug: 'birmingham-city' },
  'Birmingham': { id: 337, slug: 'birmingham-city' },
  'Blackburn Rovers': { id: 164, slug: 'blackburn-rovers' },
  'Blackburn': { id: 164, slug: 'blackburn-rovers' },
  'Bristol City': { id: 1024, slug: 'bristol-city' },
  'Bristol': { id: 1024, slug: 'bristol-city' },
  'Burnley': { id: 1132, slug: 'fc-burnley' },
  'Cardiff City': { id: 2593, slug: 'cardiff-city' },
  'Cardiff': { id: 2593, slug: 'cardiff-city' },
  'Coventry City': { id: 354, slug: 'coventry-city' },
  'Coventry': { id: 354, slug: 'coventry-city' },
  'Derby County': { id: 22, slug: 'derby-county' },
  'Derby': { id: 22, slug: 'derby-county' },
  'Hull City': { id: 2602, slug: 'hull-city' },
  'Hull': { id: 2602, slug: 'hull-city' },
  'Leeds United': { id: 399, slug: 'leeds-united' },
  'Leeds': { id: 399, slug: 'leeds-united' },
  'Leicester City': { id: 1003, slug: 'leicester-city' },
  'Leicester': { id: 1003, slug: 'leicester-city' },
  'Luton Town': { id: 1031, slug: 'luton-town' },
  'Luton': { id: 1031, slug: 'luton-town' },
  'Middlesbrough': { id: 432, slug: 'middlesbrough-fc' },
  'Millwall': { id: 1577, slug: 'fc-millwall' },
  'Norwich City': { id: 1123, slug: 'norwich-city' },
  'Norwich': { id: 1123, slug: 'norwich-city' },
  'Oxford United': { id: 1285, slug: 'oxford-united' },
  'Oxford': { id: 1285, slug: 'oxford-united' },
  'Plymouth Argyle': { id: 334, slug: 'plymouth-argyle' },
  'Plymouth': { id: 334, slug: 'plymouth-argyle' },
  'Portsmouth': { id: 718, slug: 'fc-portsmouth' },
  'Preston North End': { id: 1134, slug: 'preston-north-end' },
  'Preston': { id: 1134, slug: 'preston-north-end' },
  'Queens Park Rangers': { id: 1039, slug: 'queens-park-rangers' },
  'QPR': { id: 1039, slug: 'queens-park-rangers' },
  'Sheffield United': { id: 350, slug: 'sheffield-united' },
  'Sheffield Utd': { id: 350, slug: 'sheffield-united' },
  'Sheffield Wednesday': { id: 867, slug: 'sheffield-wednesday' },
  'Sheffield Wed': { id: 867, slug: 'sheffield-wednesday' },
  'Stoke City': { id: 512, slug: 'stoke-city' },
  'Stoke': { id: 512, slug: 'stoke-city' },
  'Sunderland': { id: 289, slug: 'sunderland-afc' },
  'Swansea City': { id: 2288, slug: 'swansea-city' },
  'Swansea': { id: 2288, slug: 'swansea-city' },
  'Watford': { id: 1010, slug: 'fc-watford' },
  'West Bromwich Albion': { id: 984, slug: 'west-bromwich-albion' },
  'West Brom': { id: 984, slug: 'west-bromwich-albion' },
  'WBA': { id: 984, slug: 'west-bromwich-albion' },
};

async function fetchWithRetry(url: string, retries = 3): Promise<string | null> {
  const headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
    'Cache-Control': 'no-cache',
  };

  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch(url, { headers });
      if (response.ok) {
        return await response.text();
      }
      console.log(`Fetch attempt ${i + 1} failed with status ${response.status}`);
    } catch (error) {
      console.log(`Fetch attempt ${i + 1} error:`, error);
    }
    await new Promise(r => setTimeout(r, 1000 * (i + 1)));
  }
  return null;
}

export async function scrapeTransfermarkt(teamName: string, tmClubId?: number): Promise<TransfermarktTeamData | null> {
  console.log(`Starting Transfermarkt scrape for: ${teamName}`);
  
  const clubInfo = TM_CLUB_IDS[teamName];
  const clubId = tmClubId || clubInfo?.id;
  const slug = clubInfo?.slug || teamName.toLowerCase().replace(/\s+/g, '-');
  
  if (!clubId) {
    console.error(`Unknown Transfermarkt club ID for: ${teamName}`);
    return null;
  }

  const result: TransfermarktTeamData = {
    name: teamName,
    logo: `https://tmssl.akamaized.net/images/wappen/head/${clubId}.png`,
    league: '',
    clubInfo: {
      officialName: teamName,
      address: '',
      phone: '',
      website: '',
      founded: '',
      stadium: '',
      stadiumCapacity: '',
      squadSize: 0,
      averageAge: '',
      foreigners: 0,
      nationalPlayers: 0,
      totalMarketValue: '',
      leagueRank: '',
      coachName: '',
      honours: [],
    },
    squad: [],
    topScorers: [],
    topAssists: [],
    transfers: { 
      arrivals: [], 
      departures: [],
      balance: { income: '', expenditure: '', balance: '' }
    }
  };

  try {
    // Fetch squad page
    const squadUrl = `https://www.transfermarkt.com.tr/${slug}/kader/verein/${clubId}/saison_id/2025`;
    console.log(`Fetching squad from: ${squadUrl}`);
    
    const squadHtml = await fetchWithRetry(squadUrl);
    if (squadHtml) {
      const $ = cheerio.load(squadHtml);
      
      // Team name
      const headerName = $('h1[data-header-headline]').text().trim() || 
                         $('header h1').text().trim() ||
                         $('h1').first().text().trim();
      if (headerName) result.name = headerName;
      
      // League
      const leagueEl = $('span.data-header__club a').first();
      result.league = leagueEl.text().trim() || '';
    }

    // Fetch DETAILED squad page (plus/1 for extended info)
    const detailedSquadUrl = `https://www.transfermarkt.com.tr/${slug}/kader/verein/${clubId}/saison_id/2025/plus/1`;
    console.log(`Fetching detailed squad from: ${detailedSquadUrl}`);
    
    const detailedSquadHtml = await fetchWithRetry(detailedSquadUrl);
    if (detailedSquadHtml) {
      const $ = cheerio.load(detailedSquadHtml);
      
      // Parse detailed squad table - columns: #, Player, Birth/Age, Nationality, Height, Foot, Joined, PreviousClub, ContractEnd, Value
      $('table.items tbody tr.odd, table.items tbody tr.even').each((_, row) => {
        const $row = $(row);
        const cells = $row.find('td');
        
        // Jersey number from first rn (row number) cell
        const jerseyNumber = $row.find('td.rn_nummer').text().trim() || cells.eq(0).text().trim();
        
        // Player name and image from hauptlink cell
        const nameLink = $row.find('td.hauptlink a').first();
        const name = nameLink.text().trim();
        const profileUrl = nameLink.attr('href') 
          ? `https://www.transfermarkt.com.tr${nameLink.attr('href')}`
          : '';
        const imgEl = $row.find('img.bilderrahmen-fixed, img[data-src]').first();
        const imageUrl = imgEl.attr('data-src') || imgEl.attr('src') || '';
        
        // Position from second table row inside player cell
        const positionEl = $row.find('td.hauptlink').closest('td').find('tr').last().find('td').last();
        const position = positionEl.text().trim() || '';
        
        // Birth date and age from zentriert cells - find the one with date pattern
        let birthDate = '';
        let age: number | null = null;
        $row.find('td.zentriert').each((_, cell) => {
          const text = $(cell).text().trim();
          const birthMatch = text.match(/(\d+\s+\w+\s+\d+)\s*\((\d+)\)/);
          if (birthMatch) {
            birthDate = birthMatch[1];
            age = parseInt(birthMatch[2]);
          }
        });
        
        // Nationality from flag image
        const natImg = $row.find('img.flaggenrahmen').first();
        const nationality = natImg.attr('title') || '';
        
        // Height - look for pattern like 1,87m
        let height = '';
        $row.find('td.zentriert').each((_, cell) => {
          const text = $(cell).text().trim();
          if (text.match(/\d,\d+\s*m/)) {
            height = text;
          }
        });
        
        // Foot preference - look for "ayak" text
        let foot = '';
        $row.find('td.zentriert').each((_, cell) => {
          const text = $(cell).text().trim();
          if (text.includes('ayak')) {
            foot = text;
          }
        });
        
        // Joined date - look for date pattern without age in parentheses
        let joinedDate = '';
        $row.find('td.zentriert').each((_, cell) => {
          const text = $(cell).text().trim();
          if (text.match(/\d+\s+\w+\s+\d{4}$/) && !text.includes('(')) {
            joinedDate = text;
          }
        });
        
        // Contract end date from last zentriert cells
        let contractEnd = '';
        const lastCells = $row.find('td.zentriert').slice(-3);
        lastCells.each((_, cell) => {
          const text = $(cell).text().trim();
          if (text.match(/\d+\s+\w+\s+\d{4}/) && !text.includes('(')) {
            contractEnd = text;
          }
        });
        
        // Previous club from image title in Önceden column
        const previousClubImg = $row.find('td').eq(7).find('img').first();
        const previousClub = previousClubImg.attr('title') || previousClubImg.attr('alt') || '';
        
        // Market value from rechts cell
        const valueEl = $row.find('td.rechts a').first();
        const marketValue = valueEl.text().trim() || '';

        if (name) {
          result.squad.push({
            jerseyNumber,
            name,
            position,
            birthDate,
            age,
            nationality,
            height,
            foot,
            joinedDate,
            contractEnd,
            previousClub,
            marketValue,
            profileUrl,
            imageUrl
          });
        }
      });
      
      result.clubInfo.squadSize = result.squad.length;
      console.log(`Parsed ${result.squad.length} players from detailed squad page`);
    }

    // Fetch main page for basic club info
    const mainUrl = `https://www.transfermarkt.com.tr/${slug}/startseite/verein/${clubId}`;
    console.log(`Fetching main page from: ${mainUrl}`);
    
    const mainHtml = await fetchWithRetry(mainUrl);
    if (mainHtml) {
      const $ = cheerio.load(mainHtml);
      
      // 1. Header Data
      // Squad Size
      const squadSizeText = $('li.data-header__label:contains("Kadro genişliği") span.data-header__content').text().trim();
      result.clubInfo.squadSize = parseInt(squadSizeText) || 0;
      
      // Average Age
      result.clubInfo.averageAge = $('li.data-header__label:contains("Yaş ortalaması") span.data-header__content').text().trim() || '';
      
      // Foreigners
      const foreignersText = $('li.data-header__label:contains("Lejyonerler") span.data-header__content').text().trim();
      result.clubInfo.foreigners = parseInt(foreignersText) || 0;
      
      // National Players
      const natPlayersText = $('li.data-header__label:contains("Milli oyuncular") span.data-header__content').text().trim();
      result.clubInfo.nationalPlayers = parseInt(natPlayersText) || 0;
      
      // Stadium
      const stadiumEl = $('li.data-header__label:contains("Stadyum") span.data-header__content a').first();
      result.clubInfo.stadium = stadiumEl.text().trim() || '';
      const capacityText = $('li.data-header__label:contains("Stadyum") span.tabellenplatz').text().trim();
      result.clubInfo.stadiumCapacity = capacityText.replace(/kapasite/i, '').trim();
      // League Rank
      // Use filter to ensure exact match for "Lig Sıralaması:"
      const rankLabel = $('span.data-header__label').filter((_, el) => /Lig Sıralaması/i.test($(el).contents().filter((_, node) => node.type === 'text').text()));
      // Content is usually a child span, or if we matched the parent, we search inside
      result.clubInfo.leagueRank = rankLabel.find('.data-header__content a').text().trim() || rankLabel.next('.data-header__content').find('a').text().trim() || '';
      
      // Market Value
      const totalValueEl = $('a[href*="marktwertanalyse"]').first();
      result.clubInfo.totalMarketValue = totalValueEl.text().trim() || '';
      
      // Website
      $('li.data-header__label:contains("Web")').each((_, el) => {
        const link = $(el).find('a').first();
        result.clubInfo.website = link.attr('href') || '';
      });

      // 2. Sidebar Data (General Info)
      // Founded
      const foundedLabel = $('span.info-table__content').filter((_, el) => /Kuruluş/i.test($(el).text()));
      result.clubInfo.founded = foundedLabel.next().text().trim() || '';
      
      // Address
      const addressLabel = $('span.info-table__content').filter((_, el) => /Adres/i.test($(el).text()));
      const addressDiv = addressLabel.next('div');
      result.clubInfo.address = addressDiv.text().replace(/\s+/g, ' ').trim() || '';
      
      // Phone
      const phoneLabel = $('span.info-table__content').filter((_, el) => /Tel/i.test($(el).text()));
      result.clubInfo.phone = phoneLabel.next().text().trim() || '';
      
      // Official Name (usually in header h1 but also in sidebar)
      result.clubInfo.officialName = $('h1.data-header__headline-wrapper').text().trim() || '';

      // 3. Coach (Teknik Direktör) - check main page sidebar first
      const coachLabel = $('span.info-table__content').filter((_, el) => /Teknik Direktör|Menejer|Antrenör/i.test($(el).text()));
      result.clubInfo.coachName = coachLabel.next().find('a').first().text().trim() || coachLabel.next().text().trim();
      
      // 4. Honours (Başarılar) - from Header Badges
      result.clubInfo.honours = [];
      $('.data-header__badge-container a').each((_, el) => {
        const title = $(el).attr('title');
        if (title) { // e.g., "1x English Champion"
           const match = title.match(/^(\d+)x\s+(.+)$/);
           if (match) {
             result.clubInfo.honours.push({ count: parseInt(match[1]), name: match[2] });
           } else {
             // Fallback for single trophies or different format
             result.clubInfo.honours.push({ count: 1, name: title });
           }
        }
      });

      // Get transfer balance from main page header - "Güncel transfer bilançosu: +57.30 mil. €"
      const balanceText = $.html();
      const balanceMatch = balanceText.match(/Güncel transfer bilançosu[:\s]*<a[^>]*class="[^"]*(?:greentext|redtext)[^"]*"[^>]*>([^<]+)</i);
      if (balanceMatch) {
        result.transfers.balance.balance = balanceMatch[1].trim();
      }
      
      // Also try to get from regular text pattern
      if (!result.transfers.balance.balance) {
        $('span:contains("transfer bilançosu"), div:contains("transfer bilançosu")').each((_, el) => {
          const text = $(el).html() || '';
          const match = text.match(/([+-]?\d+[,.]\d+\s*mil\.\s*€)/i);
          if (match && !result.transfers.balance.balance) {
            result.transfers.balance.balance = match[1].trim();
          }
        });
      }
      
      // Parse top scorers from main page - "En çok gol atanlar" section
      // HTML structure: h2 is inside a div, table.startseite is sibling after that div
      $('h2:contains("gol atanlar")').each((_, h2) => {
        const parentDiv = $(h2).parent();
        const table = parentDiv.next('table.startseite');
        table.find('tbody tr').each((_, row) => {
          const $row = $(row);
          const nameEl = $row.find('.spielername').first();
          const name = nameEl.text().trim();
          const posEl = $row.find('.spieler-zusatz').first();
          const position = posEl.text().trim();
          const goalsEl = $row.find('td.tore a, td.zentriert').last();
          const goals = parseInt(goalsEl.text().trim()) || 0;
          
          if (name && goals > 0 && result.topScorers.length < 5) {
            result.topScorers.push({ name, goals, position });
          }
        });
      });
      
      // Parse top assists from main page - "En çok asist yapanlar" section
      $('h2:contains("asist yapanlar")').each((_, h2) => {
        const parentDiv = $(h2).parent();
        const table = parentDiv.next('table.startseite');
        table.find('tbody tr').each((_, row) => {
          const $row = $(row);
          const nameEl = $row.find('.spielername').first();
          const name = nameEl.text().trim();
          const posEl = $row.find('.spieler-zusatz').first();
          const position = posEl.text().trim();
          const assistsEl = $row.find('td.zentriert').last();
          const assists = parseInt(assistsEl.text().trim()) || 0;
          
          if (name && assists > 0 && result.topAssists.length < 5) {
            result.topAssists.push({ name, assists, position });
          }
        });
      });
      
      console.log(`Parsed ${result.topScorers.length} scorers and ${result.topAssists.length} assists from main page`);
    }
    
    // If no scorers/assists found from main page, try performance data page
    if (result.topScorers.length === 0) {
      const goalsUrl = `https://www.transfermarkt.com.tr/${slug}/leistungsdaten/verein/${clubId}/reldata/&plus/1`;
      console.log(`Fetching performance data from: ${goalsUrl}`);
      
      const goalsHtml = await fetchWithRetry(goalsUrl);
      if (goalsHtml) {
        const $ = cheerio.load(goalsHtml);
        
        // Performance data table has goals in one of the columns
        $('table.items tbody tr').slice(0, 10).each((_, row) => {
          const $row = $(row);
          const nameLink = $row.find('td.hauptlink a').first();
          const name = nameLink.text().trim();
          
          // Find goals column - typically has "Gol" header
          const cells = $row.find('td');
          let goals = 0;
          let assists = 0;
          
          cells.each((_, cell) => {
            const text = $(cell).text().trim();
            // Try to identify goals and assists by checking numeric values
            const num = parseInt(text);
            if (!isNaN(num) && num > 0 && num < 50) {
              if (goals === 0) goals = num;
              else if (assists === 0) assists = num;
            }
          });
          
          if (name && goals > 0 && result.topScorers.length < 5) {
            result.topScorers.push({ name, goals, position: '' });
          }
          if (name && assists > 0 && result.topAssists.length < 5) {
            result.topAssists.push({ name, assists, position: '' });
          }
        });
        
        // Sort by goals/assists
        result.topScorers.sort((a, b) => (b.goals || 0) - (a.goals || 0));
        result.topAssists.sort((a, b) => (b.assists || 0) - (a.assists || 0));
        
        console.log(`Parsed ${result.topScorers.length} scorers and ${result.topAssists.length} assists from performance data`);
      }
    }

    // Fetch transfer records page for detailed arrivals with fees
    const transfersUrl = `https://www.transfermarkt.com.tr/${slug}/transferrekorde/verein/${clubId}/saison_id/2025`;
    console.log(`Fetching transfer records from: ${transfersUrl}`);
    
    const transfersHtml = await fetchWithRetry(transfersUrl);
    if (transfersHtml) {
      const $ = cheerio.load(transfersHtml);
      
      // Clear arrivals and re-populate with detailed data
      result.transfers.arrivals = [];
      
      // Parse transfer records table
      $('table.items tbody tr.odd, table.items tbody tr.even').each((_, row) => {
        const $row = $(row);
        const cells = $row.find('td');
        
        const nameLink = $row.find('td.hauptlink a').first();
        const playerName = nameLink.text().trim();
        
        const positionEl = $row.find('td').eq(1).find('table tr').last();
        const position = positionEl.text().trim() || '';
        
        const ageCell = cells.eq(2).text().trim();
        const age = parseInt(ageCell) || undefined;
        
        const natImg = $row.find('img.flaggenrahmen').first();
        const nationality = natImg.attr('title') || '';
        
        const fromClubCell = cells.eq(5);
        const fromClub = fromClubCell.find('a').first().text().trim() || '';
        
        const feeCell = cells.eq(6);
        const fee = feeCell.text().trim() || '';
        
        if (playerName && result.transfers.arrivals.length < 10) {
          result.transfers.arrivals.push({
            playerName,
            position,
            age,
            nationality,
            fromClub,
            fee,
            type: 'in',
            season: '25/26'
          });
        }
      });
      // Note: Transfer balance is already fetched from main page header
      // income and expenditure are not available as separate values on Transfermarkt
      
      console.log(`Parsed ${result.transfers.arrivals.length} detailed arrivals`);
    }

    // Fetch departure records page
    const departuresUrl = `https://www.transfermarkt.com.tr/${slug}/rekordabgaenge/verein/${clubId}/saison_id/2025`;
    console.log(`Fetching departure records from: ${departuresUrl}`);
    
    const departuresHtml = await fetchWithRetry(departuresUrl);
    if (departuresHtml) {
      const $ = cheerio.load(departuresHtml);
      
      // Clear departures and re-populate with detailed data
      result.transfers.departures = [];
      
      $('table.items tbody tr.odd, table.items tbody tr.even').each((_, row) => {
        const $row = $(row);
        const cells = $row.find('td');
        
        const nameLink = $row.find('td.hauptlink a').first();
        const playerName = nameLink.text().trim();
        
        const positionEl = $row.find('td').eq(1).find('table tr').last();
        const position = positionEl.text().trim() || '';
        
        const ageCell = cells.eq(2).text().trim();
        const age = parseInt(ageCell) || undefined;
        
        const natImg = $row.find('img.flaggenrahmen').first();
        const nationality = natImg.attr('title') || '';
        
        const toClubCell = cells.eq(5);
        const toClub = toClubCell.find('a').first().text().trim() || '';
        
        const feeCell = cells.eq(6);
        const fee = feeCell.text().trim() || '';
        
        if (playerName && result.transfers.departures.length < 10) {
          result.transfers.departures.push({
            playerName,
            position,
            age,
            nationality,
            toClub,
            fee,
            type: 'out',
            season: '25/26'
          });
        }
      });
      
      console.log(`Parsed ${result.transfers.departures.length} detailed departures`);
    }

    console.log(`Scraped ${result.name}: ${result.squad.length} players, ${result.topScorers.length} scorers, ${result.transfers.arrivals.length} arrivals, ${result.transfers.departures.length} departures`);
    
    if (result.squad.length === 0) {
      console.log('Squad is empty, scraping may have failed');
      return null;
    }
    
    return result;
    
  } catch (error) {
    console.error('Transfermarkt Scraping Error:', error);
    return null;
  }
}
