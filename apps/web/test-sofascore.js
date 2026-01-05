
const puppeteer = require('puppeteer');

async function test() {
  console.log('Launching browser...');
  const browser = await puppeteer.launch({
    headless: "new", 
    args: ['--no-sandbox', '--disable-setuid-sandbox'] 
  });
  const page = await browser.newPage();
  
  // Set accurate User Agent
  await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
  
  try {
    // 1. Test Search
    const searchUrl = `https://www.sofascore.com/search?q=Manchester City`;
    console.log(`Searching: ${searchUrl}`);
    await page.goto(searchUrl, { waitUntil: 'networkidle2' });
    
    // Dump search results structure
    const searchResults = await page.$$eval('a[href*="/team/"]', els => els.map(el => ({ href: el.getAttribute('href'), text: el.textContent })));
    console.log('Search Results:', searchResults.slice(0, 3));

    // 2. Test Team Page
    const teamUrl = 'https://www.sofascore.com/tr/football/team/manchester-city/17';
    console.log(`Navigating to Team: ${teamUrl}`);
    await page.goto(teamUrl, { waitUntil: 'networkidle2' });
    
    // Setup API Interception
    const apiResponses = {};
    page.on('response', async (response) => {
        const url = response.url();
        if (url.includes('/api/v1/') && response.request().resourceType() === 'xhr') {
            try {
                // Determine category based on URL
                let category = 'unknown';
                if (url.includes('/statistics')) category = 'stats';
                if (url.includes('/events')) category = 'matches';
                
                apiResponses[category] = await response.json();
                console.log(`Captured API response: ${url} (${category})`);
            } catch(e) {}
        }
    });

    // Dump __NEXT_DATA__ structure (without full content to save log space)
    const nextData = await page.evaluate(() => {
        try {
            // @ts-ignore
            const data = window.__NEXT_DATA__;
            return {
                props: Object.keys(data?.props || {}),
                pageProps: Object.keys(data?.props?.pageProps || {}),
                initialState: data?.props?.pageProps?.initialState ? Object.keys(data.props.pageProps.initialState) : 'missing'
            };
        } catch (e) { return 'Error reading NEXT_DATA'; }
    });
    console.log('__NEXT_DATA__ Structure:', JSON.stringify(nextData, null, 2));

    // Nav to Stats Tab to trigger API call
    console.log('Clicking Statistics tab...');
    // Finding tab by href or text
    const clicked = await page.evaluate(() => {
        const links = Array.from(document.querySelectorAll('a'));
        const statsLink = links.find(a => a.href.includes('tab:statistics') || a.textContent.includes('İstatistikler') || a.textContent.includes('Statistics'));
        if (statsLink) {
            statsLink.click();
            return true;
        }
        return false;
    });
    
    if (clicked) {
        console.log('Tab clicked, waiting for network...');
        await new Promise(r => setTimeout(r, 5000));
        console.log('Captured Stats:', Object.keys(apiResponses.stats || {}));
    } else {
        console.log('Statistics tab not found');
    }


  } catch (e) {
    console.error('Error during navigation:', e.message);
  } finally {
    await browser.close();
  }
}

test();
