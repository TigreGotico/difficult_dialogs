"""Tests for difficult_dialogs.library.ArgumentLibrary."""
import pytest
from pathlib import Path
from difficult_dialogs.library import ArgumentLibrary, SearchResult
from difficult_dialogs.arguments import Argument
from difficult_dialogs.premises import Premise


SAMPLE_DIR = Path(__file__).parent.parent / "examples" / "sample_arguments"


@pytest.fixture
def lib() -> ArgumentLibrary:
    lib = ArgumentLibrary(SAMPLE_DIR)
    lib.scan()
    return lib


# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------

def test_scan_indexes_arguments(lib: ArgumentLibrary) -> None:
    assert len(lib) >= 30


def test_scan_lazy(tmp_path: Path) -> None:
    """Library auto-scans on first query if scan() not called explicitly."""
    (tmp_path / "arg").mkdir()
    (tmp_path / "arg" / "intro.dialog").write_text("Hello")
    (tmp_path / "arg" / "conclusion.conclusion").write_text("Bye")
    p_dir = tmp_path / "arg" / "p1"
    p_dir.mkdir()
    (p_dir / "p1.premise").write_text("Statement one")
    lib = ArgumentLibrary(tmp_path)
    # No explicit scan()
    assert len(lib) == 1


def test_scan_missing_root() -> None:
    lib = ArgumentLibrary("/does/not/exist")
    with pytest.raises(FileNotFoundError):
        lib.scan()


def test_scan_reload(lib: ArgumentLibrary) -> None:
    original = len(lib)
    lib.scan(reload=True)
    assert len(lib) == original


def test_repr(lib: ArgumentLibrary) -> None:
    assert "ArgumentLibrary" in repr(lib)
    assert str(lib.root) in repr(lib)


# ---------------------------------------------------------------------------
# categories()
# ---------------------------------------------------------------------------

def test_categories_returns_sorted_list(lib: ArgumentLibrary) -> None:
    cats = lib.categories()
    assert isinstance(cats, list)
    assert cats == sorted(cats)
    assert len(cats) >= 5


def test_expected_categories_present(lib: ArgumentLibrary) -> None:
    cats = set(lib.categories())
    for expected in ("health", "science", "technology", "society", "philosophy"):
        assert expected in cats, f"Missing category: {expected}"


# ---------------------------------------------------------------------------
# by_category()
# ---------------------------------------------------------------------------

def test_by_category_returns_arguments(lib: ArgumentLibrary) -> None:
    health = lib.by_category("health")
    assert len(health) >= 1
    assert all(isinstance(a, Argument) for a in health)


def test_by_category_case_insensitive(lib: ArgumentLibrary) -> None:
    lower = lib.by_category("health")
    upper = lib.by_category("HEALTH")
    assert len(lower) == len(upper)


def test_by_category_unknown_returns_empty(lib: ArgumentLibrary) -> None:
    assert lib.by_category("astrology") == []


# ---------------------------------------------------------------------------
# get()
# ---------------------------------------------------------------------------

def test_get_existing_argument(lib: ArgumentLibrary) -> None:
    cats = lib.categories()
    first_arg = lib.by_category(cats[0])[0]
    found = lib.get(first_arg.name)
    assert found is not None
    assert found.name == first_arg.name


def test_get_case_insensitive(lib: ArgumentLibrary) -> None:
    cats = lib.categories()
    first_arg = lib.by_category(cats[0])[0]
    found = lib.get(first_arg.name.upper())
    assert found is not None


def test_get_nonexistent_returns_none(lib: ArgumentLibrary) -> None:
    assert lib.get("this argument definitely does not exist xyz") is None


# ---------------------------------------------------------------------------
# search()
# ---------------------------------------------------------------------------

def test_search_returns_results(lib: ArgumentLibrary) -> None:
    results = lib.search("climate")
    assert isinstance(results, list)
    assert len(results) >= 1
    assert all(isinstance(r, SearchResult) for r in results)


def test_search_scores_between_0_and_1(lib: ArgumentLibrary) -> None:
    for r in lib.search("climate change science"):
        assert 0.0 < r.score <= 1.0


def test_search_sorted_by_score_descending(lib: ArgumentLibrary) -> None:
    results = lib.search("exercise health mental")
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_search_category_filter(lib: ArgumentLibrary) -> None:
    results = lib.search("health", category="health")
    for r in results:
        assert r.category == "health"


def test_search_limit(lib: ArgumentLibrary) -> None:
    results = lib.search("the", limit=3)
    assert len(results) <= 3


def test_search_empty_query_returns_empty(lib: ArgumentLibrary) -> None:
    assert lib.search("") == []


def test_search_no_match_returns_empty(lib: ArgumentLibrary) -> None:
    assert lib.search("xyzzy_impossible_token_8675309") == []


def test_search_matched_fields_populated(lib: ArgumentLibrary) -> None:
    results = lib.search("climate change")
    assert any(r.matched_fields for r in results)


# ---------------------------------------------------------------------------
# all_arguments()
# ---------------------------------------------------------------------------

def test_all_arguments(lib: ArgumentLibrary) -> None:
    all_args = lib.all_arguments()
    assert len(all_args) == len(lib)
    assert all(isinstance(a, Argument) for a in all_args)


# ---------------------------------------------------------------------------
# Flat (no category) layout
# ---------------------------------------------------------------------------

def test_flat_layout(tmp_path: Path) -> None:
    """Arguments directly under root are indexed as 'uncategorised'."""
    arg_dir = tmp_path / "my_argument"
    arg_dir.mkdir()
    (arg_dir / "intro.dialog").write_text("Start")
    (arg_dir / "conclusion.conclusion").write_text("End")
    p = arg_dir / "p1"
    p.mkdir()
    (p / "p1.premise").write_text("A premise")
    lib = ArgumentLibrary(tmp_path)
    lib.scan()
    assert len(lib) == 1
    assert lib.categories() == ["uncategorised"]


# ---------------------------------------------------------------------------
# Coverage gaps
# ---------------------------------------------------------------------------

def test_search_result_repr(lib: ArgumentLibrary) -> None:
    """SearchResult.__repr__ includes name, category, and score."""
    lib.scan()
    results = lib.search("exercise")
    assert results
    r = results[0]
    text = repr(r)
    assert "SearchResult" in text
    assert r.argument.name in text


def test_scan_cached_return(lib: ArgumentLibrary) -> None:
    """Second scan() without reload= returns self without re-scanning."""
    lib.scan()
    count_before = len(lib)
    returned = lib.scan()  # hits the cached branch (line 94)
    assert returned is lib
    assert len(lib) == count_before


def test_index_argument_skips_broken_dir(tmp_path: Path, monkeypatch) -> None:
    """_index_argument silently skips directories that fail to load."""
    import difficult_dialogs.library as lib_module
    from difficult_dialogs.library import ArgumentLibrary

    arg_dir = tmp_path / "bad_arg"
    arg_dir.mkdir()
    (arg_dir / "intro.dialog").write_text("Start")
    monkeypatch.setattr(lib_module.Argument, "from_directory",
                        staticmethod(lambda path: (_ for _ in ()).throw(RuntimeError("fail"))))

    lib = ArgumentLibrary(tmp_path)
    lib.scan()  # should not raise; broken dir is skipped
    assert len(lib) == 0


def test_search_auto_scans(tmp_path: Path) -> None:
    """search() triggers scan() when not yet scanned."""
    from difficult_dialogs.library import ArgumentLibrary
    arg_dir = tmp_path / "my_arg"
    arg_dir.mkdir()
    (arg_dir / "intro.dialog").write_text("Intro")
    (arg_dir / "conclusion.conclusion").write_text("Conclusion")
    lib = ArgumentLibrary(tmp_path)
    assert not lib._scanned
    lib.search("intro")  # must not raise even without explicit scan()
    assert lib._scanned


def test_categories_auto_scans(tmp_path: Path) -> None:
    """categories() triggers scan() when not yet scanned."""
    from difficult_dialogs.library import ArgumentLibrary
    lib = ArgumentLibrary(tmp_path)
    assert not lib._scanned
    lib.categories()
    assert lib._scanned


def test_by_category_auto_scans(tmp_path: Path) -> None:
    """by_category() triggers scan() when not yet scanned."""
    from difficult_dialogs.library import ArgumentLibrary
    lib = ArgumentLibrary(tmp_path)
    assert not lib._scanned
    lib.by_category("anything")
    assert lib._scanned


def test_get_auto_scans(tmp_path: Path) -> None:
    """get() triggers scan() when not yet scanned."""
    from difficult_dialogs.library import ArgumentLibrary
    lib = ArgumentLibrary(tmp_path)
    assert not lib._scanned
    result = lib.get("nonexistent")
    assert lib._scanned
    assert result is None


def test_all_arguments_auto_scans(tmp_path: Path) -> None:
    """all_arguments() triggers scan() when not yet scanned."""
    from difficult_dialogs.library import ArgumentLibrary
    lib = ArgumentLibrary(tmp_path)
    assert not lib._scanned
    lib.all_arguments()
    assert lib._scanned
