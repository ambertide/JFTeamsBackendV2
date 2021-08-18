from pydantic import BaseModel


class JotFormCredentials(BaseModel):
    """
    Represents the user credential as they exist with respect to the 
        JotForm API.
    """
    appKey: str  # User's app key.
    pollID: str  # ID of the form.

class AppCredentials(BaseModel):
    """
    Represents the credential used to establish user identity on the
        proxy.
    """
    uuid: str