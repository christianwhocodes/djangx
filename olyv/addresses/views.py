import logging
from typing import Any, Dict

from django.core.mail import EmailMultiAlternatives
from django.db import ProgrammingError
from django.template.loader import render_to_string
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
from rest_framework.views import APIView

from .forms import EmailUsForm
from .models import EmailAddress

logger = logging.getLogger(__name__)


class EmailUsAPIView(APIView):
    """API endpoint for handling EmailUs form submissions."""

    def post(self, request: Request) -> Response:
        """Handle EmailUsForm submission."""
        try:
            # Create and validate form with request data
            form = EmailUsForm(data=request.data)  # type: ignore[arg-type]

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
            email_context: Dict[str, Any] = {
                "name": sender_name,
                "email": sender_email,
                "subject": sender_subject,
                "message": sender_message,
                "url": request.build_absolute_uri("/"),
            }

            # Send email
            self._send_contact_email(sender_subject, sender_email, recipient_email, email_context)

            logger.info(f"EmailUsForm email sent successfully from {sender_email}")

            return Response(
                {
                    "success": True,
                    "message": "Thank you for your message! We will get back to you soon.",
                },
                status=HTTP_200_OK,
            )

        except ValueError as e:
            # Configuration errors (like missing recipient email)
            logger.error(f"Configuration error in EmailUs form: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": "Service temporarily unavailable. Please try again later.",
                },
                status=HTTP_500_INTERNAL_SERVER_ERROR,
            )

        except Exception as e:
            logger.error(f"Unexpected error sending EmailUs form email: {str(e)}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "message": "There was an error sending your message. Please try again later.",
                },
                status=HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _get_recipient_email(self) -> str:
        """Get the recipient email address from primary EmailAddress record."""
        try:
            contact_email_obj = EmailAddress.objects.filter(is_primary=True).first()
            if contact_email_obj:
                recipient_email = contact_email_obj.email
                logger.debug(f"Using primary email from database: {recipient_email}")
                return recipient_email
            else:
                raise ValueError("No primary email address found in EmailAddress model")
        except ProgrammingError:
            # Table doesn't exist yet (migrations haven't run)
            raise ValueError("EmailAddress table not found - ensure migrations have been run")

    def _send_contact_email(
        self, subject: str, sender_email: str, recipient_email: str, context: Dict[str, Any]
    ) -> None:
        """Send the contact form email."""
        try:
            # Render email templates
            text_content = render_to_string("olyv/addresses/email-us.txt", context)
            html_content = render_to_string("olyv/addresses/email-us.html", context)

            # Create and send email
            msg = EmailMultiAlternatives(
                f"Contact Form: {subject}",
                text_content,
                from_email=None,  # Let Django use DEFAULT_FROM_EMAIL
                to=[recipient_email],
                reply_to=[sender_email],
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()

        except Exception as e:
            logger.error(f"Failed to send EmailUs form email: {str(e)}")
            raise  # Re-raise to be caught by the main exception handler
