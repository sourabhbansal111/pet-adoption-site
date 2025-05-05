from .models import Cart, CartItem

def cart(request):
    cart_count = 0
    if 'admin' in request.path:
        return {}
    else:
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart)
            for cart_item in cart_items:
                cart_count += cart_item.quantity
        except Cart.DoesNotExist:
            cart_count = 0
    return {'cart_count': cart_count}

def _cart_id(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key