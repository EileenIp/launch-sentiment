"""Tests for theme matching. No corpus required."""
from src import classify_themes, taxonomy


def test_a_crash_complaint_lands_in_bugs():
    assert "bugs_stability" in classify_themes.themes_for("game crashes every five minutes")


def test_a_nerf_complaint_lands_in_balance():
    assert "balance" in classify_themes.themes_for("they nerfed every decent weapon again")


def test_a_doxxing_complaint_lands_in_dev_conduct():
    found = classify_themes.themes_for("engage with the devs and you get doxxed")

    assert "dev_conduct" in found


def test_a_review_can_carry_several_themes():
    """"Nerfed into the ground and it crashes" is genuinely two complaints."""
    found = classify_themes.themes_for("nerfed into the ground and it crashes constantly")

    assert {"balance", "bugs_stability"} <= found


def test_matching_respects_word_boundaries():
    """'ama' must not fire on 'amazing', which would put praise in dev_conduct."""
    assert "dev_conduct" not in classify_themes.themes_for("this game is amazing")


def test_penetration_does_not_fire_on_unrelated_words():
    assert "balance" not in classify_themes.themes_for("the penalty for dying is fair")


def test_an_unrelated_complaint_matches_nothing():
    assert classify_themes.themes_for("the tutorial was a bit long") == set()


def test_matching_is_case_insensitive():
    assert classify_themes.themes_for("NERFED AGAIN") == classify_themes.themes_for("nerfed again")


def test_every_theme_has_seed_phrases():
    for theme, phrases in taxonomy.THEMES.items():
        assert phrases, f"{theme} has no seed phrases"


def test_the_two_added_themes_are_present():
    assert {"balance", "dev_conduct"} <= set(taxonomy.THEMES)


def test_psn_access_is_enabled_as_its_own_theme():
    """Enabled by Eileen 2026-09-13 — kept out of dev_conduct on purpose."""
    assert "psn_access" in taxonomy.THEMES


def test_an_account_linking_complaint_lands_in_psn_not_dev_conduct():
    found = classify_themes.themes_for("forced psn account linking, delisted in my country")

    assert "psn_access" in found
    assert "dev_conduct" not in found
