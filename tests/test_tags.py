"""Tests for getTag and getTagNameById (ported from AO3.js tests/tags.test.ts)."""

from __future__ import annotations

import ao3fetch


def test_tags_data_ids_and_dots() -> None:
    """getTag resolves IDs for canonical, synned, non-common, and dotted tags."""
    canonical = ao3fetch.getTag("Ever Given Container Ship (Anthropomorphic)")
    assert canonical.name == "Ever Given Container Ship (Anthropomorphic)"
    assert canonical.id == 56312676

    synned = ao3fetch.getTag("Ever Given Container Ship - Anthropomorphic")
    assert synned.name == "Ever Given Container Ship - Anthropomorphic"
    assert synned.id == 56312676

    nonCommon = ao3fetch.getTag("No Fandom - Freeform")
    assert nonCommon.name == "No Fandom - Freeform"
    assert nonCommon.id is None

    dotted = ao3fetch.getTag("Court Lady Go (Mr. Queen)")
    assert dotted.name == "Court Lady Go (Mr. Queen)"
    assert dotted.id == 55920663

    multiDot = ao3fetch.getTag("A Song of Ice and Fire - George R. R. Martin")
    assert multiDot.name == "A Song of Ice and Fire - George R. R. Martin"


def test_tags_canonical_and_common() -> None:
    """getTag sets canonical, common, and canonicalName accurately."""
    canonical = ao3fetch.getTag("Ever Given Container Ship (Anthropomorphic)")
    assert canonical.canonical is True
    assert canonical.canonicalName == "Ever Given Container Ship (Anthropomorphic)"

    synned = ao3fetch.getTag("Ever Given Container Ship - Anthropomorphic")
    assert synned.canonical is False
    assert synned.common is True
    assert synned.canonicalName == "Ever Given Container Ship (Anthropomorphic)"

    uncommon = ao3fetch.getTag("No Fandom - Freeform")
    assert uncommon.canonical is False
    assert uncommon.common is False
    assert uncommon.canonicalName is None


def test_tags_categories_and_additional_id() -> None:
    """getTag detects all five AO3 tag categories and leaves additional tag IDs null."""
    assert ao3fetch.getTag("The Lorax (2012)").category == "fandom"
    assert ao3fetch.getTag("Ever Given Container Ship (Anthropomorphic)").category == "character"
    assert ao3fetch.getTag("Komaeda Nagito/Sans (Undertale)").category == "relationship"
    assert ao3fetch.getTag("Castiel (Supernatural) & Misha Collins").category == "relationship"
    assert ao3fetch.getTag("Choose Not To Use Archive Warnings").category == "archive warning"

    freeform = ao3fetch.getTag("a shit ton of angst")
    assert freeform.category == "additional tags"
    assert freeform.id is None


def test_tags_parents() -> None:
    """getTag extracts single, No Fandom, and large multi-fandom parent tag lists."""
    ship = ao3fetch.getTag("Ever Given Container Ship - Anthropomorphic")
    assert ship.parentTags == ("Water Vehicles (Anthropomorphic)",)

    noFandom = ao3fetch.getTag("No Fandom - Freeform")
    assert noFandom.parentTags == ("No Fandom",)

    sherlock = ao3fetch.getTag("Sherlock Holmes")
    assert sherlock.name == "Sherlock Holmes"
    assert sherlock.parentTags == (
        "221B Baker Towers",
        "A Sherlock Holmes Adventure Series - Bonnie MacBird",
        "A Study in Emerald - Neil Gaiman",
        "A Study in Terror (1965)",
        "Adventures of Sherlock Holmes and Dr. Watson (TV Russia)",
        "Art in the Blood - Brian Stableford",
        "Baskerville: A Sherlock Holmes Mystery - Ludwig",
        "Crushed In Time (Video Game)",
        "Dr. Jekyll and Mr. Holmes - Loren D. Estleman",
        "Dr. Watson Thrillers - Robert Ryan",
        "Dust and Shadow - Lyndsay Faye",
        "Elementary (TV)",
        "Enola Holmes (Movies)",
        "Enola Holmes Series - Nancy Springer",
        "Exit Sherlock Holmes - Robert Lee Hall",
        "Hands of a Murderer (1990)",
        "Hark! A Vagrant",
        "Holmes & Watson (2018)",
        "Holmes Has Dementia | Series 4 Finale - That Mitchell & Webb Look Sketch",
        "Holmes: Science of Seduction (Visual Novel)",
        "Hound of the Baskervilles - Canny & Nicholson",
        "Inspector Lestrade: Ein Fall f\u00fcr Scotland Yard (Radio)",
        "Irene Adler Series - Carole Nelson Douglas",
        "Mary Russell - Laurie R. King",
        "Miss Holmes - Walsh",
        "Moriarty (Treefort Media Podcast)",
        "Moriarty: Zwischen Genie und Verbrechen (Maritim Audio Drama)",
        "Mr. Holmes (2015)",
        "Ms. Holmes & Ms. Watson \u2013 Apt. 2B - Hamill",
        "Murder by Decree (1979)",
        "Mycroft Holmes Series - Janina Woods",
        "Mycroft Holmes Series - Kareem Abdul-Jabbar & Anna Waterhouse",
        "Mycroft Holmes Series - Quinn Fawcett",
        "O Xang\u00f4 de Baker Street | A Samba for Sherlock - J\u00f4 Soares",
        "Professor Moriarty Series - Michael Kurland",
        "Puppet Holmes (Web Series)",
        "Sherlock & Co. (Podcast)",
        "Sherlock & Daughter (TV)",
        "Sherlock (BBC TV 2010)",
        "Sherlock Holmes & Related Fandoms",
        "Sherlock Holmes & the Servants of Hell - Paul Kane",
        "Sherlock Holmes (Asylum 2010)",
        "Sherlock Holmes (Big Finish Audio)",
        "Sherlock Holmes (Downey Movies)",
        "Sherlock Holmes (Granada TV 1984)",
        "Sherlock Holmes (Radio 1989-2010 Coules)",
        "Sherlock Holmes (Rathbone Movies)",
        "Sherlock Holmes (TV 1964)",
        "Sherlock Holmes (TV 1965)",
        "Sherlock Holmes - Arthur Conan Doyle",
        "Sherlock Holmes - Joel Horwood (Play)",
        "Sherlock Holmes - John Taylor",
        "Sherlock Holmes and Doctor Watson (TV 1980)",
        "Sherlock Holmes and the Adventure of the Furtive Festivity (2018)",
        "Sherlock Holmes and the Case of the Christmas Goose - Menendian/Weagly",
        "Sherlock Holmes and the Case of the Silk Stocking (2004)",
        "Sherlock Holmes and the Hound of the Baskervilles (Short Film 2015)",
        "Sherlock Holmes Chapter One (Video Game)",
        "Sherlock Holmes in the 22nd Century (Cartoon)",
        "Sherlock Holmes Returns (1993)",
        "Sherlock Holmes: A Drama in Four Acts - Conan Doyle & Gillette",
        "Sherlock Holmes: Crimes and Punishments (Video Game)",
        "Sherlock Holmes: Die geheimen F\u00e4lle des Meisterdetektivs (Radio)",
        "Sherlock Holmes: Lost Detective (Video Game)",
        "Sherlock Holmes: The Awakened (Video Game)",
        "Sherlock Holmes: The Devil's Daughter (Video Game)",
        "Sherlock Holmes: The Game is Afoot! - Takarazuka Revue",
        "Sherlock Lupin e io - Alessandro Gatti",
        "Sherlock North (TV)",
        "Sherlock Parody Series - Underholdningsavdelingen Sketches",
        "Sherlock: Case Of Evil (2002)",
        "Sherlock: Find Hidden Objects (Video Game)",
        "The Adventure of Sherlock Holmes' Smarter Brother (1975)",
        "The Adventure of the Peerless Peer - Philip Jose Farmer",
        "The Adventures of Jamie Watson (And Sherlock Holmes) (Web Series)",
        "The Beekeeper's Picnic (Video Game)",
        "The Boy Sherlock Holmes - Shane Peacock",
        "The Case of Death and Honey - Neil Gaiman",
        "The Curious Case of Miss Violet Stone - Poppy Z. Brite & David Ferguson",
        "The Horror of the Many Faces - Tim Lebbon",
        "The Hound of the Baskervilles (1959)",
        "The Hound of the Baskervilles (1983)",
        "The Hound of the Baskervilles (2002)",
        "The Irregulars (TV)",
        "The New Adventures of Sherlock Holmes (Radio)",
        "The Newly Discovered Casebook of Sherlock Holmes (Radio)",
        "The Private Life of Sherlock Holmes (1970)",
        "The Sexual Adventures of Sherlock Holmes - Larry Townsend",
        "The Testament of Sherlock Holmes (Video Game)",
        "The Whole Art of Detection: Lost Mysteries of Sherlock Holmes - Lyndsay Faye",
        "There Is No Game: Wrong Dimension (Video Game)",
        "Victorian Undead: Sherlock Holmes vs Zombies! (Comics)",
        "Watson (TV 2025)",
        "Watson and Holmes (Comics)",
        "Watson's Sketchbook - Molly Knox Ostertag (Webcomic)",
        "Young Sherlock (TV 2026)",
        "Young Sherlock Holmes (1985)",
        "Young Sherlock Holmes Series - Andrew Lane",
        "\u041c\u044b \u0441 \u0428\u0435\u0440\u043b\u043e\u043a\u043e\u043c \u0425\u043e\u043b\u043c\u0441\u043e\u043c | Me and Sherlock Holmes (Short Film)",
        "\u0428\u0435\u0440\u043b\u043e\u043a \u0425\u043e\u043b\u043c\u0441 | Sherlock Holmes (TV 2013)",
        "\u6b4c\u821e\u4f0e\u753a\u30b7\u30e3\u30fc\u30ed\u30c3\u30af | Kabukichou Sherlock (Anime)",
    )


def test_tags_subtags_and_deep_nesting() -> None:
    """getTag preserves AO3.js ordering and parentSubTag links for nested subtags."""
    mindPalace = ao3fetch.getTag("Mind Palace")
    assert mindPalace.name == "Mind Palace"
    assert mindPalace.subTags == (
        ao3fetch.SubTag(tagName="Hannibal Lecter's Mind Palace", parentSubTag=None),
        ao3fetch.SubTag(
            tagName="Will Graham in Hannibal Lecter's Mind Palace",
            parentSubTag="Hannibal Lecter's Mind Palace",
        ),
        ao3fetch.SubTag(tagName="Sherlock Holmes's Mind Palace", parentSubTag=None),
        ao3fetch.SubTag(
            tagName="John Watson in Sherlock Holmes' Mind Palace",
            parentSubTag="Sherlock Holmes's Mind Palace",
        ),
        ao3fetch.SubTag(tagName="Will Graham's Stream Mind Palace", parentSubTag=None),
    )

    wings = ao3fetch.getTag("Wings")
    assert wings.name == "Wings"
    assert ao3fetch.SubTag(parentSubTag=None, tagName="Wing Kink") in wings.subTags
    assert ao3fetch.SubTag(parentSubTag="Wing Kink", tagName="Castiel/Dean Winchester Wing Kink") in wings.subTags
    assert ao3fetch.SubTag(parentSubTag="Wing Kink", tagName="Dean Winchester Has a Wing Kink") in wings.subTags
    assert ao3fetch.SubTag(parentSubTag=None, tagName="Sunday Has Wings (Honkai: Star Rail)") in wings.subTags
    assert (
        ao3fetch.SubTag(
            parentSubTag="Sunday Has Wings (Honkai: Star Rail)",
            tagName="Sunday Has Additional Wings (Honkai: Star Rail)",
        )
        in wings.subTags
    )
    assert (
        ao3fetch.SubTag(
            parentSubTag="Sunday Has Additional Wings (Honkai: Star Rail)",
            tagName="Sunday's Vagina Has Wings (Honkai: Star Rail)",
        )
        in wings.subTags
    )

    worldbuilding = ao3fetch.getTag("Worldbuilding")
    assert worldbuilding.name == "Worldbuilding"
    assert worldbuilding.subTags == (
        ao3fetch.SubTag(parentSubTag=None, tagName="Dixing Worldbuilding (Guardian)"),
        ao3fetch.SubTag(parentSubTag=None, tagName="Earth C Worldbuilding (Homestuck)"),
        ao3fetch.SubTag(parentSubTag=None, tagName="Eridian Lore & Worldbuilding (Project Hail Mary)"),
        ao3fetch.SubTag(
            parentSubTag="Eridian Lore & Worldbuilding (Project Hail Mary)",
            tagName="Eridian Culture & Customs (Project Hail Mary)",
        ),
        ao3fetch.SubTag(
            parentSubTag="Eridian Lore & Worldbuilding (Project Hail Mary)",
            tagName="Eridian Government & Politics (Project Hail Mary)",
        ),
        ao3fetch.SubTag(
            parentSubTag="Eridian Lore & Worldbuilding (Project Hail Mary)",
            tagName="Eridian Language & Grammar (Project Hail Mary)",
        ),
        ao3fetch.SubTag(
            parentSubTag="Eridian Lore & Worldbuilding (Project Hail Mary)",
            tagName="Eridian Science (Project Hail Mary)",
        ),
        ao3fetch.SubTag(
            parentSubTag="Eridian Lore & Worldbuilding (Project Hail Mary)",
            tagName="Eridian Thrums (Project Hail Mary)",
        ),
        ao3fetch.SubTag(
            parentSubTag="Eridian Lore & Worldbuilding (Project Hail Mary)",
            tagName="Eridians are a Hive Mind (Project Hail Mary)",
        ),
        ao3fetch.SubTag(
            parentSubTag="Eridian Culture & Customs (Project Hail Mary)",
            tagName="Eridian Celebration Clothing & Jewelry (Project Hail Mary)",
        ),
        ao3fetch.SubTag(
            parentSubTag="Eridian Culture & Customs (Project Hail Mary)",
            tagName="Eridian Courtship Rituals (Project Hail Mary)",
        ),
        ao3fetch.SubTag(
            parentSubTag="Eridian Culture & Customs (Project Hail Mary)",
            tagName="Eridian Music (Project Hail Mary)",
        ),
        ao3fetch.SubTag(
            parentSubTag="Eridian Culture & Customs (Project Hail Mary)",
            tagName="Eridian Religions (Project Hail Mary)",
        ),
        ao3fetch.SubTag(
            parentSubTag="Eridian Courtship Rituals (Project Hail Mary)",
            tagName="Eridian Mate Marks (Project Hail Mary)",
        ),
        ao3fetch.SubTag(
            parentSubTag="Eridian Language & Grammar (Project Hail Mary)",
            tagName="Ryland Grace Speaks Eridian",
        ),
        ao3fetch.SubTag(
            parentSubTag="Eridian Language & Grammar (Project Hail Mary)",
            tagName="The Convict | Simon (Iron Lung) Speaks Eridian (Project Hail Mary)",
        ),
        ao3fetch.SubTag(
            parentSubTag="Eridian Science (Project Hail Mary)",
            tagName="Eridian Base-6 Math (Project Hail Mary)",
        ),
        ao3fetch.SubTag(
            parentSubTag="Eridian Science (Project Hail Mary)",
            tagName="Eridian Biology (Project Hail Mary)",
        ),
        ao3fetch.SubTag(
            parentSubTag="Eridian Science (Project Hail Mary)",
            tagName="Eridian Technology (Project Hail Mary)",
        ),
        ao3fetch.SubTag(
            parentSubTag="Eridian Biology (Project Hail Mary)",
            tagName="Eridians Can Purr (Project Hail Mary)",
        ),
        ao3fetch.SubTag(
            parentSubTag="Eridian Biology (Project Hail Mary)",
            tagName="Eridians Do Not Have Genders (Project Hail Mary)",
        ),
        ao3fetch.SubTag(
            parentSubTag="Eridian Biology (Project Hail Mary)",
            tagName="Eridians Have Ovipositors (Project Hail Mary)",
        ),
        ao3fetch.SubTag(
            parentSubTag="Eridians Can Purr (Project Hail Mary)",
            tagName="Purring Rocky (Project Hail Mary)",
        ),
        ao3fetch.SubTag(
            parentSubTag="Eridians Have Ovipositors (Project Hail Mary)",
            tagName="Rocky Has an Ovipositor (Project Hail Mary)",
        ),
        ao3fetch.SubTag(
            parentSubTag="Eridian Technology (Project Hail Mary)",
            tagName="Eridian Space Elevator (Project Hail Mary)",
        ),
        ao3fetch.SubTag(parentSubTag=None, tagName="Geofiction"),
        ao3fetch.SubTag(parentSubTag=None, tagName="Halovian Lore and Worldbuilding (Honkai: Star Rail)"),
        ao3fetch.SubTag(
            parentSubTag="Halovian Lore and Worldbuilding (Honkai: Star Rail)",
            tagName="Halovian Biology (Honkai: Star Rail)",
        ),
        ao3fetch.SubTag(parentSubTag=None, tagName="Minecraft Worldbuilding"),
        ao3fetch.SubTag(parentSubTag=None, tagName="Naruto Worldbuilding"),
        ao3fetch.SubTag(parentSubTag="Naruto Worldbuilding", tagName="Anbu Lore (Naruto)"),
        ao3fetch.SubTag(parentSubTag="Naruto Worldbuilding", tagName="Clan Lore (Naruto)"),
        ao3fetch.SubTag(
            parentSubTag="Naruto Worldbuilding",
            tagName="Kirigakure | Hidden Mist Village Worldbuilding",
        ),
        ao3fetch.SubTag(
            parentSubTag="Naruto Worldbuilding",
            tagName="Konohagakure | Hidden Leaf Village Worldbuilding",
        ),
        ao3fetch.SubTag(parentSubTag="Naruto Worldbuilding", tagName="Shinobi Culture (Naruto)"),
        ao3fetch.SubTag(parentSubTag="Naruto Worldbuilding", tagName="Shinobi Politics (Naruto)"),
        ao3fetch.SubTag(
            parentSubTag="Naruto Worldbuilding",
            tagName="Sunagakure | Hidden Sand Village Worldbuilding",
        ),
        ao3fetch.SubTag(
            parentSubTag="Naruto Worldbuilding",
            tagName="Uzushiogakure | Hidden Eddy Village Worldbuilding",
        ),
        ao3fetch.SubTag(parentSubTag="Clan Lore (Naruto)", tagName="Aburame Clan Lore (Naruto)"),
        ao3fetch.SubTag(parentSubTag="Clan Lore (Naruto)", tagName="Hatake Clan Lore (Naruto)"),
        ao3fetch.SubTag(parentSubTag="Clan Lore (Naruto)", tagName="Hyuuga Clan Lore (Naruto)"),
        ao3fetch.SubTag(parentSubTag="Clan Lore (Naruto)", tagName="Nara Clan Lore (Naruto)"),
        ao3fetch.SubTag(parentSubTag="Clan Lore (Naruto)", tagName="Senju Clan Lore (Naruto)"),
        ao3fetch.SubTag(parentSubTag="Clan Lore (Naruto)", tagName="Uchiha Clan Lore (Naruto)"),
        ao3fetch.SubTag(parentSubTag="Clan Lore (Naruto)", tagName="Uzumaki Clan Lore (Naruto)"),
        ao3fetch.SubTag(parentSubTag="Hyuuga Clan Lore (Naruto)", tagName="Hyuuga Clan Politics (Naruto)"),
        ao3fetch.SubTag(
            parentSubTag="Uchiha Clan Lore (Naruto)",
            tagName="Red Eyes are Blessed by Amaterasu (Naruto)",
        ),
        ao3fetch.SubTag(
            parentSubTag="Uchiha Clan Lore (Naruto)",
            tagName="Sharingan Exchange as Marriage (Naruto)",
        ),
        ao3fetch.SubTag(parentSubTag="Uchiha Clan Lore (Naruto)", tagName="Uchiha Clan Politics (Naruto)"),
        ao3fetch.SubTag(parentSubTag="Shinobi Politics (Naruto)", tagName="Clan Politics (Naruto)"),
        ao3fetch.SubTag(
            parentSubTag="Shinobi Politics (Naruto)",
            tagName="Konohagakure | Hidden Leaf Village Politics",
        ),
        ao3fetch.SubTag(
            parentSubTag="Shinobi Politics (Naruto)",
            tagName="Sunagakure | Hidden Sand Village Politics",
        ),
        ao3fetch.SubTag(parentSubTag="Clan Politics (Naruto)", tagName="Clan Restoration Act (Naruto)"),
        ao3fetch.SubTag(parentSubTag="Clan Politics (Naruto)", tagName="Hyuuga Clan Politics (Naruto)"),
        ao3fetch.SubTag(parentSubTag="Clan Politics (Naruto)", tagName="Uchiha Clan Politics (Naruto)"),
        ao3fetch.SubTag(
            parentSubTag="Konohagakure | Hidden Leaf Village Politics",
            tagName="Uchiha Clan Politics (Naruto)",
        ),
        ao3fetch.SubTag(parentSubTag=None, tagName="Pokemon Worldbuilding"),
        ao3fetch.SubTag(parentSubTag=None, tagName="Vidyadhara Lore and Worldbuilding (Honkai: Star Rail)"),
        ao3fetch.SubTag(
            parentSubTag="Vidyadhara Lore and Worldbuilding (Honkai: Star Rail)",
            tagName="Vidyadhara Biology (Honkai: Star Rail)",
        ),
        ao3fetch.SubTag(parentSubTag=None, tagName="Wolfblood Worldbuilding (Wolfblood TV)"),
        ao3fetch.SubTag(parentSubTag=None, tagName="Xiang Fei | Shang Qinghua's Worldbuilding"),
        ao3fetch.SubTag(parentSubTag=None, tagName="Xianzhou Lore and Worldbuilding (Honkai: Star Rail)"),
        ao3fetch.SubTag(
            parentSubTag="Xianzhou Lore and Worldbuilding (Honkai: Star Rail)",
            tagName="Luminary Wardance Ceremony (Honkai: Star Rail)",
        ),
    )

    eventualRomance = ao3fetch.getTag("Eventual Romance")
    assert eventualRomance.name == "Eventual Romance"
    assert not eventualRomance.subTags


def test_tags_synonyms() -> None:
    """getTag extracts tagsWithSameMeaning for canonical tags and empty tuple when none exist."""
    charlie = ao3fetch.getTag("Charlie Magne | Morningstar")
    assert charlie.name == "Charlie Magne | Morningstar"
    assert charlie.canonical is True
    assert charlie.tagsWithSameMeaning == (
        "(Charlie just mentioned)",
        "(mentioned) Charlie Magne | Morningstar",
        "(mentions) Charlie Magne",
        "2p Charlie (Mentioned briefly)",
        "2P Charlie - Character",
        "2P Charlie Magne",
        ": Charlie Morningstar",
        "Anti-Charlie",
        "baby Charlie Magne - Character",
        "Baby Charlie Morningstar - Character",
        "Background Charlie - Character",
        "Background Charlie Magne | Morningstar",
        "Blessed Cat Charlie",
        "Brief Charlie Magne | Morningstar cameo",
        "Brief Charlie Morningstar - Character",
        "cahrlie",
        'Charlemagne "Charlie" Morningstar (Hazbin Hotel)',
        "Charles Morningstar",
        "Charlie (briefly mentioned)",
        "Charlie (Hazbin Hotel)",
        "Charlie (Hazbin Hotel) (mentioned)",
        "Charlie (Hazbin Hotel) | mentioned",
        "Charlie (Hazbin Hotel)(background)",
        "Charlie (Hazbing Hotel)",
        "Charlie (Mentioned small cameo)",
        "Charlie - Mentioned",
        "Charlie Hazbin - Character",
        "Charlie Hazbin hotel",
        "Charlie Hellspawn",
        "charlie is here but not enough to tag really",
        "charlie is the only hazbin character/maybe vaggie but most likey no",
        "Charlie Killjoy",
        "Charlie Magne",
        "Charlie Magne (Deceased)",
        "Charlie Magne (Hazbin Hotel)",
        "Charlie Magne (Mention Only)",
        "Charlie Magne (mentioned)",
        "Charlie Magne (Referenced)",
        "Charlie Magne [mentioned]",
        "Charlie Magne Morningstar",
        "Charlie Magne | Charlie Morningstar",
        "Charlie magne | morningstar ( mentioned )",
        "Charlie Magne | Morningstar (Briefly)",
        "Charlie Magne | Morningstar (Hazbin Hotel) (mentioned)",
        "Charlie Magne | Morningstar (Hazbin Hotel) - Character",
        "Charlie Magne | Morningstar (Mention)",
        "Charlie Magne | Morningstar (mentioned)",
        "Charlie Magne | Morningstar (Minor)",
        "Charlie Magne | Morningstar (referenced)",
        "Charlie Magne | Morningstar - mentioned",
        "Charlie Magne | Morningstar mentioned",
        "Charlie Magne | Morningstar \u00d7",
        "Charlie Magne | Morningstar(but only mentioned)",
        "Charlie Magne | Morningstar(mentioned)",
        "Charlie Magne | Morningstar(Minor)",
        "Charlie Magne-Morningstar",
        "Charlie Magnet",
        "Charlie Magne| Morningstar (Hazbin Hotel)",
        "Charlie Magne|Morningstar",
        "Charlie Magne|Morningstar (Mentioned)",
        "Charlie Mange",
        "Charlie Mange | Morningstar",
        "Charlie Mange | Morningstar (Hazbin Hotel)",
        "Charlie mentioned (Hazbin Hotel)",
        "Charlie Mor",
        "Charlie Moringstar",
        "Charlie Morningstar",
        "Charlie morningstar (hasbin hotel)",
        "Charlie Morningstar (Hazbin Hotel)",
        "Charlie Morningstar (Hazbin Hotel) (mentioned)",
        "Charlie Morningstar (mentioned)",
        "Charlie Morningstar (mentioned).",
        "Charlie Morningstar - Mentioned",
        "Charlie Morningstar implied",
        "Charlie Morningstar | Ghost-Spider",
        "Charlie Morningstar(Hazbin Hotel)",
        "Charlie Morningstar/Magne",
        "charlie's mentioned near the end",
        "Charlie's shadow",
        "charlie( hazbin hotel)",
        "Charlie(Hazbin Hotel)",
        'Charlotte "Charlie" Magne | Morningstar',
        'Charlotte "Charlie" Morningstar',
        "Charlotte Absolute Evil (Hazbin Hotel AU)",
        "Charlotte Absolute Evil (Hazbin Hotel)",
        "Charlotte Absolute Evil(Hazbin Hotel)",
        "Charlotte Magne",
        "Charlotte Magne (Hazbin Hotel)",
        "Charlotte Morningstar",
        "Charlotte Morningstar (Hazbin Hotel)",
        "Charlotte vasiliou magne (hazbin hotel au)",
        "Charolette Magne (Hazbin Hotel)",
        "child Charlie - Character",
        "College Student Charlie - Character",
        "Cursed Cat Charlie",
        "Danny Do-Bad (Hazbin Hotel)",
        "Danny-Do-Bad - Character",
        "Dark Charlie Magne | Morningstar - Character",
        "Dark!Queen Charlie",
        "Demeter Charlie",
        "Demon Charlie - Character",
        "Demon Charlie Magne - Character",
        "Demon Charlie Morningstar",
        "Demon!Charlie - Character",
        "Evil!Charlie - Character",
        "he and charlie text so wanted to tag him",
        "Human Charlie - Character",
        "Human Charlie Magne (Hazbin Hotel)",
        "human Charlie Morningstar",
        "human toddler Charlie",
        "human!Charlie - Character",
        "kid Charlie (Hazbin Hotel)",
        "Male Charlie - Character",
        "Mention of Charlie Morningstar (Hazbin Hotel)",
        "mentioned Charlie",
        "Mentioned Charlie (Hazbin Hotel)",
        "mentioned Charlie Magne - Character",
        "Mentioned Charlie Magne Morningstar",
        "mentioned Charlie Magne | Morningstar - Character",
        "mentioned charlie magne/morningstar",
        "Mentioned Charlie mange",
        "Mentioned Charlie Morningstar",
        "Mentioned Charlie Morningstar (Hazbin hotel) - Character",
        "Mentions Charlie Magne | Morningstar",
        "mentions of Charlie Magne",
        "Mentions of Charlie Magne | Morningstar",
        "Mentions of Charlie Morningstar - Character",
        "Minor Charlie Magne | Morningstar - Character",
        "Minor Charlie Morningstar",
        "Princess Charlie (Hazbin Hotel)",
        "Princess Charlotte Morningstar - Character",
        "Referenced Charlie",
        "Single Mom Charlie Morningstar - Character",
        "Sugar Mommy!Charlie",
        "swap charlie",
        "Swapped Charlie Morningstar",
        "The Diabolical Danny-Do-Bad",
        "The Savant | Charlie Morningstar",
    )

    noSynonyms = ao3fetch.getTag("Original Senator Characters")
    assert noSynonyms.name == "Original Senator Characters"
    assert not noSynonyms.tagsWithSameMeaning


def test_get_tag_name_by_id_from_atom_feed() -> None:
    """getTagNameById resolves canonical tag names from real AO3 Atom feeds and returns None on non-Atom responses."""
    assert ao3fetch.getTagNameById(56312676) == "Ever Given Container Ship (Anthropomorphic)"
    assert ao3fetch.getTagNameById("56312666") is None
