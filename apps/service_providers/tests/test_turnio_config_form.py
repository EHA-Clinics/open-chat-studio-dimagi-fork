from apps.service_providers.forms import TurnIOMessagingConfigForm
from apps.service_providers.messaging_service import TurnIOService


class TestTurnIOMessagingConfigForm:
    """The hmac_secret is optional so that existing Turn providers keep working after deploy.

    See dimagi/open-chat-studio#2346 - enforcing on deploy day would drop live webhook
    traffic for every provider that has not yet copied its secret across from Turn.
    """

    def test_hmac_secret_is_optional(self):
        form = TurnIOMessagingConfigForm(None, data={"auth_token": "token123"})
        assert form.is_valid(), form.errors
        assert form.cleaned_data["hmac_secret"] == ""

    def test_hmac_secret_is_saved_when_supplied(self):
        form = TurnIOMessagingConfigForm(None, data={"auth_token": "token123", "hmac_secret": "s3cr3t-value"})
        assert form.is_valid(), form.errors
        assert form.cleaned_data["hmac_secret"] == "s3cr3t-value"

    def test_hmac_secret_is_stripped(self):
        form = TurnIOMessagingConfigForm(None, data={"auth_token": "token123", "hmac_secret": "  s3cr3t-value  "})
        assert form.is_valid(), form.errors
        assert form.cleaned_data["hmac_secret"] == "s3cr3t-value"

    def test_blank_secret_on_a_pre_existing_provider_normalises_to_empty_string(self):
        """A provider saved before this field existed has no hmac_secret in its config.

        ObfuscatingMixin restores the unmasked original for an unchanged field, which
        would be None here. Storing None would defeat the `not hmac_secret` check.
        """
        form = TurnIOMessagingConfigForm(
            None,
            data={"auth_token": "token123", "hmac_secret": ""},
            initial={"auth_token": "token123"},
        )
        assert form.is_valid(), form.errors
        assert form.cleaned_data["hmac_secret"] == ""

    def test_unchanged_masked_secret_keeps_the_original_value(self):
        form = TurnIOMessagingConfigForm(
            None,
            data={"auth_token": "token123", "hmac_secret": "s3cr...ue"},
            initial={"auth_token": "token123", "hmac_secret": "s3cr3t-value"},
        )
        assert form.is_valid(), form.errors
        assert form.cleaned_data["hmac_secret"] == "s3cr3t-value"

    def test_secret_is_obfuscated_for_display(self):
        form = TurnIOMessagingConfigForm(None, initial={"auth_token": "token123", "hmac_secret": "s3cr3t-value"})
        assert form["hmac_secret"].value() == "s3cr...ue"


class TestTurnIOTemplateFields:
    """Template config for out-of-window sends lives on the provider form."""

    def test_template_fields_are_optional(self):
        form = TurnIOMessagingConfigForm(None, data={"auth_token": "token123"})
        assert form.is_valid(), form.errors
        assert form.cleaned_data["template_namespace"] == ""
        assert form.cleaned_data["template_name"] == ""
        assert form.cleaned_data["template_language"] == "en"
        # Omitted header cleans to blank (headerless). The "AdhereBot" field initial only
        # pre-fills the rendered input; a submitted blank still means "omit the header".
        assert form.cleaned_data["template_header_param"] == ""

    def test_header_initial_prefills_adherebot(self):
        form = TurnIOMessagingConfigForm(None)
        assert form["template_header_param"].value() == "AdhereBot"
        assert form["template_language"].value() == "en"

    def test_template_namespace_and_name_are_saved_when_supplied(self):
        form = TurnIOMessagingConfigForm(
            None,
            data={
                "auth_token": "token123",
                "template_namespace": "  ns-uuid  ",
                "template_name": "  refill_patient  ",
                "template_language": "ha",
                "template_header_param": "  AdhereBot  ",
            },
        )
        assert form.is_valid(), form.errors
        assert form.cleaned_data["template_namespace"] == "ns-uuid"
        assert form.cleaned_data["template_name"] == "refill_patient"
        assert form.cleaned_data["template_language"] == "ha"
        assert form.cleaned_data["template_header_param"] == "AdhereBot"

    def test_blank_language_defaults_to_en(self):
        form = TurnIOMessagingConfigForm(None, data={"auth_token": "token123", "template_language": "  "})
        assert form.is_valid(), form.errors
        assert form.cleaned_data["template_language"] == "en"

    def test_blank_header_param_is_kept_for_headerless_templates(self):
        """Clearing the header must survive cleaning so headerless templates omit the component."""
        form = TurnIOMessagingConfigForm(
            None,
            data={
                "auth_token": "token123",
                "template_namespace": "ns",
                "template_name": "tpl",
                "template_header_param": "   ",
            },
        )
        assert form.is_valid(), form.errors
        assert form.cleaned_data["template_header_param"] == ""

    def test_namespace_without_name_is_rejected(self):
        form = TurnIOMessagingConfigForm(None, data={"auth_token": "token123", "template_namespace": "ns-uuid"})
        assert not form.is_valid()
        assert "__all__" in form.errors

    def test_name_without_namespace_is_rejected(self):
        form = TurnIOMessagingConfigForm(None, data={"auth_token": "token123", "template_name": "refill_patient"})
        assert not form.is_valid()
        assert "__all__" in form.errors

    def test_cleaned_config_builds_service(self):
        form = TurnIOMessagingConfigForm(
            None,
            data={
                "auth_token": "token123",
                "template_namespace": "ns-uuid",
                "template_name": "refill_patient",
                "template_language": "ha",
                "template_header_param": "",
            },
        )
        assert form.is_valid(), form.errors
        service = TurnIOService(**form.cleaned_data)
        assert service.template_namespace == "ns-uuid"
        assert service.template_name == "refill_patient"
        assert service.template_language == "ha"
        assert service.template_header_param == ""
