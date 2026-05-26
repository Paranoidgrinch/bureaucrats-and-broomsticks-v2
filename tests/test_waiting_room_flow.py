from rich.table import Table

import bab.console.waiting_room_flow as waiting_room_flow


def test_waiting_room_flow_imports_table() -> None:
    assert waiting_room_flow.Table is Table


from bab.console.waiting_room_flow import waiting_room_copy_for_stage


def test_waiting_room_copy_uses_default_waiting_room_text() -> None:
    copy = waiting_room_copy_for_stage(None, heal_percent=25)

    assert copy.title == "Waiting Room"
    assert copy.table_title == "Waiting Room Choices"
    assert copy.productive_choice == "Do something productive."
    assert copy.nap_choice == "Take a Nap."
    assert copy.heal_effect == "Heal 25% of max HP."
    assert "postponed decisions" in copy.description


def test_waiting_room_copy_uses_final_office_text_for_final_stage() -> None:
    copy = waiting_room_copy_for_stage("final_office", heal_percent=25)

    assert copy.title == "Final Office"
    assert copy.table_title == "Final Office Choices"
    assert copy.productive_choice == "Review one last document."
    assert copy.nap_choice == "Rest on the hard bench."
    assert copy.heal_effect == "Heal 25% of max HP."
    assert "Commissioner's door" in copy.description
    assert "final office" in copy.nap_result_template
