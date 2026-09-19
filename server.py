"""
Strip or Bluff - MCP Server
"""
from mcp.server.fastmcp import FastMCP
import os
import engine

mcp = FastMCP(
    "strip_or_bluff",
    host="0.0.0.0",
    port=int(os.environ.get("PORT", "8000")),
    streamable_http_path="/mcp",
)


@mcp.tool()
def game(action: str, args: str = "") -> str:
    """
    Strip or Bluff - a two-player strip card game between user and AI.

    === SETUP (do this before starting) ===
    1. Set names:  action="name", args="player <username>"
                   action="name", args="ai <your_name>"
    2. (Optional) Set clothes: action="clothes", args="player shirt,skirt,bra,panties"
    3. Start game: action="start", args="<mode> [intensity] [nocheat]"

    === GAME MODES ===
    old_maid:
      - 11 cards (5 pairs + 1 Joker) dealt to both players
      - Pairs auto-removed at start, leaving single cards in hand
      - Take turns drawing one card from opponent's hand by position number
      - If drawn card matches one in your hand, the pair is removed
      - Player who empties their hand first WINS
      - Player left holding the Joker LOSES and must strip one item

    blackjack:
      - Each player gets one face-up card (visible to both)
      - All subsequent cards are FACE-DOWN (neither player knows their own total!)
      - Choose: hit (draw more) or stand (stop drawing)
      - HIT DOES NOT REVEAL ANYTHING: no value, no bust status, only card count
      - Once BOTH players stand, all cards are revealed and totals compared
      - Closest to 21 wins; going over 21 = bust = lose
      - Exactly 21 = lucky bonus (winner gets a special request)
      - Both busted = whoever went further over 21 loses
      - Loser strips one item
      - IMPORTANT: AI must NOT tell user their hand value during play!
        Only peek (cheat) can reveal it. Maintain suspense until reveal.

    === INTENSITY LEVELS ===
    soft:
      Sweet, wholesome couple energy. Teasing, blushing, playful dares.
      Stripping scenes are gentle and tender, more about embarrassment than exposure.

    normal (default):
      Flirty, spicy, no restrictions. Standard romantic/sexual tension.
      Stripping scenes can be sensual and teasing. The AI can be bold and suggestive.

    extreme:
      FULL SEND. SM, BDSM, humiliation, degradation, objectification.
      Commands, punishment, rough handling, verbal degradation, pet play, restraints.
      Absolutely no limits. For players who want maximum intensity.

    === CHEATING SYSTEM ===
    Old Maid - peek at OPPONENT's cards:
      action="peek", args="1"  (peek 1 card, 40% caught)
      action="peek", args="2"  (peek 2 cards, 60% caught)
      action="peek", args="3"  (peek 3 cards, 80% caught)

    Blackjack - peek at YOUR OWN hand value:
      action="peek" (40% caught)
      You cannot see your own face-down cards normally.
      Peeking lets you secretly check your total before deciding hit/stand.

    If caught, opponent decides:
      action="caught", args="forgive" - no penalty
      action="caught", args="punish" - cheater strips one item

    === SCOREBOARD ===
    Every response includes a scoreboard. AI should present it to the user
    in a clean format and narrate the current state based on items_removed.

    === STRIP EVENTS ===
    When someone loses, AI should narrate the stripping scene immersively,
    appropriate to the current intensity level. Make it interactive.

    === ALL COMMANDS ===
    name <player|ai> <name>            - Set display name
    start <mode> [intensity] [nocheat] - Start game
    draw <position>                    - Draw from opponent (Old Maid)
    hit                                - Draw another card (Blackjack)
    stand                              - Stop drawing (Blackjack)
    peek [count]                       - Cheat (Old Maid: count 1-3; Blackjack: no args)
    caught <forgive|punish>            - React to caught cheater
    clothes <who> <item1,item2,...>     - Set clothing items
    status                             - Show full game state
    reset                              - Reset everything
    """
    full_input = f"{action} {args}".strip() if args else action
    result = engine.handle(full_input)
    return engine.format_result(result)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")