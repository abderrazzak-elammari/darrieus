from darrieus import freefem


def test_override_file():
    text = freefem.override(nIface=48, nu=0.1, out="a.csv")
    assert text == 'nIface = 48;\nnu = 0.1;\nout = "a.csv";\n'


def test_stage_copies_scripts(tmp_path):
    freefem.stage(tmp_path, lambda_=2.0)
    assert (tmp_path / "common.idp").exists()
    assert (tmp_path / "darrieus.edp").exists()
    assert (tmp_path / "override.idp").read_text() == "lambda_ = 2.0;\n"


def test_repository_override_is_empty():
    text = (freefem.SCRIPTS / "override.idp").read_text()
    assert all(line.startswith("//") or not line.strip() for line in text.splitlines())
