from django.conf import settings
import sib_api_v3_sdk



def get_brevo_api():
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = settings.BREVO_API_KEY
    configuration.host = settings.BREVO_CONFIG_URL
    return sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )


BREVO_SENDER = {
    "email": settings.BREVO_SENDER_EMAIL,
    "name": settings.BREVO_SENDER_NAME,
}

