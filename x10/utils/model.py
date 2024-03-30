import inspect

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic.fields import AliasChoices, FieldInfo
from pydantic.functional_serializers import PlainSerializer
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Annotated


class X10BaseModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore", use_enum_values=True)

    # Read this to get more context why `alias_generator` can't be used:
    # https://github.com/pydantic/pydantic/discussions/7877
    # `AliasChoices` is used to support both "from json" (e.g. `Model.model_validate_json(...)` -- camel case required)
    # and "manual" (e.g. `Model(...)` -- snake case required) models creation.
    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)

        for key in inspect.get_annotations(cls):
            key_alias = to_camel(key)

            if key_alias == key:
                continue

            try:
                attr = getattr(cls, key)
            except AttributeError:
                field_info = Field(validation_alias=AliasChoices(key, key_alias), serialization_alias=key_alias)
                setattr(cls, key, field_info)
            else:
                if isinstance(attr, FieldInfo):
                    if attr.validation_alias is None:
                        attr.validation_alias = AliasChoices(key, key_alias)
                    if attr.serialization_alias is None:
                        attr.serialization_alias = key_alias
                else:
                    field_info = Field(
                        default=attr,
                        validation_alias=AliasChoices(key, key_alias),
                        serialization_alias=key_alias,
                    )
                    setattr(cls, key, field_info)

    def to_pretty_json(self):
        return self.model_dump_json(indent=4)

    def to_api_request_json(self, *, exclude_none: bool = False):
        return self.model_dump(mode="json", by_alias=True, exclude_none=exclude_none)


class EmptyModel(X10BaseModel):
    pass


HexValue = Annotated[
    int,
    PlainSerializer(lambda x: hex(x), return_type=str, when_used="json"),
    BeforeValidator(lambda x: int(x, 16) if not isinstance(x, int) else x),
]
