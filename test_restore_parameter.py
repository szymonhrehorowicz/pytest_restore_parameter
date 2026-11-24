import pytest
from typing import Any, Callable

parameters: dict[str, Any] = {"param1": 1}


class Connector:
    def write_parameter(self, parameter: str, value: Any):
        parameters[parameter] = value

    def read_parameter(self, parameter: str):
        return parameters[parameter]


@pytest.fixture(scope="session")
def connector():
    return Connector()


class TempParModifier:

    def __init__(self, connector: Connector, parameter: str, value: Any | None = None):
        self.initial_value: Any = connector.read_parameter(parameter)
        self.parameter: str = parameter
        self.connector: Connector = connector
        if value:
            connector.write_parameter(parameter, value)

    def modify(self, value: Any):
        self.connector.write_parameter(self.parameter, value)

    def restore(self):
        print("\nRESTORING VALUE\n")
        self.connector.write_parameter(self.parameter, self.initial_value)


TempParamModifierFactory = Callable[[str, Any | None], TempParModifier]


@pytest.fixture(scope="module")
def temp_par_modifier(
    request: pytest.FixtureRequest, connector: Connector
) -> TempParamModifierFactory:

    def create_modifier(parameter: str, value: Any | None) -> TempParModifier:
        modifier = TempParModifier(connector, parameter, value)
        request.addfinalizer(modifier.restore)
        return modifier

    return create_modifier


@pytest.fixture(scope="module")
def scenario(temp_par_modifier: TempParamModifierFactory, connector: Connector):
    result = {"initial_value": connector.read_parameter("param1")}

    param1_modifier = temp_par_modifier("param1", 10)
    result["value_after_first_modification"] = connector.read_parameter("param1")

    param1_modifier.modify(11)
    result["value_after_second_modification"] = connector.read_parameter("param1")

    return result


def test_initial_value(scenario):
    assert scenario["initial_value"] == 1


def test_value_after_first_modification(scenario):
    assert scenario["value_after_first_modification"] == 10


def test_value_after_second_modification(scenario):
    assert scenario["value_after_second_modification"] == 11
