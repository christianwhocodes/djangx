import logging
from typing import TypedDict

from django.conf import settings
from django.core.exceptions import ProgrammingError
from django.core.mail import EmailMultiAlternatives
from django.http import HttpRequest
from django.template.loader import render_to_string
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
from rest_framework.views import APIView

from .forms import EmailUsForm
from .models import EmailAddress


class EmailContext(TypedDict):
    """Type definition for email template context."""
    name: str
    email: str
    subject: str
    message: str
    url: str

logger = logging.getLogger(__name__)


class EmailUsAPIView(APIView):
    """API endpoint for handling contact form submissions."""

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "")

    def post(self, request: HttpRequest) -> Response:
        """Handle contact form submission."""
        try:
            # Create and validate form with request data
            form = EmailUsForm(request.data)

            if not form.is_valid():
                return Response(
                    {
                        "success": False,
                        "message": "Please correct the errors below.",
                        "errors": form.errors,
                    },
                    status=HTTP_400_BAD_REQUEST,
                )

            # Extract validated data
            sender_name = form.cleaned_data["name"]
            sender_email = form.cleaned_data["email"]
            sender_subject = form.cleaned_data["subject"]
            sender_message = form.cleaned_data["message"]

            # Get recipient email
            recipient_email = self._get_recipient_email()

            # Prepare email context
            email_context = {
                "name": sender_name,
                "email": sender_email,
                "subject": sender_subject,
                "message": sender_message,
                "url": request.build_absolute_uri("/"),
            }

            # Send email
            self._send_contact_email(sender_subject, sender_email, recipient_email, email_context)

            return Response(
                {
                    "success": True,
                    "message": "Thank you for your message! We will get back to you soon.",
                },
                status=HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error sending contact email: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": "There was an error sending your message. Please try again later.",
                },
                status=HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _get_recipient_email(self) -> str:
        """Get the recipient email address."""
        recipient_email: str | None = None

        # Attempt to get the primary contact email from the EmailAddress model
        try:
            contact_email_obj = EmailAddress.objects.filter(is_primary=True).first()
            if contact_email_obj:
                recipient_email = contact_email_obj.email
        except ProgrammingError:
            # Table doesn't exist yet (migrations haven't run)
            logger.info("EmailAddress table not found, using fallback email")

        # Fallback to DEFAULT_FROM_EMAIL if no primary email found
        if not recipient_email:
            recipient_email = self.from_email

        return recipient_email

    def _send_contact_email(
        self, subject: str, sender_email: str, recipient_email: str, context: EmailContext
    ) -> None:
        """Send the contact form email."""
        # Render email templates
        text_content = render_to_string("addresses/email-us.txt", context)
        html_content = render_to_string("addresses/email-us.html", context)

        # Send email
        msg = EmailMultiAlternatives(
            f"Contact Form: {subject}",
            text_content,
            self.from_email,
            [recipient_email],
            reply_to=[sender_email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()