"""Bản đồ kỹ năng lớp 1–12: mã không trùng, mọi kỹ năng cần trước đều tồn tại."""
from app.services.topi import skill_map


def test_ids_unique_and_needs_known():
    ids = [n["id"] for n in skill_map.nodes()]
    assert len(ids) == len(set(ids))
    known = set(ids)
    for n in skill_map.nodes():
        assert set(n["needs"]) <= known, n["id"]
        assert n["name_vi"] and "[check]" not in n["name_vi"]


def test_grade_10_gets_its_own_and_lower_grades():
    ids = {n["id"] for n in skill_map.for_grade(10)}
    assert {"H10.01", "N10.01", "N9.15", "N5.06"} <= ids
    assert not any(i.startswith(("N11", "H11", "T11", "N12")) for i in ids)
    assert "Giá trị lượng giác của góc 0°–180°" in skill_map.prompt_list(10)
