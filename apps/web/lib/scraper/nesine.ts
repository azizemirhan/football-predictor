
import { NovadaClient } from './novada';
import puppeteer from 'puppeteer'; 

// MTID to Market Name Mapping
const MARKET_NAMES: Record<number, string> = {
  1: 'MATCH_RESULT',        // Maç Sonucu (1X2)
  7: 'OVER_UNDER_2_5',      // Alt/Üst 2.5
  13: 'HANDICAP',           // Handikap
  14: 'DOUBLE_CHANCE',      // Çifte Şans
  29: 'BTTS',               // Karşılıklı Gol (Both Teams to Score)
  38: 'TOTAL_GOALS',        // Toplam Gol
  48: 'FIRST_HALF_RESULT',  // İlk Yarı Sonucu
  212: 'HANDICAP_RESULT',   // Handikaplı Maç Sonucu
  268: 'OVER_UNDER_1_5',    // Alt/Üst 1.5
  326: 'RESULT_OVER_UNDER', // Maç Sonucu + Alt/Üst
  342: 'FIRST_HALF_OVER_UNDER', // İY Alt/Üst
  414: 'OVER_UNDER_3_5',    // Alt/Üst 3.5
  450: 'CORRECT_SCORE',     // Doğru Skor
  452: 'HT_FT',             // İY/MS
  587: 'TEAM_GOALS',        // Takım Gol Sayısı
};

export interface ScrapedMarket {
  mtid: number;
  marketType: string;
  outcomes: { name: string; odds: number }[];
}

export interface ScrapedMatch {
  source: string;
  id: string;
  code: string;
  homeTeam: string;
  awayTeam: string;
  date: string;
  time: string;
  timestamp: number;
  markets: ScrapedMarket[];
  // Legacy 1X2 for backward compatibility
  odds?: { home: number; draw: number; away: number };
}

export async function scrapeNesine(proxyClient: NovadaClient) {
  console.log('Starting Nesine scrape (All Markets v3)...');
  
  const browser = await puppeteer.launch({
    headless: true,
    args: [
      `--proxy-server=${proxyClient.getAnonymizedProxyUrl()}`,
      '--no-sandbox',
      '--disable-setuid-sandbox'
    ]
  });

  try {
    const page = await browser.newPage();
    
    // Authenticate Proxy
    if (process.env.NOVADA_PROXY_USER && process.env.NOVADA_PROXY_PASS) {
      await page.authenticate({
        username: process.env.NOVADA_PROXY_USER,
        password: process.env.NOVADA_PROXY_PASS
      });
    }

    await page.setExtraHTTPHeaders({
        'Referer': 'https://www.nesine.com/',
        'Origin': 'https://www.nesine.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    });

    const apiUrl = 'https://cdnbulten.nesine.com/api/bulten/getprebultenfull';
    console.log('Navigating to API:', apiUrl);
    
    await page.goto(apiUrl, { waitUntil: 'networkidle0', timeout: 60000 });

    const content = await page.evaluate(() => document.body.innerText);
    const data = JSON.parse(content);
    
    if (!data.sg || !data.sg.EA) {
        throw new Error('Invalid Nesine API response structure');
    }

    const matches: ScrapedMatch[] = data.sg.EA
      .filter((evt: any) => evt.TYPE === 1) // Only football matches
      .map((evt: any) => {
        // Extract ALL markets
        const markets: ScrapedMarket[] = (evt.MA || []).map((m: any) => {
          const mtid = m.MTID;
          const marketType = MARKET_NAMES[mtid] || `UNKNOWN_${mtid}`;
          const outcomes = (m.OCA || []).map((o: any) => ({
            name: o.ON || String(o.N),
            odds: Number(o.O)
          }));
          return { mtid, marketType, outcomes };
        });

        // Legacy 1X2 extraction for backward compat
        const market1x2 = markets.find(m => m.mtid === 1);
        const odds = market1x2 ? {
          home: market1x2.outcomes.find(o => o.name === '1' || o.name === 'MS1')?.odds || 0,
          draw: market1x2.outcomes.find(o => o.name === 'X')?.odds || 0,
          away: market1x2.outcomes.find(o => o.name === '2' || o.name === 'MS2')?.odds || 0
        } : undefined;

        return {
          source: 'Nesine',
          id: String(evt.EV),
          code: String(evt.C),
          homeTeam: evt.HN,
          awayTeam: evt.AN,
          date: evt.D,
          time: evt.T,
          timestamp: evt.ESD,
          markets,
          odds
        };
      })
      .filter((m: ScrapedMatch) => m.markets.length > 0);

    console.log(`Parsed ${matches.length} matches with ${matches.reduce((a, m) => a + m.markets.length, 0)} total markets.`);
    
    // Save for debug
    const fs = require('fs');
    fs.writeFileSync('/home/aziz/.gemini/antigravity/brain/5bae58cd-3463-46fa-b376-8a20561c480b/nesine_all_markets.json', JSON.stringify(matches.slice(0, 5), null, 2));

    return { success: true, count: matches.length, matches };
    
  } catch (error) {
    console.error('Scraping Error:', error);
    return { success: false, error: String(error) };
  } finally {
    await browser.close();
  }
}
