import help


def test_general_help_lists_topics_and_usage_guidance(capsys):
    # Verifies general help prints every topic and the next-step guidance.
    help.show_general_help()

    output = capsys.readouterr().out
    for topic in help.HELP_TOPICS.values():
        assert topic["title"] in output
        assert topic["usage"] in output
    assert "Type 'help <topic>'" in output
    assert "Type 'exit' to quit" in output


def test_topic_help_renders_description_commands_and_optimizer_flags(capsys):
    # Verifies detailed topics render optional sections and normalize topic names.
    help.show_topic_help(" OPTIMIZER ")
    optimizer_output = capsys.readouterr().out
    assert "OPTIMIZER FLAGS" in optimizer_output
    assert "optimizer add" in optimizer_output
    assert "Valid Flags Reference" in optimizer_output
    assert "faculty_course" in optimizer_output

    help.show_topic_help("new")
    assert "Details:" in capsys.readouterr().out

    help.show_topic_help("room")
    assert "Commands:" in capsys.readouterr().out


def test_topic_help_reports_unknown_topic(capsys):
    # Verifies an unknown topic reports the complete list of available topics.
    help.show_topic_help("unknown")

    output = capsys.readouterr().out
    assert "Unknown help topic 'unknown'" in output
    assert "Available topics:" in output
    assert ", ".join(help.HELP_TOPICS) in output


def test_help_handler_selects_general_or_topic_help(capsys):
    # Verifies empty and nonempty help commands route to the appropriate renderer.
    help.help_handler(None)
    assert "SCHEDULER CLI COMMAND REFERENCE" in capsys.readouterr().out

    help.help_handler(None, "limit")
    assert "SCHEDULE GENERATION LIMIT" in capsys.readouterr().out
