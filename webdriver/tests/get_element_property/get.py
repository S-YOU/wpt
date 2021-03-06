import pytest

from tests.support.asserts import assert_error, assert_success
from tests.support.inline import inline


def get_element_property(session, element_id, prop):
    return session.transport.send(
        "GET", "session/{session_id}/element/{element_id}/property/{prop}".format(
            session_id=session.session_id,
            element_id=element_id,
            prop=prop))


def test_no_top_browsing_context(session, closed_window):
    response = get_element_property(session, "foo", "id")
    assert_error(response, "no such window")


def test_no_browsing_context(session, closed_frame):
    response = get_element_property(session, "foo", "id")
    assert_error(response, "no such window")


def test_element_not_found(session):
    response = get_element_property(session, "foo", "id")
    assert_error(response, "no such element")


def test_element_stale(session):
    session.url = inline("<input id=foobar>")
    element = session.find.css("input", all=False)
    session.refresh()

    response = get_element_property(session, element.id, "id")
    assert_error(response, "stale element reference")


def test_property_non_existent(session):
    session.url = inline("<input>")
    element = session.find.css("input", all=False)

    response = get_element_property(session, element.id, "foo")
    assert_success(response, None)
    assert session.execute_script("return arguments[0].foo", args=(element,)) is None


def test_content_attribute(session):
    session.url = inline("<input value=foobar>")
    element = session.find.css("input", all=False)

    response = get_element_property(session, element.id, "value")
    assert_success(response, "foobar")


def test_idl_attribute(session):
    session.url = inline("<input value=foo>")
    element = session.find.css("input", all=False)
    session.execute_script("""arguments[0].value = "bar";""", args=(element,))

    response = get_element_property(session, element.id, "value")
    assert_success(response, "bar")


@pytest.mark.parametrize("js_primitive,py_primitive", [
    ("\"foobar\"", "foobar"),
    (42, 42),
    ([], []),
    ({}, {}),
    ("null", None),
    ("undefined", None),
])
def test_primitives(session, js_primitive, py_primitive):
    session.url = inline("""
        <input>

        <script>
        const input = document.querySelector("input");
        input.foobar = {js_primitive};
        </script>
        """.format(js_primitive=js_primitive))
    element = session.find.css("input", all=False)

    response = get_element_property(session, element.id, "foobar")
    assert_success(response, py_primitive)


@pytest.mark.parametrize("js_primitive,py_primitive", [
    ("\"foobar\"", "foobar"),
    (42, 42),
    ([], []),
    ({}, {}),
    ("null", None),
    ("undefined", None),
])
def test_primitives_set_by_execute_script(session, js_primitive, py_primitive):
    session.url = inline("<input>")
    element = session.find.css("input", all=False)
    session.execute_script("arguments[0].foobar = {}".format(js_primitive), args=(element,))

    response = get_element_property(session, element.id, "foobar")
    assert_success(response, py_primitive)


def test_mutated_element(session):
    session.url = inline("<input type=checkbox>")
    element = session.find.css("input", all=False)
    element.click()

    checked = session.execute_script("""
        return arguments[0].hasAttribute('checked')
        """, args=(element,))
    assert checked is False

    response = get_element_property(session, element.id, "checked")
    assert_success(response, True)
