RARITY_STYLE = {
    "Common": "⚪ Common",
    "Rare": "🟢 Rare",
    "Epic": "🔵 Epic",
    "Legendary": "🟣 Legendary",
    "Mythic": "🟡 Mythic"
}


def rarity_text(rarity: str) -> str:
    return RARITY_STYLE.get(rarity, rarity)


WEAPONS = {
    "dagger": {
        "name": "🗡 Кинджал",
        "rarity": "Common",
        "win_bonus": 5,
        "crit_chance": 5,
        "effect": "crit",
        "effect_chance": 10,
        "effect_bonus": 10,
        "price": 5000,
        "drop_chance": 45
    },

    "axe": {
        "name": "🪓 Сокира",
        "rarity": "Rare",
        "win_bonus": 8,
        "crit_chance": 3,
        "effect": "heavy_hit",
        "effect_chance": 12,
        "effect_bonus": 12,
        "price": 12000,
        "drop_chance": 30
    },

    "shield": {
        "name": "🛡 Щит",
        "rarity": "Rare",
        "win_bonus": 6,
        "crit_chance": 0,
        "effect": "block",
        "effect_chance": 15,
        "effect_bonus": 10,
        "price": 15000,
        "drop_chance": 20
    },

    "dark_sword": {
        "name": "⚔️ Темний меч",
        "rarity": "Epic",
        "win_bonus": 12,
        "crit_chance": 8,
        "effect": "dark_strike",
        "effect_chance": 10,
        "effect_bonus": 18,
        "price": 50000,
        "drop_chance": 5
    }
}