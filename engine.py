"""
Strip or Bluff - Game Engine v3.2
Modes: Joker's Draw (old_maid) / Blackjack (21)
Intensity: soft / normal / extreme
Features: auto-scoreboard, blind blackjack, name support, upgraded peek system
"""

import random
import json

# --- Constants ---
RANKS = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"]
SUITS = ["S","H","D","C"]
SUIT_SYMBOLS = {"S": "\u2660", "H": "\u2665", "D": "\u2666", "C": "\u2663"}
JOKER = "JOKER"

DEFAULT_PLAYER_CLOTHES = ["top", "bottom", "underwear", "panties"]
DEFAULT_AI_CLOTHES = ["jacket", "shirt", "pants", "underwear"]

# Peek catch rates by number of cards peeked
CATCH_RATES = {1: 0.4, 2: 0.6, 3: 0.8}
BJ_CATCH_RATE = 0.4

# --- Helpers ---
def card_display(card):
    if card == JOKER:
        return "JOKER"
    rank = card[:-1]
    suit = card[-1]
    return f"{rank}{SUIT_SYMBOLS.get(suit, suit)}"

def hand_value_bj(hand):
    total = 0
    aces = 0
    for card in hand:
        if card == JOKER:
            continue
        rank = card[:-1]
        if rank in ["J", "Q", "K"]:
            total += 10
        elif rank == "A":
            total += 11
            aces += 1
        else:
            total += int(rank)
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    return total

def build_full_deck():
    return [f"{r}{s}" for r in RANKS for s in SUITS]

# --- Scoreboard ---
def _scoreboard():
    p_name = state.player_name
    a_name = state.ai_name
    p_removed = state.player_items_removed
    a_removed = state.ai_items_removed
    sb = {
        "scoreboard": {
            p_name: {
                "clothes_count": len(state.player_clothes),
                "items_removed": p_removed,
                "hand_count": len(state.player_hand),
                "pairs_matched": len(state.player_pairs),
            },
            a_name: {
                "clothes_count": len(state.ai_clothes),
                "items_removed": a_removed,
                "hand_count": len(state.ai_hand),
                "pairs_matched": len(state.ai_pairs),
            },
            "round": state.round,
            "mode": state.mode,
            "intensity": state.intensity,
            "turn": state.player_name if state.turn == "player" else state.ai_name,
        }
    }
    return sb

# --- Game State ---
class GameState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.mode = None
        self.intensity = "normal"
        self.round = 0
        self.player_hand = []
        self.ai_hand = []
        self.player_clothes = list(DEFAULT_PLAYER_CLOTHES)
        self.ai_clothes = list(DEFAULT_AI_CLOTHES)
        self.player_pairs = []
        self.ai_pairs = []
        self.player_items_removed = []
        self.ai_items_removed = []
        self.turn = None
        self.phase = "idle"
        self.cheat_enabled = True
        self.player_stood = False
        self.ai_stood = False
        self.player_visible = []
        self.ai_visible = []
        self.player_name = "player"
        self.ai_name = "ai"
        self._bj_deck = []

    def status_dict(self):
        return {
            "mode": self.mode,
            "intensity": self.intensity,
            "round": self.round,
            "phase": self.phase,
            "turn": self.player_name if self.turn == "player" else self.ai_name,
            "cheat_enabled": self.cheat_enabled,
            self.player_name: {
                "clothes_count": len(self.player_clothes),
                "items_removed": self.player_items_removed,
                "hand_count": len(self.player_hand),
                "pairs": self.player_pairs,
            },
            self.ai_name: {
                "clothes_count": len(self.ai_clothes),
                "items_removed": self.ai_items_removed,
                "hand_count": len(self.ai_hand),
                "pairs": self.ai_pairs,
            },
        }

state = GameState()

# --- Old Maid Setup ---
def _setup_old_maid():
    ranks_chosen = random.sample(RANKS, 5)
    full_deck = build_full_deck()
    cards = []
    for rank in ranks_chosen:
        rank_cards = [c for c in full_deck if c[:-1] == rank]
        pair = random.sample(rank_cards, 2)
        cards.extend(pair)
    cards.append(JOKER)
    random.shuffle(cards)
    split = random.choice([5, 6])
    state.player_hand = cards[:split]
    state.ai_hand = cards[split:]
    _remove_pairs("player")
    _remove_pairs("ai")

def _remove_pairs(who):
    hand = state.player_hand if who == "player" else state.ai_hand
    pairs_list = state.player_pairs if who == "player" else state.ai_pairs
    found = True
    while found:
        found = False
        ranks_in_hand = {}
        for i, card in enumerate(hand):
            if card == JOKER:
                continue
            rank = card[:-1]
            if rank in ranks_in_hand:
                pair = (card_display(ranks_in_hand[rank]), card_display(card))
                pairs_list.append(pair)
                hand.remove(ranks_in_hand[rank])
                hand.remove(card)
                found = True
                break
            else:
                ranks_in_hand[rank] = card

# --- Blackjack Setup ---
def _setup_blackjack():
    deck = build_full_deck()
    random.shuffle(deck)
    state.player_hand = [deck.pop()]
    state.ai_hand = [deck.pop()]
    state.player_visible = [card_display(state.player_hand[0])]
    state.ai_visible = [card_display(state.ai_hand[0])]
    state._bj_deck = deck
    state.player_stood = False
    state.ai_stood = False

# --- Actions ---
def do_start(args_str):
    parts = args_str.strip().split()
    mode = parts[0] if parts else "old_maid"
    if mode not in ("old_maid", "blackjack"):
        return {"error": "mode must be old_maid or blackjack"}

    cheat = True
    intensity = "normal"
    for p in parts[1:]:
        if p == "nocheat":
            cheat = False
        elif p in ("soft", "normal", "extreme"):
            intensity = p

    state.mode = mode
    state.round += 1
    state.phase = "playing"
    state.cheat_enabled = cheat
    state.intensity = intensity
    state.player_pairs = []
    state.ai_pairs = []
    state.turn = random.choice(["player", "ai"])

    if mode == "old_maid":
        _setup_old_maid()
    else:
        _setup_blackjack()

    result = {
        "event": "game_start",
        "mode": mode,
        "intensity": intensity,
        "round": state.round,
        "cheat_enabled": cheat,
        "first_turn": state.player_name if state.turn == "player" else state.ai_name,
        "player_hand_count": len(state.player_hand),
        "ai_hand_count": len(state.ai_hand),
    }
    if mode == "old_maid":
        result["player_pairs_removed"] = len(state.player_pairs)
        result["ai_pairs_removed"] = len(state.ai_pairs)
    else:
        result["player_visible_card"] = state.player_visible[0]
        result["ai_visible_card"] = state.ai_visible[0]
        result["note"] = "Only the first card is face-up. All subsequent hits are blind (face-down). Neither side knows their total or whether they have busted until BOTH stand and cards are revealed. Use peek (cheat) to secretly check your own hand value before deciding to hit or stand."
    result.update(_scoreboard())
    return result

def do_draw(args_str):
    if state.mode != "old_maid":
        return {"error": "draw is only for old_maid mode"}
    if state.phase != "playing":
        return {"error": "game not in progress"}

    pos = int(args_str.strip()) if args_str.strip() else 1
    who = state.turn
    who_name = state.player_name if who == "player" else state.ai_name
    opponent = "ai" if who == "player" else "player"
    opp_hand = state.ai_hand if who == "player" else state.player_hand
    my_hand = state.player_hand if who == "player" else state.ai_hand
    my_pairs = state.player_pairs if who == "player" else state.ai_pairs

    if not opp_hand:
        return _check_old_maid_end()

    idx = max(0, min(pos - 1, len(opp_hand) - 1))
    drawn_card = opp_hand.pop(idx)

    matched = False
    matched_with = None
    if drawn_card != JOKER:
        drawn_rank = drawn_card[:-1]
        for c in my_hand:
            if c != JOKER and c[:-1] == drawn_rank:
                matched = True
                matched_with = c
                break

    if matched:
        my_hand.remove(matched_with)
        my_pairs.append((card_display(matched_with), card_display(drawn_card)))
        event = "draw_match"
    else:
        my_hand.append(drawn_card)
        random.shuffle(my_hand)
        event = "draw_keep"

    win_check = _check_old_maid_end()
    if win_check:
        win_check.update(_scoreboard())
        return win_check

    state.turn = opponent
    next_name = state.player_name if opponent == "player" else state.ai_name
    result = {
        "event": event,
        "who_drew": who_name,
        "position_chosen": pos,
        "card_drawn": card_display(drawn_card),
        "matched": matched,
        "matched_pair": (card_display(matched_with), card_display(drawn_card)) if matched else None,
        "player_hand_count": len(state.player_hand),
        "ai_hand_count": len(state.ai_hand),
        "next_turn": next_name,
    }
    result.update(_scoreboard())
    return result

def _check_old_maid_end():
    if len(state.player_hand) == 0:
        return _round_end("ai")
    if len(state.ai_hand) == 0:
        return _round_end("player")
    if len(state.player_hand) == 1 and state.player_hand[0] == JOKER and len(state.ai_hand) == 0:
        return _round_end("player")
    if len(state.ai_hand) == 1 and state.ai_hand[0] == JOKER and len(state.player_hand) == 0:
        return _round_end("ai")
    return None

def do_hit(args_str):
    if state.mode != "blackjack":
        return {"error": "hit is only for blackjack mode"}
    if state.phase != "playing":
        return {"error": "game not in progress"}

    who = state.turn
    who_name = state.player_name if who == "player" else state.ai_name
    if who == "player" and state.player_stood:
        return {"error": "player already stood"}
    if who == "ai" and state.ai_stood:
        return {"error": "ai already stood"}

    hand = state.player_hand if who == "player" else state.ai_hand
    card = state._bj_deck.pop()
    hand.append(card)

    # Blind mode: do NOT reveal value or bust status.
    # Player must use peek (cheat) to know their own total.
    # Resolution happens only when both sides stand.

    opponent = "ai" if who == "player" else "player"
    opp_stood = state.ai_stood if who == "player" else state.player_stood
    if not opp_stood:
        state.turn = opponent
        next_name = state.player_name if opponent == "player" else state.ai_name
    else:
        next_name = who_name

    result = {
        "event": "hit",
        "who": who_name,
        "card_count": len(hand),
        "message": f"{who_name} draws another card face-down. Total cards in hand: {len(hand)}. No one knows the value yet.",
        "next_turn": next_name,
    }
    result.update(_scoreboard())
    return result

def do_stand(args_str):
    if state.mode != "blackjack":
        return {"error": "stand is only for blackjack mode"}
    if state.phase != "playing":
        return {"error": "game not in progress"}

    who = state.turn
    who_name = state.player_name if who == "player" else state.ai_name
    if who == "player":
        state.player_stood = True
    else:
        state.ai_stood = True

    if state.player_stood and state.ai_stood:
        return _resolve_blackjack()

    opponent = "ai" if who == "player" else "player"
    opp_name = state.player_name if opponent == "player" else state.ai_name
    state.turn = opponent
    result = {
        "event": "stand",
        "who": who_name,
        "next_turn": opp_name,
        "message": f"{who_name} stands. Waiting for {opp_name}.",
    }
    result.update(_scoreboard())
    return result

def _resolve_blackjack():
    p_val = hand_value_bj(state.player_hand)
    a_val = hand_value_bj(state.ai_hand)
    p_cards = [card_display(c) for c in state.player_hand]
    a_cards = [card_display(c) for c in state.ai_hand]

    p_bust = p_val > 21
    a_bust = a_val > 21
    p_bj = p_val == 21
    a_bj = a_val == 21

    result = {
        "event": "blackjack_reveal",
        f"{state.player_name}_cards": p_cards,
        f"{state.player_name}_value": p_val,
        f"{state.player_name}_busted": p_bust,
        f"{state.ai_name}_cards": a_cards,
        f"{state.ai_name}_value": a_val,
        f"{state.ai_name}_busted": a_bust,
    }

    # Determine outcome
    if p_bust and a_bust:
        # Both busted: whoever is further from 21 loses
        if p_val > a_val:
            end = _round_end("player", reason="double_bust")
        elif a_val > p_val:
            end = _round_end("ai", reason="double_bust")
        else:
            end = {"event": "draw_tie", "message": "Both busted equally! Tie, no one strips."}
            state.phase = "idle"
    elif p_bust:
        end = _round_end("player", reason="bust")
    elif a_bust:
        end = _round_end("ai", reason="bust")
    elif p_val > a_val:
        end = _round_end("ai", reason="higher")
    elif a_val > p_val:
        end = _round_end("player", reason="higher")
    else:
        end = {"event": "draw_tie", "message": "Tie! No one strips this round."}
        state.phase = "idle"

    # Bonus for hitting exactly 21
    if p_bj and not a_bj:
        result["bonus_21"] = state.player_name
        result["bonus_message"] = f"{state.player_name} hit exactly 21! Lucky bonus: winner gets a special request!"
    elif a_bj and not p_bj:
        result["bonus_21"] = state.ai_name
        result["bonus_message"] = f"{state.ai_name} hit exactly 21! Lucky bonus: winner gets a special request!"

    result.update(end)
    result.update(_scoreboard())
    return result

def _round_end(loser, reason=None):
    state.phase = "stripping"
    loser_name = state.player_name if loser == "player" else state.ai_name
    winner_name = state.ai_name if loser == "player" else state.player_name
    clothes = state.player_clothes if loser == "player" else state.ai_clothes
    items_removed = state.player_items_removed if loser == "player" else state.ai_items_removed

    if not clothes:
        state.phase = "game_over"
        return {
            "event": "game_over",
            "loser": loser_name,
            "winner": winner_name,
            "message": f"{loser_name} has no clothes left! Game over!",
            "intensity": state.intensity,
        }

    stripped_item = clothes.pop()
    items_removed.append(stripped_item)
    state.phase = "idle"

    result = {
        "event": "strip",
        "loser": loser_name,
        "winner": winner_name,
        "item_removed": stripped_item,
        "items_removed_so_far": list(items_removed),
        "remaining_count": len(clothes),
        "intensity": state.intensity,
        "message": f"{loser_name} loses! Must remove: {stripped_item}",
    }

    if not clothes:
        state.phase = "game_over"
        result["game_over"] = True
        result["final_message"] = f"{loser_name} is fully stripped! {winner_name} gets a final request!"

    return result

def do_peek(args_str):
    if not state.cheat_enabled:
        return {"error": "cheating is disabled this game"}
    if state.phase != "playing":
        return {"error": "can only peek during active game"}

    who = state.turn
    who_name = state.player_name if who == "player" else state.ai_name

    # Blackjack mode: peek at your OWN hand value
    if state.mode == "blackjack":
        caught = random.random() < BJ_CATCH_RATE
        if caught:
            result = {
                "event": "cheat_caught",
                "cheater": who_name,
                "target": "self",
                "message": f"{who_name} was caught peeking at their own cards! Opponent decides: forgive or punish",
                "intensity": state.intensity,
            }
            result.update(_scoreboard())
            return result

        hand = state.player_hand if who == "player" else state.ai_hand
        val = hand_value_bj(hand)
        result = {
            "event": "cheat_success",
            "cheater": who_name,
            "target": "self",
            "cards_seen": [card_display(c) for c in hand],
            "hand_value": val,
            "message": f"{who_name} secretly peeked at their own hand: total = {val}",
        }
        result.update(_scoreboard())
        return result

    # Old Maid mode: peek at opponent's cards (1-3 cards)
    parts = args_str.strip().split()
    num_cards = 1
    if parts:
        try:
            num_cards = int(parts[0])
            num_cards = max(1, min(3, num_cards))
        except ValueError:
            num_cards = 1

    catch_rate = CATCH_RATES.get(num_cards, 0.4)
    caught = random.random() < catch_rate

    if caught:
        result = {
            "event": "cheat_caught",
            "cheater": who_name,
            "target": "opponent",
            "cards_attempted": num_cards,
            "catch_rate": f"{int(catch_rate*100)}%",
            "message": f"{who_name} tried to peek at {num_cards} card(s) but got caught! Opponent decides: forgive or punish",
            "intensity": state.intensity,
        }
        result.update(_scoreboard())
        return result

    opp_hand = state.ai_hand if who == "player" else state.player_hand
    peek_count = min(num_cards, len(opp_hand))
    peek_indices = random.sample(range(len(opp_hand)), peek_count)
    cards_seen = [(i+1, card_display(opp_hand[i])) for i in sorted(peek_indices)]

    result = {
        "event": "cheat_success",
        "cheater": who_name,
        "target": "opponent",
        "cards_peeked": num_cards,
        "cards_seen": cards_seen,
        "message": f"{who_name} secretly peeked at {peek_count} of opponent's cards!",
    }
    result.update(_scoreboard())
    return result

def do_caught(args_str):
    choice = args_str.strip().lower() if args_str.strip() else "forgive"
    if choice == "forgive":
        result = {
            "event": "cheat_forgiven",
            "message": "Cheater was forgiven. No penalty.",
            "intensity": state.intensity,
        }
        result.update(_scoreboard())
        return result
    elif choice == "punish":
        cheater = "ai" if state.turn == "player" else "player"
        cheater_name = state.player_name if cheater == "player" else state.ai_name
        clothes = state.player_clothes if cheater == "player" else state.ai_clothes
        items_removed = state.player_items_removed if cheater == "player" else state.ai_items_removed
        if not clothes:
            state.phase = "game_over"
            result = {
                "event": "game_over",
                "loser": cheater_name,
                "message": f"{cheater_name} was punished but has no clothes left! Game over!",
                "intensity": state.intensity,
            }
            result.update(_scoreboard())
            return result
        stripped = clothes.pop()
        items_removed.append(stripped)
        result = {
            "event": "cheat_punished",
            "cheater": cheater_name,
            "item_removed": stripped,
            "items_removed_so_far": list(items_removed),
            "remaining_count": len(clothes),
            "intensity": state.intensity,
            "message": f"{cheater_name} must remove {stripped} as punishment!",
        }
        if not clothes:
            state.phase = "game_over"
            result["game_over"] = True
        result.update(_scoreboard())
        return result
    else:
        return {"error": "choice must be forgive or punish"}

def do_clothes(args_str):
    parts = args_str.strip().split(None, 1)
    if len(parts) < 2:
        return {"error": "usage: clothes <player|ai> <item1,item2,...>"}
    who = parts[0].lower()
    items = [x.strip() for x in parts[1].split(",")]
    if who in ("player", state.player_name.lower()):
        state.player_clothes = items
        who = state.player_name
    elif who in ("ai", state.ai_name.lower()):
        state.ai_clothes = items
        who = state.ai_name
    else:
        return {"error": "who must be player or ai (or their names)"}
    return {
        "event": "clothes_set",
        "who": who,
        "clothes": items,
        "count": len(items),
    }

def do_name(args_str):
    parts = args_str.strip().split(None, 1)
    if len(parts) < 2:
        return {"error": "usage: name <player|ai> <name>"}
    who = parts[0].lower()
    new_name = parts[1].strip()
    if who == "player":
        state.player_name = new_name
    elif who == "ai":
        state.ai_name = new_name
    else:
        return {"error": "who must be player or ai"}
    return {
        "event": "name_set",
        "who": who,
        "name": new_name,
        "player_name": state.player_name,
        "ai_name": state.ai_name,
    }

def do_status(args_str):
    s = state.status_dict()
    if state.mode == "old_maid":
        s["your_hand"] = [card_display(c) for c in state.player_hand]
    elif state.mode == "blackjack":
        s[f"{state.player_name}_visible"] = state.player_visible
        s[f"{state.ai_name}_visible"] = state.ai_visible
        s[f"{state.player_name}_card_count"] = len(state.player_hand)
        s[f"{state.ai_name}_card_count"] = len(state.ai_hand)
    return s

def do_reset(args_str):
    state.reset()
    return {"event": "reset", "message": "Game fully reset. Ready to start a new game."}

# --- Main Handler ---
ACTIONS = {
    "start": do_start,
    "draw": do_draw,
    "hit": do_hit,
    "stand": do_stand,
    "peek": do_peek,
    "caught": do_caught,
    "clothes": do_clothes,
    "name": do_name,
    "status": do_status,
    "reset": do_reset,
}

def handle(input_str):
    input_str = str(input_str).strip()
    parts = input_str.split(None, 1)
    action = parts[0].lower() if parts else ""
    args = parts[1] if len(parts) > 1 else ""
    fn = ACTIONS.get(action)
    if not fn:
        return json.dumps({"error": f"unknown action: {action}", "available": list(ACTIONS.keys())}, ensure_ascii=False)
    result = fn(args)
    return json.dumps(result, ensure_ascii=False, indent=2)

def format_result(result_str):
    return result_str