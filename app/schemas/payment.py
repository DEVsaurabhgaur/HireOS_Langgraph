from pydantic import BaseModel

class CheckoutSession(BaseModel):
    order_id: str
    amount: int
    currency: str = 'INR'
    status: str
