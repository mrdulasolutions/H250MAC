from h250mac.listener import interface_skip_message


def test_seized_handset_is_not_a_permission_error():
    message = interface_skip_message(OSError("open failed"))
    assert "already open" in message
    assert "Accessibility" not in message
    assert "Input Monitoring" not in message


def test_other_open_errors_keep_the_original_text():
    assert interface_skip_message(OSError("device gone")) == (
        "skipped an interface (device gone)"
    )
