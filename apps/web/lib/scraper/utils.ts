
import { distance } from 'fastest-levenshtein';

export function normalizeName(name: string): string {
  if (!name) return '';
  return name.toLowerCase()
    .replace(/ü/g, 'u')
    .replace(/ğ/g, 'g')
    .replace(/ı/g, 'i')
    .replace(/ş/g, 's')
    .replace(/ç/g, 'c')
    .replace(/ö/g, 'o')
    .replace(/[^a-z0-9 ]/g, '')
    .trim();
}

// Alias map: { "man. city" => team_id, "manchester city" => team_id, ... }
export type AliasMap = Map<string, number>;

export function buildAliasMap(aliases: { team_id: number; alias: string }[]): AliasMap {
  const map = new Map<string, number>();
  for (const a of aliases) {
    map.set(normalizeName(a.alias), a.team_id);
  }
  return map;
}

export function findMatchingMatch(
  scrapedMatch: any, 
  dbMatches: any[], 
  aliasMap?: AliasMap
) {
  const scrapedHome = scrapedMatch.homeTeam;
  const scrapedAway = scrapedMatch.awayTeam;
  const scrapedDate = scrapedMatch.date; // "DD.MM.YYYY"
  
  // 1. Filter by date first
  const sameDateMatches = dbMatches.filter(m => {
      const dbDate = new Date(m.match_date);
      const day = String(dbDate.getDate()).padStart(2, '0');
      const month = String(dbDate.getMonth() + 1).padStart(2, '0');
      const year = dbDate.getFullYear();
      const formattedDbDate = `${day}.${month}.${year}`;
      return formattedDbDate === scrapedDate;
  });

  if (sameDateMatches.length === 0) return null;

  // 2. Try EXACT ALIAS MATCH first (if aliasMap provided)
  if (aliasMap) {
    const homeTeamId = aliasMap.get(normalizeName(scrapedHome));
    const awayTeamId = aliasMap.get(normalizeName(scrapedAway));
    
    if (homeTeamId && awayTeamId) {
      // Find match where home_team.id === homeTeamId AND away_team.id === awayTeamId
      const exactMatch = sameDateMatches.find(m => 
        m.home_team?.id === homeTeamId && m.away_team?.id === awayTeamId
      );
      if (exactMatch) return exactMatch;
    }
  }

  // 3. Fallback to fuzzy matching
  let bestMatch = null;
  let minDistance = Infinity;
  
  const normalizedHome = normalizeName(scrapedHome);
  const normalizedAway = normalizeName(scrapedAway);

  for (const dbMatch of sameDateMatches) {
      if (!dbMatch.home_team || !dbMatch.away_team) continue;
      
      const dbHome = normalizeName(dbMatch.home_team.name);
      const dbAway = normalizeName(dbMatch.away_team.name);
      
      const distHome = distance(normalizedHome, dbHome);
      const distAway = distance(normalizedAway, dbAway);
      const totalDist = distHome + distAway;
      
      if (totalDist < 12 && totalDist < minDistance) {
          minDistance = totalDist;
          bestMatch = dbMatch;
      }
  }

  return bestMatch;
}
