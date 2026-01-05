import { NovadaClient } from './novada';
import puppeteer, { Page } from 'puppeteer';

// Complete Iddaa Market Type Mapping - Turkish Names (61+ types)
const IDDAA_MARKET_NAMES: Record<number, string> = {
  // Maç Sonucu
  1: 'Maç Sonucu',
  3: 'Handikaplı Maç Sonucu',
  4: 'Toplam Gol Aralığı',
  6: 'İlk Gol',
  7: 'Maç Sonucu & Alt/Üst',
  11: 'Skoru İlk Açan Takım',
  12: 'Son Golü Atan Takım',
  17: 'Korner - Maç Sonucu',
  36: 'İlk Yarı Sonucu',
  48: 'Ev Sahibi Alt/Üst',
  49: 'Deplasman Alt/Üst',
  52: 'Hangi Takım Kaç Farkla Kazanır',
  53: 'Ev Sahibi Toplam Gol',
  56: 'Deplasman Toplam Gol',
  60: 'Alt/Üst',
  67: 'İlk Yarı/Maç Sonucu',
  68: 'İlk Yarı Her İki Takım da Gol Atar',
  69: 'Penaltı Var/Yok',
  72: 'Kırmızı Kart Var/Yok',
  77: 'İlk Yarı Çifte Şans',
  84: 'Ev Sahibi Gol Yemeden Kazanır',
  85: 'Kim Daha Fazla Atar',
  86: 'Ev Sahibi Her İki Yarıyı Kazanır',
  87: 'Deplasman Her İki Yarıyı Kazanır',
  88: 'İlk Yarı 1X2',
  89: 'Karşılıklı Gol',
  90: 'İlk Yarı/Maç Sonucu',
  91: 'Tek/Çift',
  92: 'Çifte Şans',
  100: 'Handikap',
  101: 'Alt/Üst',
  603: 'Ev Sahibi Alt/Üst',
  604: 'Deplasman Alt/Üst',
  643: 'Deplasman Gol Yemeden Kazanır',
  644: 'Beraberlik Olur mu?',
  658: 'Deplasman Yarı Kazanır',
  698: 'Maç Sonucu & Karşılıklı Gol',
  699: 'İlk Yarı & Karşılıklı Gol',
  700: 'Alt/Üst & Karşılıklı Gol',
  717: 'İlk Yarı Kim Daha Çok Korner Kullanır',
  718: 'İlk Yarı Toplam Korner Aralığı',
  719: 'İlk Yarı Tek/Çift',
  720: 'Her İki Yarıda Gol',
  722: 'Ev Sahibi İlk Yarı Alt/Üst',
  723: 'Deplasman İlk Yarı Alt/Üst',
  724: 'İlk Yarı Alt/Üst',
  727: 'Ev Sahibi Yarı Kazanır',
  728: 'Deplasman Yarı Kazanır',
  729: 'İlk Yarı & Alt/Üst',
  730: 'İkinci Yarı Sonucu',
  737: 'Her İki Yarıda da Alt/Üst',
  821: 'İlk Yarı Skoru',
  822: 'Doğru Skor',
  823: 'İlk Yarı Toplam Korner Sayısı Alt/Üst',
  824: 'Toplam Korner Sayısı',
  861: 'Oyuncu İlk Golü Atar',
  862: 'Oyuncu Son Golü Atar',
  863: 'Oyuncu Gol Atar',
  864: 'Oyuncu 2+ Gol Atar',
  865: 'Oyuncu Hat-Trick Yapar',
  866: 'Oyuncu Kart Görür',
};

export interface IddaaScrapedMarket {
  mtid: number;
  marketType: string;
  outcomes: { name: string; odds: number; selectionValue?: string }[];
}

export interface IddaaScrapedMatch {
  source: string;
  id: string;
  code: string;
  homeTeam: string;
  awayTeam: string;
  date: string;
  time: string;
  timestamp: number;
  markets: IddaaScrapedMarket[];
  odds?: { home: number; draw: number; away: number };
}

async function fetchEventDetails(page: Page, eventId: string): Promise<any> {
  try {
    const url = `https://sportsbookv2.iddaa.com/sportsbook/event/${eventId}`;
    await page.goto(url, { waitUntil: 'networkidle0', timeout: 30000 });
    const content = await page.evaluate(() => document.body.innerText);
    return JSON.parse(content);
  } catch (error) {
    console.error(`Error fetching event ${eventId}:`, error);
    return null;
  }
}

export async function scrapeIddaa(proxyClient: NovadaClient) {
  console.log('Starting Iddaa scrape (Full Markets)...');
  
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
    
    if (process.env.NOVADA_PROXY_USER && process.env.NOVADA_PROXY_PASS) {
      await page.authenticate({
        username: process.env.NOVADA_PROXY_USER,
        password: process.env.NOVADA_PROXY_PASS
      });
    }

    await page.setExtraHTTPHeaders({
      'Referer': 'https://www.iddaa.com/',
      'Origin': 'https://www.iddaa.com',
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    });

    // Step 1: Fetch events list
    const eventsUrl = 'https://sportsbookv2.iddaa.com/sportsbook/events?st=1&type=0&version=0';
    console.log('Fetching Iddaa events list...');
    
    await page.goto(eventsUrl, { waitUntil: 'networkidle0', timeout: 60000 });
    const content = await page.evaluate(() => document.body.innerText);
    const data = JSON.parse(content);
    
    if (!data.data || !data.data.events) {
      throw new Error('Invalid Iddaa API response structure');
    }

    const matches: IddaaScrapedMatch[] = [];
    
    for (const evt of data.data.events) {
      const startTime = new Date(evt.d * 1000);
      const dateStr = startTime.toLocaleDateString('tr-TR', { day: '2-digit', month: '2-digit', year: 'numeric' });
      const timeStr = startTime.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });
      
      // Step 2: Fetch FULL event details for each match
      const eventDetails = await fetchEventDetails(page, String(evt.i));
      
      let markets: IddaaScrapedMarket[] = [];
      
      if (eventDetails?.data?.m) {
        for (const market of eventDetails.data.m) {
          const mtid = market.st;
          const marketType = IDDAA_MARKET_NAMES[mtid] || `Tip ${mtid}`;
          
          // Include selection value (sov) for Alt/Üst markets like "2.5", "0:1" etc.
          const selectionValue = market.sov;
          const displayName = selectionValue ? `${marketType} ${selectionValue}` : marketType;
          
          const outcomes = (market.o || []).map((o: any) => ({
            name: o.n || '',
            odds: Number(o.odd) || 0
          }));
          
          markets.push({ mtid, marketType: displayName, outcomes });
        }
      } else {
        // Fallback: use basic markets from events list if detail fetch fails
        if (evt.m && Array.isArray(evt.m)) {
          for (const market of evt.m) {
            const mtid = market.st;
            const marketType = IDDAA_MARKET_NAMES[mtid] || `Tip ${mtid}`;
            const selectionValue = market.sov;
            const displayName = selectionValue ? `${marketType} ${selectionValue}` : marketType;
            
            const outcomes = (market.o || []).map((o: any) => ({
              name: o.n || '',
              odds: Number(o.odd) || 0
            }));
            
            markets.push({ mtid, marketType: displayName, outcomes });
          }
        }
      }
      
      // Extract 1X2 odds
      const match1x2 = markets.find(m => m.mtid === 1 && !m.marketType.includes(' '));
      const odds = match1x2 ? {
        home: match1x2.outcomes.find(o => o.name === '1')?.odds || 0,
        draw: match1x2.outcomes.find(o => o.name === '0')?.odds || 0,
        away: match1x2.outcomes.find(o => o.name === '2')?.odds || 0
      } : undefined;
      
      matches.push({
        source: 'Iddaa',
        id: String(evt.i),
        code: String(evt.bri || evt.i),
        homeTeam: evt.hn,
        awayTeam: evt.an,
        date: dateStr,
        time: timeStr,
        timestamp: evt.d * 1000,
        markets,
        odds
      });
      
      console.log(`Fetched ${evt.hn} vs ${evt.an}: ${markets.length} markets`);
    }
    
    const totalMarkets = matches.reduce((a, m) => a + m.markets.length, 0);
    console.log(`Parsed ${matches.length} Iddaa matches with ${totalMarkets} total markets.`);

    return { success: true, count: matches.length, matches };
    
  } catch (error) {
    console.error('Iddaa Scraping Error:', error);
    return { success: false, error: String(error) };
  } finally {
    await browser.close();
  }
}
