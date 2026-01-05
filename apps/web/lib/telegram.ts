/**
 * Telegram Notification Service
 * 
 * Used to send alerts about:
 * - New value bets found
 * - System sync status
 * - Critical errors
 */

const BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN
const CHAT_ID = process.env.TELEGRAM_CHAT_ID

interface ValueBetNotification {
  homeTeam: string
  awayTeam: string
  selection: string
  odds: number
  edge: number
  stake: number
  bookmaker: string
  date: string
}

export async function sendTelegramMessage(message: string): Promise<boolean> {
  if (!BOT_TOKEN || !CHAT_ID) {
    console.warn('Telegram credentials not configured')
    return false
  }

  try {
    const url = `https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id: CHAT_ID,
        text: message,
        parse_mode: 'HTML',
        disable_web_page_preview: true
      })
    })

    const data = await response.json()
    
    if (!data.ok) {
      console.error('Telegram API error:', data.description)
      return false
    }

    return true
  } catch (error) {
    console.error('Failed to send Telegram message:', error)
    return false
  }
}

export async function sendValueBetAlert(bet: ValueBetNotification): Promise<boolean> {
  const emoji = bet.edge > 0.08 ? '💎' : bet.edge > 0.05 ? '🔥' : '💡'
  
  const message = `
${emoji} <b>VALUE BET FOUND</b>

⚽ <b>${bet.homeTeam} vs ${bet.awayTeam}</b>
📅 ${bet.date}

🎯 Selection: <b>${bet.selection}</b>
📊 Odds: <b>${bet.odds.toFixed(2)}</b> (${bet.bookmaker})
📈 Edge: <b>+${(bet.edge * 100).toFixed(1)}%</b>
💰 Kelly Stake: <b>%${(bet.stake * 100).toFixed(1)}</b>

<i>System generated alert</i>
`.trim()

  return sendTelegramMessage(message)
}

export async function sendSyncStatus(
  matches: number, 
  valueBets: number,
  duration: string
): Promise<boolean> {
  const message = `
🔄 <b>Sync Completed</b>

⏱️ Duration: ${duration}
🏟️ Matches: ${matches}
💎 New Value Bets: ${valueBets}

<i>System generated alert</i>
`.trim()

  return sendTelegramMessage(message)
}
