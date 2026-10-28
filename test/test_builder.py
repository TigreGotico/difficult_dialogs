"""Tests for ArgumentBuilder and PremiseBuilder."""
import pytest
from difficult_dialogs.builder import ArgumentBuilder, PremiseBuilder
from difficult_dialogs.arguments import Argument
from difficult_dialogs.premises import Premise


# ------------------------------------------------------------------ #
# PremiseBuilder
# ------------------------------------------------------------------ #

def test_premise_builder_statement() -> None:
    arg = ArgumentBuilder("a").premise("p").statement("claim").done().build()
    assert arg.premises[0].statements[0].text == "claim"


def test_premise_builder_support() -> None:
    arg = ArgumentBuilder("a").premise("p").statement("c").support("evidence").done().build()
    assert "evidence" in arg.premises[0].support


def test_premise_builder_source() -> None:
    arg = ArgumentBuilder("a").premise("p").statement("c").source("http://x.com").done().build()
    assert "http://x.com" in arg.premises[0].sources


def test_premise_builder_five_ws() -> None:
    pb = (
        ArgumentBuilder("a")
        .premise("p")
        .statement("c")
        .what("a thing")
        .why("reasons")
        .how("doing stuff")
        .when("now")
        .where("here")
        .who("everyone")
    )
    arg = pb.done().build()
    p = arg.premises[0]
    assert "a thing" in p.what
    assert "reasons" in p.why
    assert "doing stuff" in p.how
    assert "now" in p.when
    assert "here" in p.where
    assert "everyone" in p.who


def test_premise_builder_description() -> None:
    arg = ArgumentBuilder("a").premise("p").description("Custom desc").statement("c").done().build()
    assert arg.premises[0].description == "Custom desc"


def test_premise_builder_done_returns_argument_builder() -> None:
    ab = ArgumentBuilder("a")
    pb = ab.premise("p")
    assert isinstance(pb, PremiseBuilder)
    result = pb.done()
    assert result is ab


def test_premise_builder_build_returns_premise() -> None:
    ab = ArgumentBuilder("a")
    pb = ab.premise("p").statement("c")
    p = pb.build()
    assert isinstance(p, Premise)
    assert p.statements[0].text == "c"
    assert len(ab.build().premises) == 1


def test_premise_duplicate_not_added_twice() -> None:
    """Registering the same premise name twice only adds it once."""
    ab = ArgumentBuilder("a")
    pb = ab.premise("p").statement("c1")
    p = pb.build()
    # build() registers; calling done() on same parent again would re-add
    # but _add_premise deduplicates by name
    ab._add_premise(p)  # manual second registration
    arg = ab.build()
    assert len(arg.premises) == 1


# ------------------------------------------------------------------ #
# ArgumentBuilder
# ------------------------------------------------------------------ #

def test_argument_builder_name() -> None:
    arg = ArgumentBuilder("my_arg").build()
    assert arg.name == "my_arg"


def test_argument_builder_intro() -> None:
    arg = ArgumentBuilder("a").intro("Hello").build()
    assert arg.intro == "Hello"


def test_argument_builder_conclusion() -> None:
    arg = ArgumentBuilder("a").conclusion("Done").build()
    assert arg.conclusion == "Done"


def test_argument_builder_multiple_premises() -> None:
    arg = (
        ArgumentBuilder("a")
        .premise("p1").statement("s1").done()
        .premise("p2").statement("s2").done()
        .build()
    )
    assert len(arg.premises) == 2
    assert arg.premises[0].name == "p1"
    assert arg.premises[1].name == "p2"


def test_argument_builder_add_premise_directly() -> None:
    p = Premise(name="direct")
    p.add_statement("stmt")
    arg = ArgumentBuilder("a").add_premise(p).build()
    assert arg.premises[0] is p


def test_argument_builder_returns_argument_instance() -> None:
    result = ArgumentBuilder("x").build()
    assert isinstance(result, Argument)


def test_full_chain() -> None:
    """End-to-end fluent construction."""
    arg = (
        ArgumentBuilder("climate")
        .intro("Let's discuss climate change.")
        .conclusion("The evidence is clear.")
        .premise("human_causation")
            .statement("97% of scientists agree.")
            .support("See IPCC AR6.")
            .source("https://www.ipcc.ch/")
            .why("CO2 traps heat.")
            .done()
        .build()
    )
    assert arg.name == "climate"
    assert arg.intro == "Let's discuss climate change."
    assert arg.conclusion == "The evidence is clear."
    assert len(arg.premises) == 1
    p = arg.premises[0]
    assert p.statements[0].text == "97% of scientists agree."
    assert "See IPCC AR6." in p.support
    assert "CO2 traps heat." in p.why
