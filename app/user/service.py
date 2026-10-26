from fastapi_mail import MessageSchema, MessageType

def create_message(recipients: list[str], subject: str, body: str) -> MessageSchema:
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        body=body,
        subtype=MessageType.html)
    return message
